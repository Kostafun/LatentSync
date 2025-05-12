import os
import argparse
from b2_manager import B2Manager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def process_media_files(audio_path: str, video_path: str):
    """
    Process media files by uploading them to B2, processing, and managing the results
    
    Args:
        audio_path (str): Path to the input audio file
        video_path (str): Path to the input video file
    """
    # Initialize B2Manager with credentials from environment variables
    b2 = B2Manager(
        bucket_name=os.getenv('BUCKET_NAME'),
        bucket_id=os.getenv('BUCKET_ID'),
        key_id=os.getenv('BUCKET_KEY_ID'),
        app_key=os.getenv('BUCKET_APP_KEY')
    )

    # Validate input files exist
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Define folder and file paths
    folder_name = "media_processing/"
    audio_filename = os.path.basename(audio_path)
    video_filename = os.path.basename(video_path)
    result_file = "result.mp4"

    try:
        # 1. Create folder in bucket
        print("Creating folder in bucket...")
        if not b2.create_folder(folder_name):
            raise Exception("Failed to create folder")

        # 2. Upload files to the folder
        print(f"Uploading audio file: {audio_filename}...")
        if not b2.upload_file(audio_path, f"{folder_name}{audio_filename}"):
            raise Exception("Failed to upload audio file")

        print(f"Uploading video file: {video_filename}...")
        if not b2.upload_file(video_path, f"{folder_name}{video_filename}"):
            raise Exception("Failed to upload video file")

        # 3. Run external processing (example using ffmpeg)
        print("Running external processing...")
        # Note: Replace this with your actual processing command
        os.system(f"ffmpeg -i {video_path} -i {audio_path} -c:v copy -c:a aac {result_file}")

        # 4. Upload the result file
        print("Uploading result file...")
        if not b2.upload_file(result_file, f"{folder_name}{result_file}"):
            raise Exception("Failed to upload result file")

        # 5. Download the result file
        print("Downloading result file...")
        if not b2.download_file(f"{folder_name}{result_file}", f"downloaded_{result_file}"):
            raise Exception("Failed to download result file")

        # 6. Clean up - delete the folder and all its contents
        print("Cleaning up...")
        if not b2.delete_folder_recursive(folder_name):
            raise Exception("Failed to delete folder")

        print("Process completed successfully!")

    except Exception as e:
        print(f"Error during processing: {e}")
        # Attempt to clean up even if there was an error
        b2.delete_folder_recursive(folder_name)
        raise

def main():
    parser = argparse.ArgumentParser(description='Process media files with B2 storage')
    parser.add_argument('--audio', '-a', required=True,
                      help='Path to the input audio file')
    parser.add_argument('--video', '-v', required=True,
                      help='Path to the input video file')
    
    args = parser.parse_args()
    process_media_files(args.audio, args.video)

if __name__ == "__main__":
    main() 