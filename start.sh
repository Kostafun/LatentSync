#!/usr/bin/env bash

# Enable error reporting and command echo
set -e
set -x

echo "=== RUNPOD SERVERLESS CONTAINER INITIALIZATION ==="
echo "Current directory: $(pwd)"
echo "Directory listing:"
ls -la

echo "=== CHECKING RUNPOD VOLUME ==="
if [ -d "/runpod-volume" ]; then
    echo "RunPod volume exists"
    echo "RunPod volume contents:"
    ls -la /runpod-volume
else
    echo "ERROR: RunPod volume does not exist"
fi

echo "=== SYMLINKING FILES FROM NETWORK VOLUME ==="
echo "Creating symlink from /runpod-volume to /workspace"
ln -sf /runpod-volume /workspace
echo "Checking if symlink was created:"
if [ -L "/workspace" ]; then
    echo "Symlink created successfully"
    echo "Workspace contents:"
    ls -la /workspace
else
    echo "ERROR: Failed to create symlink"
fi

echo "=== SETTING UP CACHE DIRECTORY ==="
echo "Removing existing cache directory"
rm -rf /root/.cache
echo "Creating symlink for cache directory"
ln -sf /runpod-volume/.cache /root/.cache
echo "Checking if cache symlink was created:"
if [ -L "/root/.cache" ]; then
    echo "Cache symlink created successfully"
else
    echo "ERROR: Failed to create cache symlink"
fi

echo "=== SETTING UP MODEL CHECKPOINTS ==="
echo "Creating torch hub checkpoints directory"
mkdir -p /root/.cache/torch/hub/checkpoints
echo "Checking if checkpoints directory exists in workspace:"
if [ -d "/workspace/checkpoints" ]; then
    echo "Checkpoints directory exists"
    echo "Checkpoints directory contents:"
    ls -la /workspace/checkpoints
    
    echo "Checking if auxiliary directory exists:"
    if [ -d "/workspace/checkpoints/auxiliary" ]; then
        echo "Auxiliary directory exists"
        echo "Auxiliary directory contents:"
        ls -la /workspace/checkpoints/auxiliary
    else
        echo "ERROR: Auxiliary directory does not exist"
    fi
else
    echo "ERROR: Checkpoints directory does not exist"
fi

echo "Creating symlinks for model files"
if [ -f "/workspace/checkpoints/auxiliary/2DFAN4-cd938726ad.zip" ]; then
    ln -sf /workspace/checkpoints/auxiliary/2DFAN4-cd938726ad.zip /root/.cache/torch/hub/checkpoints/2DFAN4-cd938726ad.zip
    echo "2DFAN4 model symlink created"
else
    echo "ERROR: 2DFAN4 model file not found"
fi

if [ -f "/workspace/checkpoints/auxiliary/s3fd-619a316812.pth" ]; then
    ln -sf /workspace/checkpoints/auxiliary/s3fd-619a316812.pth /root/.cache/torch/hub/checkpoints/s3fd-619a316812.pth
    echo "s3fd model symlink created"
else
    echo "ERROR: s3fd model file not found"
fi

if [ -f "/workspace/checkpoints/auxiliary/vgg16-397923af.pth" ]; then
    ln -sf /workspace/checkpoints/auxiliary/vgg16-397923af.pth /root/.cache/torch/hub/checkpoints/vgg16-397923af.pth
    echo "vgg16 model symlink created"
else
    echo "ERROR: vgg16 model file not found"
fi

echo "=== CHECKING MAIN MODEL CHECKPOINT ==="
if [ -f "/workspace/checkpoints/latentsync_unet.pt" ]; then
    echo "Main model checkpoint exists"
    echo "File size: $(du -h /workspace/checkpoints/latentsync_unet.pt | cut -f1)"
else
    echo "ERROR: Main model checkpoint not found"
fi

echo "=== CHECKING ENVIRONMENT ==="
echo "Python version:"
python3 --version

echo "=== CHECKING VIRTUAL ENVIRONMENT ==="
if [ -d "/workspace/venv" ]; then
    echo "Virtual environment exists"
else
    echo "ERROR: Virtual environment not found"
fi

echo "=== STARTING RUNPOD HANDLER ==="
export PYTHONUNBUFFERED=1
echo "Activating virtual environment"
source /workspace/venv/bin/activate
echo "Changing to workspace directory"
cd /workspace
echo "Starting handler.py"
python3 -u handler.py