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
    payload = validate(event['input'], INPUT_SCHEMA)
    
    # Define temp_dir outside try block so it's available in except block
    temp_dir = f"/workspace/tmp/lipsync_{uuid.uuid4()}"
    
    try:
        # Initialize B2 manager
        b2 = setup_b2()
        
        # Create a unique temporary directory
        os.makedirs(temp_dir, exist_ok=True)
        
        # Extract B2 paths from URLs
        video_b2_path = extract_b2_path(payload['source_video'])
        audio_b2_path = extract_b2_path(payload['source_audio'])
        
        # Download files from B2
        video_path = os.path.join(temp_dir, "video.mp4")
        audio_path = os.path.join(temp_dir, "audio.mp3")
        
        if not b2.download_file(video_b2_path, video_path):
            raise Exception("Failed to download video file")
            
        if not b2.download_file(audio_b2_path, audio_path):
            raise Exception("Failed to download audio file")
        
        # Prepare inference arguments
        inference_args = {
            'unet_config_path': "configs/unet/second_stage.yaml",
            'inference_ckpt_path': "checkpoints/latentsync_unet.pt",
            'video_path': video_path,
            'audio_path': audio_path,
            'video_out_path': os.path.join(temp_dir, "result.mp4"),
            'inference_steps': 20,
            'guidance_scale': 1.0,
            'seed': 1247,
            'start_frame': 0
        }
        
        # Run inference
        result_path = run_inference({'input': inference_args})
        
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
        if os.path.exists(temp_dir):
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