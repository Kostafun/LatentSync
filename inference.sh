#!/bin/bash

python -m scripts.inference \
    --unet_config_path "configs/unet/second_stage.yaml" \
    --inference_ckpt_path "checkpoints/latentsync_unet.pt" \
    --guidance_scale 1 \
    --video_path "assets/vert2_00007.mp4" \
    --audio_path "assets/censored.mp3" \
    --video_out_path "video_out.mp4"
