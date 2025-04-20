FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# # Set environment variables
# ENV DEBIAN_FRONTEND=noninteractive
# ENV PYTHONUNBUFFERED=1
# ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    git \
    ffmpeg \
    libgl1 \
    python3.10 \
    python3.10-dev \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Set up Python
RUN ln -s /usr/bin/python3.10 /usr/bin/python
RUN pip install --upgrade pip

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
# COPY requirements.txt /requirements.txt

# Install Python dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p /root/.cache/torch/hub/checkpoints

# Download checkpoints from HuggingFace
#RUN huggingface-cli download ByteDance/LatentSync --local-dir checkpoints --exclude "*.git*" "README.md"
RUN huggingface-cli download ByteDance/LatentSync latentsync_unet.pt --local-dir checkpoints 
RUN huggingface-cli download ByteDance/LatentSync whisper/tiny.pt --local-dir checkpoints 

# Create soft links for auxiliary models
#RUN ln -s /app/checkpoints/auxiliary/2DFAN4-cd938726ad.zip /root/.cache/torch/hub/checkpoints/2DFAN4-cd938726ad.zip && \
#    ln -s /app/checkpoints/auxiliary/s3fd-619a316812.pth /root/.cache/torch/hub/checkpoints/s3fd-619a316812.pth && \
#    ln -s /app/checkpoints/auxiliary/vgg16-397923af.pth /root/.cache/torch/hub/checkpoints/vgg16-397923af.pth

# Expose port for Gradio app
#EXPOSE 7860

# Set the default command to run the Gradio app
CMD ["python3", "-u", "rp_handler.py"]