import os
import uuid
from typing import Dict, Any
from b2_manager import B2Manager
from scripts.inference import run_inference
from dotenv import load_dotenv
import runpod
from runpod.serverless.utils.rp_validator import validate
from runpod.serverless.modules.rp_logger import RunPodLogger
import shutil

# Comment out the restoration import until it exists
# from restoration import *
from schemas.input import INPUT_SCHEMA

logger = RunPodLogger()
# Load environment variables
load_dotenv()

# Add detailed logging for debugging
logger.info("=== DEBUGGING RUNPOD SERVERLESS ENVIRONMENT ===")
logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"__file__ path: {__file__}")
logger.info(f"Absolute __file__ path: {os.path.abspath(__file__)}")
logger.info(f"Directory listing of current directory: {os.listdir('.')}")

# Log environment variables (without exposing sensitive values)
logger.info("=== ENVIRONMENT VARIABLES CHECK ===")
logger.info(f"RUNPOD_SECRET_BUCKET_NAME exists: {os.getenv('RUNPOD_SECRET_BUCKET_NAME') is not None}")
logger.info(f"RUNPOD_SECRET_BUCKET_ID exists: {os.getenv('RUNPOD_SECRET_BUCKET_ID') is not None}")
logger.info(f"RUNPOD_SECRET_BUCKET_KEY_ID exists: {os.getenv('RUNPOD_SECRET_BUCKET_KEY_ID') is not None}")
logger.info(f"RUNPOD_SECRET_BUCKET_APP_KEY exists: {os.getenv('RUNPOD_SECRET_BUCKET_APP_KEY') is not None}")

def setup_b2():
    """Initialize and return B2Manager instance"""
    return B2Manager(
        bucket_name=os.getenv('RUNPOD_SECRET_BUCKET_NAME'),
        bucket_id=os.getenv('RUNPOD_SECRET_BUCKET_ID'),
        key_id=os.getenv('RUNPOD_SECRET_BUCKET_KEY_ID'),
        app_key=os.getenv('RUNPOD_SECRET_BUCKET_APP_KEY')
    )

def extract_b2_path(b2_url: str) -> str:
    """Extract the path from a B2 URL"""
    # Remove the domain and bucket name from the URL
    # Example: https://f004.backblazeb2.com/file/bucket-name/path/to/file.mp4
    # Should return: path/to/file.mp4
    parts = b2_url.split('/file/')
    if len(parts) != 2:
        raise ValueError(f"Invalid B2 URL format: {b2_url}")
    return parts[1].split('/', 1)[1]

def handler(event):
    """
    Process the input payload and return the result file URL
    
    Args:
        payload (Dict[str, Any]): Input payload according to input schema
        
    Returns:
        Dict[str, str]: Dictionary containing the result file URL
    """
    payload = validate(event["input"], INPUT_SCHEMA)
    logger.info(f"Payload: {payload}")
    #payload=payload['validated_input']

    #payload = event['input']
    # Define temp_dir outside try block so it's available in except block
    # Use a directory relative to the current file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    temp_dir = os.path.join(current_dir, "tmp", f"lipsync_{uuid.uuid4()}")
    
    # Log path information
    logger.info(f"Current directory resolved to: {current_dir}")
    logger.info(f"Temporary directory path: {temp_dir}")
    
    try:
        # Initialize B2 manager
        b2 = setup_b2()
        
        # Create a unique temporary directory
        logger.info(f"Attempting to create temporary directory: {temp_dir}")
        os.makedirs(temp_dir, exist_ok=True)
        logger.info(f"Temporary directory created successfully: {os.path.exists(temp_dir)}")
        
        # Extract B2 paths from URLs
        # logger.info(f"payload: {payload}")
        # print("payload: {}".format(payload))
        video_b2_path = extract_b2_path(payload['source_video'])
        audio_b2_path = extract_b2_path(payload['source_audio'])
        
        # Download files from B2
        video_path = os.path.join(temp_dir, "video.mp4")
        audio_path = os.path.join(temp_dir, "audio.mp3")
        
        logger.info(f"Attempting to download video from B2: {video_b2_path}")
        if not b2.download_file(video_b2_path, video_path):
            logger.error(f"Failed to download video file from B2: {video_b2_path}")
            raise Exception("Failed to download video file")
        logger.info(f"Video download successful, file exists: {os.path.exists(video_path)}")
            
        logger.info(f"Attempting to download audio from B2: {audio_b2_path}")
        if not b2.download_file(audio_b2_path, audio_path):
            logger.error(f"Failed to download audio file from B2: {audio_b2_path}")
            raise Exception("Failed to download audio file")
        logger.info(f"Audio download successful, file exists: {os.path.exists(audio_path)}")
        
        # Prepare inference arguments
        unet_config_path = "configs/unet/second_stage.yaml"
        inference_ckpt_path = "checkpoints/latentsync_unet.pt"
        
        # Log file existence checks
        logger.info(f"Checking if config file exists: {os.path.exists(unet_config_path)}")
        logger.info(f"Checking if checkpoint file exists: {os.path.exists(inference_ckpt_path)}")
        
        inference_args = {
            'unet_config_path': unet_config_path,
            'inference_ckpt_path': inference_ckpt_path,
            'video_path': video_path,
            'audio_path': audio_path,
            'video_out_path': os.path.join(temp_dir, "result.mp4"),
            'inference_steps': 20,
            'guidance_scale': 1.0,
            'seed': 1247,
            'start_frame': 0
        }
        
        # Run inference
        logger.info(f"Starting inference with arguments: {inference_args}")
        try:
            result_path = run_inference({'input': inference_args})
            logger.info(f"Inference completed successfully, result path: {result_path}")
            logger.info(f"Result file exists: {os.path.exists(result_path)}")
        except Exception as e:
            logger.error(f"Error during inference: {str(e)}")
            raise
        
        # Upload result back to B2
        # Use the same folder as the source video
        result_b2_path = os.path.dirname(video_b2_path) + "/result.mp4"
        
        if not b2.upload_file(result_path, result_b2_path):
            raise Exception("Failed to upload result file")
        
        # Clean up temporary directory
        shutil.rmtree(temp_dir)
        
        # Return the result URL
        return {
            "result_url": f"https://{os.getenv('BUCKET_NAME')}.s3.us-west-002.backblazeb2.com/{result_b2_path}"
        }
        
    except Exception as e:
        # Clean up on error
        logger.error(f"Error in handler: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        if os.path.exists(temp_dir):
            logger.info(f"Cleaning up temporary directory: {temp_dir}")
            shutil.rmtree(temp_dir)
        raise Exception(f"Error processing request: {str(e)}")
    
if __name__ == '__main__':
    logger.info('Starting RunPod Serverless...')
    runpod.serverless.start(
        {
            'handler': handler,
            "return_aggregate_stream": True
        }
    )