# Copyright (c) 2024 Bytedance Ltd. and/or its affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
from omegaconf import OmegaConf
import torch
from diffusers import AutoencoderKL, DDIMScheduler
from latentsync.models.unet import UNet3DConditionModel
from latentsync.pipelines.lipsync_pipeline import LipsyncPipeline
from diffusers.utils.import_utils import is_xformers_available
from accelerate.utils import set_seed
from latentsync.whisper.audio2feature import Audio2Feature
import time
import subprocess
import latentsync.utils.util as util
import os
import librosa
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('inference')

def main(config, args):
    # Check if the GPU supports float16
    gpu_available = torch.cuda.is_available()
    logger.info(f"CUDA available: {gpu_available}")
    if gpu_available:
        logger.info(f"CUDA device count: {torch.cuda.device_count()}")
        logger.info(f"CUDA device name: {torch.cuda.get_device_name(0)}")
        logger.info(f"CUDA device capability: {torch.cuda.get_device_capability()}")
    
    is_fp16_supported = gpu_available and torch.cuda.get_device_capability()[0] > 7
    dtype = torch.float16 if is_fp16_supported else torch.float32
    logger.info(f"Using dtype: {dtype}")

    #print(f"Input video path: {args.video_path}")
    #print(f"Input audio path: {args.audio_path}")
    #print(f"Loaded checkpoint path: {args.inference_ckpt_path}")

    logger.info(f"Loading scheduler from: configs")
    logger.info(f"Configs directory exists: {os.path.exists('configs')}")
    logger.info(f"Configs directory contents: {os.listdir('configs') if os.path.exists('configs') else 'Directory not found'}")
    
    try:
        scheduler = DDIMScheduler.from_pretrained("configs")
        logger.info("Scheduler loaded successfully")
    except Exception as e:
        logger.error(f"Error loading scheduler: {str(e)}")
        raise

    if config.model.cross_attention_dim == 768:
        whisper_model_path = "small"
    elif config.model.cross_attention_dim == 384:
        whisper_model_path = "tiny"
    else:
        raise NotImplementedError("cross_attention_dim must be 768 or 384")

    logger.info(f"Loading audio encoder with whisper model: {whisper_model_path}")
    whisper_path = f"checkpoints/whisper/{whisper_model_path}.pt"
    logger.info(f"Checking if whisper model exists: {os.path.exists(whisper_path)}")
    
    try:
        audio_encoder = Audio2Feature(model_path=whisper_model_path, device="cuda", num_frames=config.data.num_frames)
        logger.info("Audio encoder loaded successfully")
    except Exception as e:
        logger.error(f"Error loading audio encoder: {str(e)}")
        raise

    logger.info("Loading VAE model from stabilityai/sd-vae-ft-mse")
    try:
        vae = AutoencoderKL.from_pretrained("stabilityai/sd-vae-ft-mse", torch_dtype=dtype)
        vae.config.scaling_factor = 0.18215
        vae.config.shift_factor = 0
        logger.info("VAE model loaded successfully")
    except Exception as e:
        logger.error(f"Error loading VAE model: {str(e)}")
        raise

    logger.info(f"Loading UNet model from checkpoint: {args.inference_ckpt_path}")
    logger.info(f"Checkpoint file exists: {os.path.exists(args.inference_ckpt_path)}")
    
    if os.path.exists(args.inference_ckpt_path):
        logger.info(f"Checkpoint file size: {os.path.getsize(args.inference_ckpt_path)} bytes")
    else:
        logger.error(f"Checkpoint file not found at: {args.inference_ckpt_path}")
        # List parent directory contents to help debug
        checkpoint_dir = os.path.dirname(args.inference_ckpt_path)
        if os.path.exists(checkpoint_dir):
            logger.info(f"Contents of checkpoint directory: {os.listdir(checkpoint_dir)}")
        else:
            logger.error(f"Checkpoint directory does not exist: {checkpoint_dir}")
    
    try:
        unet, _ = UNet3DConditionModel.from_pretrained(
            OmegaConf.to_container(config.model),
            args.inference_ckpt_path,  # load checkpoint
            device="cpu",
        )
        logger.info("UNet model loaded successfully")
    except Exception as e:
        logger.error(f"Error loading UNet model: {str(e)}")
        raise

    unet = unet.to(dtype=dtype)

    # set xformers
    if is_xformers_available():
        unet.enable_xformers_memory_efficient_attention()
        print("Xformers enabled")

    pipeline = LipsyncPipeline(
        vae=vae,
        audio_encoder=audio_encoder,
        unet=unet,
        scheduler=scheduler,
    ).to("cuda")

    if args.seed != -1:
        set_seed(args.seed)
    else:
        torch.seed()

    print(f"Initial seed: {torch.initial_seed()}")

    pipeline(
        video_path=args.video_path,
        audio_path=args.audio_path,
        video_out_path=args.video_out_path,
        video_mask_path=args.video_out_path.replace(".mp4", "_mask.mkv"),
        num_frames=config.data.num_frames,
        num_inference_steps=args.inference_steps,
        guidance_scale=args.guidance_scale,
        weight_dtype=dtype,
        width=config.data.resolution,
        height=config.data.resolution,
    )

