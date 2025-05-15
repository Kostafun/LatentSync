FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04

# # Set environment variables
# ENV DEBIAN_FRONTEND=noninteractive
# ENV PYTHONUNBUFFERED=1
# ENV PYTHONPATH=/app
# ENV DEBIAN_FRONTEND=noninteractive \
#     PYTHONUNBUFFERED=1 \
#     PIP_NO_CACHE_DIR=on 

RUN ln -sf $(which python3.11) /usr/local/bin/python && \
    ln -sf $(which python3.11) /usr/local/bin/python3

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt update && \
    apt upgrade -y && \
    apt install -y \
      python3-dev \
      python3-pip \
      python3-venv \
      git \
      git-lfs \
      wget \
      curl \
      ffmpeg \
      unzip &&\
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean -y
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Install system dependencies
# RUN apt-get update && apt-get install -y \
#     wget \
#     git \
#     ffmpeg \
#     libgl1 \
#     python3.10 \
#     python3.10-dev \
#     python3-pip \
#     && rm -rf /var/lib/apt/lists/*

# Set up Python
#RUN ln -s /usr/bin/python3.10 /usr/bin/python
#RUN pip install --upgrade pip

# Set working directory
#WORKDIR /workspace

#RUN pip3 install --no-cache-dir torch==2.4.0 torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# RUN git clone -b runpod2 https://github.com/Kostafun/LatentSync && \
#     cd /workspace/LatentSync  && \
#     pip3 install -r requirements.txt

# Create necessary directories
# RUN mkdir -p /root/.cache/torch/hub/checkpoints

# Download checkpoints from HuggingFace
#RUN huggingface-cli download ByteDance/LatentSync --local-dir checkpoints --exclude "*.git*" "README.md"
# RUN huggingface-cli download ByteDance/LatentSync latentsync_unet.pt --local-dir checkpoints 
# RUN huggingface-cli download ByteDance/LatentSync whisper/tiny.pt --local-dir checkpoints 

# Create soft links for auxiliary models
#RUN ln -s /app/checkpoints/auxiliary/2DFAN4-cd938726ad.zip /root/.cache/torch/hub/checkpoints/2DFAN4-cd938726ad.zip && \
#    ln -s /app/checkpoints/auxiliary/s3fd-619a316812.pth /root/.cache/torch/hub/checkpoints/s3fd-619a316812.pth && \
#    ln -s /app/checkpoints/auxiliary/vgg16-397923af.pth /root/.cache/torch/hub/checkpoints/vgg16-397923af.pth

# Expose port for Gradio app
#EXPOSE 7860
# COPY --chmod=755 rp_handler.py /workspace/LatentSync/rp_handler.py

WORKDIR /workspace

# Copy the project files (.dockerignore will exclude mp3/mp4 files)
COPY . /workspace/

#ENV PYTHONPATH="/workspace:${PYTHONPATH}"
#ENV PATH="/workspace/.venv/bin:${PATH}"

ADD start.sh /start.sh

# Start the container
RUN chmod +x /start.sh
ENTRYPOINT /start.sh