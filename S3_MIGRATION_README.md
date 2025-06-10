# S3 Migration Guide

This document outlines the migration from Backblaze B2 to AWS S3 (or S3-compatible services) for the RunPod serverless lipsync endpoint.

## Changes Made

### 1. New S3 Manager (`s3_manager.py`)
- Replaced `b2_manager.py` with a new S3-compatible manager
- Implements datetime + random string file naming convention
- Supports both AWS S3 and S3-compatible services
- Includes proper error handling and logging

### 2. Updated Dependencies
- Replaced `b2sdk` with `boto3` in `requirements.txt`
- Added support for AWS S3 SDK

### 3. Modified Handler (`handler.py`)
- Updated imports to use S3Manager instead of B2Manager
- Implemented unique file naming using datetime timestamps and random strings
- Updated URL parsing to handle S3 URLs instead of B2 URLs
- Modified environment variable names for S3 configuration

### 4. File Naming Convention
The new system generates unique filenames using:
- Datetime timestamp: `YYYYMMDD_HHMMSS`
- Random string: 8 characters (lowercase letters + digits)
- Format: `{timestamp}_{random_string}.{extension}`
- Example: `20241208_143022_a7b9c2d1.mp4`

## Environment Variables

### Required S3 Environment Variables
Replace the old B2 environment variables with these S3 variables:

```bash
# S3 Configuration
RUNPOD_SECRET_S3_BUCKET_NAME=your-s3-bucket-name
RUNPOD_SECRET_S3_ACCESS_KEY_ID=your-access-key-id
RUNPOD_SECRET_S3_SECRET_ACCESS_KEY=your-secret-access-key
RUNPOD_SECRET_S3_REGION=us-east-1  # Optional, defaults to us-east-1
RUNPOD_SECRET_S3_ENDPOINT_URL=https://your-custom-endpoint.com  # Optional, for S3-compatible services
```

### Old B2 Variables (No Longer Used)
```bash
# These are no longer needed:
# RUNPOD_SECRET_BUCKET_NAME
# RUNPOD_SECRET_BUCKET_ID
# RUNPOD_SECRET_BUCKET_KEY_ID
# RUNPOD_SECRET_BUCKET_APP_KEY
```

## S3 URL Formats Supported

The system now accepts S3 URLs in various formats:

### AWS S3 URLs
```
# Virtual-hosted-style URL
https://bucket-name.s3.region.amazonaws.com/path/to/file.mp4

# Path-style URL
https://s3.region.amazonaws.com/bucket-name/path/to/file.mp4
```

### S3-Compatible Services
```
# Custom endpoint format
https://your-endpoint.com/bucket-name/path/to/file.mp4
```

## Input Schema

The input schema remains the same:
```json
{
  "source_video": "https://your-bucket.s3.amazonaws.com/path/to/video.mp4",
  "source_audio": "https://your-bucket.s3.amazonaws.com/path/to/audio.mp3",
  "face_restore": false,
  "upscale": 1,
  "codeformer_fidelity": 0.5
}
```

## Output Changes

The response now includes both the result URL and the S3 key:
```json
{
  "result_url": "https://presigned-url-to-result.mp4",
  "s3_key": "20241208_143022_a7b9c2d1.mp4"
}
```

## Key Features

### 1. Unique File Naming
- No more folder-based organization
- Each file gets a unique timestamp + random string name
- Prevents naming conflicts and overwrites

### 2. Presigned URLs
- Result URLs are presigned with 24-hour expiration
- Secure access without exposing credentials

### 3. S3 Compatibility
- Works with AWS S3
- Compatible with S3-like services (MinIO, DigitalOcean Spaces, etc.)
- Configurable endpoint URLs

### 4. Error Handling
- Comprehensive logging for debugging
- Proper cleanup of temporary files
- Detailed error messages

## Migration Steps

1. **Update Environment Variables**: Replace B2 variables with S3 variables
2. **Update Input URLs**: Change from B2 URLs to S3 URLs in your requests
3. **Test Connection**: Verify S3 credentials and bucket access
4. **Deploy**: Update your RunPod serverless deployment

## Troubleshooting

### Common Issues

1. **Invalid S3 URL Format**
   - Ensure URLs follow supported S3 formats
   - Check bucket name and region in URL

2. **Access Denied**
   - Verify S3 credentials are correct
   - Check bucket permissions for read/write access

3. **Endpoint Connection Failed**
   - For custom endpoints, ensure URL is correct
   - Verify endpoint supports S3 API

### Logging

The system provides detailed logging for:
- S3 connection status
- File download/upload progress
- URL parsing results
- Error details

Check RunPod logs for debugging information.

## Performance Considerations

- Presigned URLs expire after 24 hours
- Temporary files are cleaned up after processing
- Unique naming prevents cache conflicts
- S3 transfer speeds may vary by region

## Security Notes

- Presigned URLs provide secure, time-limited access
- No permanent public URLs are created
- Credentials are never exposed in logs
- Temporary files are securely cleaned up