def shorten_video(video_path, temp_dir, duration):
    target_video_path = os.path.join(temp_dir, "video.mp4")
    command = f"ffmpeg -loglevel error -y -nostdin -i {video_path} -t {duration} -c copy {target_video_path}"
    subprocess.run(command, shell=True)
    return target_video_path

def loop_video(video_path, temp_dir, audio_duration, video_duration):
    target_video_path = os.path.join(temp_dir, "video2.mp4")
    loop_count = int(audio_duration // video_duration) 

    command = f"ffmpeg -loglevel error -y -nostdin -stream_loop {loop_count} -i {video_path} -c copy {target_video_path}"
    subprocess.run(command, shell=True)
    return shorten_video(target_video_path, temp_dir, audio_duration)

def crop_video(video_path, temp_dir, start_time):
    target_video_path = os.path.join(temp_dir, "video2.mp4")
    command = f"ffmpeg -loglevel error -y -nostdin -i {video_path} -ss {start_time} -c:v libx264 -crf 0 {target_video_path}"

    subprocess.run(command, shell=True)
    return shorten_video(target_video_path, temp_dir, audio_duration)

def get_audio_duration(audio_path):
    """
    Returns the duration of the audio file in seconds.
    """
    y, sr = librosa.load(audio_path)
    duration = librosa.get_duration(y=y, sr=sr)
    return duration

def get_video_duration(video_path):
    """
    Returns the duration of the video file in seconds.
    """
    command = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {video_path}"
    output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
    duration = float(output.decode().strip())
    return duration

def run_inference(job):
    logger.info("Starting run_inference function")
    logger.info(f"Job input: {job}")
    
    args = job['input']
    start_timer = time.time()
    
    logger.info(f"Inference arguments: {args}")
    # Convert dictionary args to argparse.Namespace if needed
    if isinstance(args, dict):
        # Create a new argparse.Namespace object
        namespace_args = argparse.Namespace()
        
        # Transfer all dictionary keys to the namespace
        for key, value in args.items():
            setattr(namespace_args, key, value)
        
        # Replace the dictionary with the namespace
        args = namespace_args
        
    # Set default values for optional arguments if not present
    if not hasattr(args, 'inference_steps'):
        args.inference_steps = 20
    if not hasattr(args, 'guidance_scale'):
        args.guidance_scale = 1.0
    if not hasattr(args, 'seed'):
        args.seed = 1247
    if not hasattr(args, 'start_frame'):
        args.start_frame = 0

    logger.info("Creating temporary directory")
    temp_dir = util.create_temp_dir()
    logger.info(f"Temporary directory created: {temp_dir}")

    logger.info(f"Loading config from: {args.unet_config_path}")
    logger.info(f"Config file exists: {os.path.exists(args.unet_config_path)}")
    
    try:
        config = OmegaConf.load(args.unet_config_path)
        logger.info("Config loaded successfully")
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        raise

    
    logger.info(f"Checking input files:")
    logger.info(f"Video path: {args.video_path}, exists: {os.path.exists(args.video_path)}")
    logger.info(f"Audio path: {args.audio_path}, exists: {os.path.exists(args.audio_path)}")
    
    try:
        video_duration = get_video_duration(args.video_path)
        logger.info(f"Video duration: {video_duration} seconds")
        
        start_time = args.start_frame/25
        if start_time > video_duration:
            start_time = start_time % video_duration
        logger.info(f"Start time: {start_time} seconds")

        audio_duration = get_audio_duration(args.audio_path)+2 + start_time
        logger.info(f"Audio duration: {audio_duration} seconds")
    except Exception as e:
        logger.error(f"Error getting media durations: {str(e)}")
        raise

    if audio_duration < video_duration: 
        args.video_path = shorten_video(args.video_path, temp_dir, audio_duration)
    elif audio_duration > video_duration:
        args.video_path = loop_video(args.video_path, temp_dir, audio_duration, video_duration)
    if start_time > 0:
        args.video_path = crop_video(args.video_path, temp_dir, start_time)
    
    logger.info("Starting main inference process")
    try:
        main(config, args)
        logger.info("Main inference process completed successfully")
    except Exception as e:
        logger.error(f"Error in main inference process: {str(e)}")
        raise
    finally:
        logger.info(f"Cleaning up temporary directory: {temp_dir}")
        util.delete_temp_dir(temp_dir)
    end_timer = time.time()

    execution_time = end_timer - start_timer
    execution_time_per_second = execution_time / (audio_duration-2)
    logger.info(f"Total execution time: {execution_time:.2f} seconds")
    logger.info(f"Execution time per second of audio duration: {execution_time_per_second:.2f} seconds")
    
    logger.info(f"Output video path: {args.video_out_path}")
    logger.info(f"Output video exists: {os.path.exists(args.video_out_path)}")
    
    return args.video_out_path

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--unet_config_path", type=str, default="configs/unet/second_stage.yaml")
    parser.add_argument("--inference_ckpt_path", type=str, default="checkpoints/latentsync_unet.pt")
    parser.add_argument("--video_path", type=str, required=True)
    parser.add_argument("--audio_path", type=str, required=True)
    parser.add_argument("--video_out_path", type=str, required=True)
    parser.add_argument("--inference_steps", type=int, default=20)
    parser.add_argument("--guidance_scale", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=1247)
    parser.add_argument("--start_frame", type=int, default=0)
    args = parser.parse_args()

    run_inference(args)
