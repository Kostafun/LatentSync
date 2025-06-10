#!/usr/bin/env python3
"""
Test script for S3 integration
This script tests the S3Manager functionality without running the full inference pipeline.
"""

import os
import sys
import tempfile
from dotenv import load_dotenv
from s3_manager import S3Manager, extract_s3_key_from_url

# Load environment variables
load_dotenv()

def test_s3_connection():
    """Test S3 connection and basic operations"""
    print("=== Testing S3 Connection ===")
    
    try:
        # Initialize S3 manager
        s3 = S3Manager(
            bucket_name=os.getenv('RUNPOD_SECRET_S3_BUCKET_NAME'),
            access_key_id=os.getenv('RUNPOD_SECRET_S3_ACCESS_KEY_ID'),
            secret_access_key=os.getenv('RUNPOD_SECRET_S3_SECRET_ACCESS_KEY'),
            region=os.getenv('RUNPOD_SECRET_S3_REGION', 'us-east-1'),
            endpoint_url=os.getenv('RUNPOD_SECRET_S3_ENDPOINT_URL')
        )
        print("✅ S3 connection successful")
        return s3
    except Exception as e:
        print(f"❌ S3 connection failed: {e}")
        return None

def test_url_parsing():
    """Test S3 URL parsing functionality"""
    print("\n=== Testing S3 URL Parsing ===")
    
    test_urls = [
        "https://my-bucket.s3.us-east-1.amazonaws.com/path/to/video.mp4",
        "https://s3.us-west-2.amazonaws.com/my-bucket/path/to/audio.mp3",
        "https://custom-endpoint.com/my-bucket/files/test.mp4"
    ]
    
    for url in test_urls:
        try:
            s3_key = extract_s3_key_from_url(url)
            print(f"✅ URL: {url}")
            print(f"   S3 Key: {s3_key}")
        except Exception as e:
            print(f"❌ URL: {url}")
            print(f"   Error: {e}")

def test_file_operations(s3_manager):
    """Test file upload/download operations"""
    if not s3_manager:
        print("\n❌ Skipping file operations test - no S3 connection")
        return
    
    print("\n=== Testing File Operations ===")
    
    try:
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write("This is a test file for S3 integration")
            temp_file_path = temp_file.name
        
        print(f"Created temporary test file: {temp_file_path}")
        
        # Test upload
        success, s3_key = s3_manager.upload_file(temp_file_path)
        if success:
            print(f"✅ File uploaded successfully to S3 key: {s3_key}")
            
            # Test URL generation
            url = s3_manager.get_file_url(s3_key)
            print(f"✅ Generated URL: {url[:50]}...")
            
            # Test download
            download_path = temp_file_path + "_downloaded"
            if s3_manager.download_file(s3_key, download_path):
                print(f"✅ File downloaded successfully to: {download_path}")
                
                # Verify content
                with open(download_path, 'r') as f:
                    content = f.read()
                if "This is a test file" in content:
                    print("✅ File content verified")
                else:
                    print("❌ File content verification failed")
                
                # Clean up downloaded file
                os.unlink(download_path)
            else:
                print("❌ File download failed")
            
            # Clean up S3 file
            if s3_manager.delete_file(s3_key):
                print("✅ Test file cleaned up from S3")
            else:
                print("⚠️  Failed to clean up test file from S3")
        else:
            print("❌ File upload failed")
        
        # Clean up local temp file
        os.unlink(temp_file_path)
        print("✅ Local test file cleaned up")
        
    except Exception as e:
        print(f"❌ File operations test failed: {e}")

def test_unique_filename_generation():
    """Test unique filename generation"""
    print("\n=== Testing Unique Filename Generation ===")
    
    try:
        s3 = S3Manager("dummy", "dummy", "dummy")  # Just for testing filename generation
        
        # Generate multiple filenames
        filenames = []
        for i in range(5):
            filename = s3.generate_unique_filename("test.mp4")
            filenames.append(filename)
            print(f"Generated filename {i+1}: {filename}")
        
        # Check uniqueness
        if len(set(filenames)) == len(filenames):
            print("✅ All generated filenames are unique")
        else:
            print("❌ Some generated filenames are duplicates")
            
    except Exception as e:
        print(f"❌ Filename generation test failed: {e}")

def main():
    """Run all tests"""
    print("S3 Integration Test Suite")
    print("=" * 50)
    
    # Check environment variables
    required_vars = [
        'RUNPOD_SECRET_S3_BUCKET_NAME',
        'RUNPOD_SECRET_S3_ACCESS_KEY_ID',
        'RUNPOD_SECRET_S3_SECRET_ACCESS_KEY'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        print("Please set these variables before running the test.")
        return 1
    
    # Run tests
    test_unique_filename_generation()
    test_url_parsing()
    s3_manager = test_s3_connection()
    test_file_operations(s3_manager)
    
    print("\n" + "=" * 50)
    print("Test suite completed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())