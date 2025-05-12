#!/usr/bin/env python3
import argparse
import os
from datetime import datetime
import uuid

from schemas.input import INPUT_SCHEMA
from b2_manager import B2Manager
from dotenv import load_dotenv
import runpod
from runpod import AsyncioEndpoint, AsyncioJob
import asyncio
import aiohttp
# Load environment variables
load_dotenv()

def setup_b2():
    """Initialize and return B2Manager instance"""
    return B2Manager(
        bucket_name=os.getenv('BUCKET_NAME'),
        bucket_id=os.getenv('BUCKET_ID'),
        key_id=os.getenv('BUCKET_KEY_ID'),
        app_key=os.getenv('BUCKET_APP_KEY')
    )

async def asyncprocess_with_b2(video_path: str, audio_path: str, output_path: str = "./output", face_restore: bool = True, upscale: int = 1, codeformer_fidelity: float = 0.7):
    """
    Process files using B2 storage
    
    Args:
        b2: B2Manager instance
        video_path: Path to video file
        audio_path: Path to audio file
        result_path: Path for the result file
    """
    b2 = setup_b2()
    folder_name = f"lipsync_{datetime.now().strftime('%Y%m%d')}_{str(uuid.uuid4())[:8]}/"
    
    try:
        # Validate input files
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        # Create folder in bucket
        print("Creating folder in bucket...")
        if not b2.create_folder(folder_name):
            raise Exception("Failed to create folder")

        # Upload files
        # video_filename = os.path.basename(video_path)
        # audio_filename = os.path.basename(audio_path)
        video_filename = "video.mp4"
        audio_filename = "audio.mp3"
        result_filename = "result.mp4"
        
        print(f"Uploading video file: {video_filename}...")
        if not b2.upload_file(video_path, f"{folder_name}{video_filename}"):
            raise Exception("Failed to upload video file")

        print(f"Uploading audio file: {audio_filename}...")
        if not b2.upload_file(audio_path, f"{folder_name}{audio_filename}"):
            raise Exception("Failed to upload audio file")

        # Process files (lip sync)
        print("Processing files...")
        payload = {
            "input": {
                "source_video": f"{folder_name}{video_filename}",
                "source_audio": f"{folder_name}{audio_filename}",
                "face_restore": face_restore,
                "upscale": upscale,
                "codeformer_fidelity": codeformer_fidelity
            }
        }
        
        # Make the API request
        response = await process_with_runpod(payload)
        
        # Download the result
        print("Downloading result file...")
        if not b2.download_file(f"{folder_name}{result_filename}", f"{output_path}/{result_filename}"):
            raise Exception("Failed to download result file")

        # Clean up
        print("Cleaning up...")
        if not b2.delete_folder_recursive(folder_name):
            raise Exception("Failed to delete folder")

        print("Process completed successfully!")
        return response

    except Exception as e:
        print(f"Error during processing: {e}")
        # Attempt to clean up even if there was an error
        b2.delete_folder_recursive(folder_name)
        raise

async def process_with_runpod(payload: dict):
    async with aiohttp.ClientSession() as session:
        runpod.api_key = os.getenv("RUNPOD_API_KEY")
        endpoint = AsyncioEndpoint(os.getenv("RUNPOD_ENDPOINT_ID"), session)
        job: AsyncioJob = await endpoint.run(payload)

        while True:
            status = await job.status()
            print(f"Current job status: {status}")
            if status == "COMPLETED":
                output = await job.output()
                print("Job output:", output)
                break  # Exit the loop once the job is completed.
            elif status in ["FAILED"]:
                print("Job failed or encountered an error.")

                break
            else:
                print("Job in queue or processing. Waiting 15 seconds...")
                await asyncio.sleep(15)  # Wait for 3 seconds before polling again

        return output

def parse_args():
    parser = argparse.ArgumentParser(description='Run lip sync with specified parameters')
    
    # Add required arguments
    parser.add_argument('--source-video', type=str, default="temp/video.mp4",
                      help='Path to the source video file')
    parser.add_argument('--source-audio', type=str, default="temp/audio.mp3",
                      help='Path to the source audio file')
    parser.add_argument('--output-path', type=str, default="./output",
                      help='Path to the output file')
    # Add optional arguments with defaults from schema
    parser.add_argument('--face-restore', type=bool, default=INPUT_SCHEMA['face_restore']['default'],
                      help='Whether to restore face quality')
    parser.add_argument('--upscale', type=int, default=INPUT_SCHEMA['upscale']['default'],
                      help='Upscale factor')
    parser.add_argument('--codeformer-fidelity', type=float, 
                      default=INPUT_SCHEMA['codeformer_fidelity']['default'],
                      help='Codeformer fidelity parameter')
    
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    
    # Initialize B2 manager
    
    asyncio.run(asyncprocess_with_b2(args.source_video, args.source_audio, args.output_path, args.face_restore, args.upscale, args.codeformer_fidelity))
    # Process files with B2 storage
