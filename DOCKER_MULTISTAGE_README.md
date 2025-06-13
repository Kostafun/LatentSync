# Multi-Stage Docker Build Strategy for AutoTube Endpoint

This directory contains a multi-stage Docker build strategy designed to optimize Docker Hub uploads by separating heavy dependencies (~7GB) from lightweight application code (~3.4M).

## Overview

The strategy uses two Docker images:

1. **Base Image** (`Dockerfile.base`) - Contains heavy dependencies:
   - Python virtual environment with all requirements
   - Downloaded model files (`latentsync_unet.pt`, `whisper/tiny.pt`)
   - System dependencies (ffmpeg, etc.)
   - ~7GB total size

2. **Application Image** (`Dockerfile.app`) - Contains only application code:
   - Uses base image as foundation
   - Copies endpoint source code
   - Sets up entrypoint
   - ~3.4M additional size

## Benefits

- **Faster Iterations**: Code changes only require rebuilding the small application layer
- **Reduced Bandwidth**: Only ~3.4M needs to be uploaded for code changes vs ~7GB full rebuild
- **Better Caching**: Base image with models is cached and reused
- **Cost Effective**: Significantly reduces Docker Hub bandwidth usage

## Files Structure

```
endpoint/
├── Dockerfile.base          # Base image with dependencies and models
├── Dockerfile.app           # Application image with source code
├── .dockerignore           # Optimized build context exclusions
├── build-and-deploy.sh     # Automated build and deployment script
├── requirements.txt        # Python dependencies
├── start.sh               # Container entrypoint script
└── DOCKER_MULTISTAGE_README.md  # This file
```

## Quick Start

### 1. Set Your Docker Hub Username

```bash
export DOCKER_HUB_USERNAME="your-actual-dockerhub-username"
```

### 2. Build and Deploy Both Images

```bash
chmod +x build-and-deploy.sh
./build-and-deploy.sh full
```

This will:
- Build the base image (~7GB, takes 15-30 minutes)
- Push base image to Docker Hub
- Build the application image (~3.4M, takes 1-2 minutes)
- Push application image to Docker Hub

### 3. For Code Changes (Fast Iteration)

```bash
./build-and-deploy.sh app-only
```

This only rebuilds and pushes the small application layer (~3.4M, takes 1-2 minutes).

## Manual Build Commands

### Build Base Image

```bash
# Build base image (do this once or when dependencies change)
docker build -f Dockerfile.base -t your-dockerhub-username/autotube-base:latest .

# Push to Docker Hub
docker push your-dockerhub-username/autotube-base:latest
```

### Build Application Image

```bash
# Update Dockerfile.app to use your base image
sed -i 's/your-dockerhub-username/actual-username/g' Dockerfile.app

# Build application image
docker build -f Dockerfile.app -t your-dockerhub-username/autotube-app:latest .

# Push to Docker Hub
docker push your-dockerhub-username/autotube-app:latest
```

## Build Script Options

The `build-and-deploy.sh` script supports several commands:

```bash
# Build and push both images
./build-and-deploy.sh full

# Build and push only base image
./build-and-deploy.sh base-only

# Build and push only application image
./build-and-deploy.sh app-only

# Build both images locally (don't push)
./build-and-deploy.sh build-only
```

### Environment Variables

Customize the build with environment variables:

```bash
export DOCKER_HUB_USERNAME="myusername"
export BASE_IMAGE_NAME="autotube-base"
export APP_IMAGE_NAME="autotube-app"
export BASE_TAG="v1.0"
export APP_TAG="v1.0"

./build-and-deploy.sh full
```

## Deployment

Use the application image in your deployment:

```bash
# Run the container
docker run -d \
  --name autotube-endpoint \
  -p 8000:8000 \
  -e RUNPOD_SECRET_S3_BUCKET_NAME="your-bucket" \
  -e RUNPOD_SECRET_S3_ACCESS_KEY_ID="your-key" \
  -e RUNPOD_SECRET_S3_SECRET_ACCESS_KEY="your-secret" \
  your-dockerhub-username/autotube-app:latest
```

## Development Workflow

### Initial Setup (One Time)
1. Build and push base image: `./build-and-deploy.sh base-only`
2. Build and push app image: `./build-and-deploy.sh app-only`

### Code Changes (Fast Iteration)
1. Make code changes
2. Rebuild only app image: `./build-and-deploy.sh app-only`
3. Deploy updated app image

### Dependency Changes (Rare)
1. Update `requirements.txt`
2. Rebuild base image: `./build-and-deploy.sh base-only`
3. Rebuild app image: `./build-and-deploy.sh app-only`

## Troubleshooting

### Base Image Build Fails
- Check internet connection (downloads ~7GB of models)
- Verify Docker has enough disk space
- Check Docker Hub authentication: `docker login`

### Application Image Build Fails
- Ensure base image exists: `docker images | grep autotube-base`
- Verify Dockerfile.app references correct base image
- Check .dockerignore isn't excluding required files

### Push Fails
- Verify Docker Hub login: `docker login`
- Check repository exists on Docker Hub
- Verify push permissions for the repository

### Model Download Issues
- The base image downloads models from HuggingFace
- Ensure network access to `huggingface.co`
- Check if HuggingFace authentication is needed

## Image Sizes

Expected image sizes:
- **Base Image**: ~7GB (includes PyTorch, models, dependencies)
- **Application Image**: ~7GB total (~3.4M additional layer)
- **Upload for code changes**: Only ~3.4M (application layer)

## Performance Comparison

| Scenario | Traditional Build | Multi-Stage Build |
|----------|------------------|-------------------|
| Initial build | ~7GB upload | ~7GB upload |
| Code change | ~7GB upload | ~3.4M upload |
| Time for code change | 15-30 minutes | 1-2 minutes |
| Bandwidth savings | 0% | ~95% |

## Security Notes

- The `.dockerignore` file excludes sensitive files like `.env`
- Pass secrets as environment variables at runtime
- Don't include API keys or credentials in the Docker images
- Use Docker secrets or external secret management for production

## Maintenance

### Updating Models
When new model versions are available:
1. Update the download commands in `Dockerfile.base`
2. Rebuild base image: `./build-and-deploy.sh base-only`
3. Rebuild app image: `./build-and-deploy.sh app-only`

### Updating Dependencies
When `requirements.txt` changes:
1. Rebuild base image: `./build-and-deploy.sh base-only`
2. Rebuild app image: `./build-and-deploy.sh app-only`

### Cleaning Up
Remove old images to save disk space:
```bash
# Remove old images
docker image prune -f

# Remove specific old versions
docker rmi your-dockerhub-username/autotube-base:old-tag
docker rmi your-dockerhub-username/autotube-app:old-tag