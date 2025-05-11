#!/usr/bin/env bash

echo "Symlinking files from Network Volume"
ln -s /runpod-volume /workspace
# ln -s /runpod-volume/checkpoints /workspace/checkpoints

rm -rf /root/.cache
ln -s /runpod-volume/.cache /root/.cache

mkdir -p /root/.cache/torch/hub/checkpoints
ln -s /workspace/checkpoints/auxiliary/2DFAN4-cd938726ad.zip /root/.cache/torch/hub/checkpoints/2DFAN4-cd938726ad.zip
ln -s /workspace/checkpoints/auxiliary/s3fd-619a316812.pth /root/.cache/torch/hub/checkpoints/s3fd-619a316812.pth
ln -s /workspace/checkpoints/auxiliary/vgg16-397923af.pth /root/.cache/torch/hub/checkpoints/vgg16-397923af.pth

echo "Starting RunPod Handler"
export PYTHONUNBUFFERED=1
source /workspace/venv/bin/activate
cd /workspace
python3 -u rp_handler.py