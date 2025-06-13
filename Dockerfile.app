# Use the base image that contains all heavy dependencies
# Replace 'your-dockerhub-username' with your actual Docker Hub username
FROM kostafun/latentsync-base:latest

# Set working directory (should already be set in base image)
WORKDIR /workspace

# Set environment variables (inherited from base image but ensuring they're set)
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/workspace
ENV PATH="/workspace/.venv/bin:${PATH}"
ENV VIRTUAL_ENV="/workspace/.venv"

# Copy the entire endpoint folder contents (excluding what's in .dockerignore)
COPY . /workspace/

# Create symbolic links for auxiliary models (from the original Dockerfile)
RUN ln -s /workspace/checkpoints/auxiliary/2DFAN4-cd938726ad.zip /root/.cache/torch/hub/checkpoints/2DFAN4-cd938726ad.zip && \
    ln -s /workspace/checkpoints/auxiliary/s3fd-619a316812.pth /root/.cache/torch/hub/checkpoints/s3fd-619a316812.pth && \
    ln -s /workspace/checkpoints/auxiliary/vgg16-397923af.pth /root/.cache/torch/hub/checkpoints/vgg16-397923af.pth

# Copy and set up the start script
ADD start.sh /start.sh
RUN chmod +x /start.sh

# Verify the application setup
RUN echo "=== APPLICATION IMAGE SETUP VERIFICATION ===" && \
    echo "Current directory: $(pwd)" && \
    echo "Directory contents:" && ls -la && \
    echo "Models available:" && ls -la /workspace/checkpoints/ && \
    echo "Virtual environment active:" && which python && \
    echo "Python path:" && python -c "import sys; print(sys.path)" && \
    echo "Start script permissions:" && ls -la /start.sh

# Set the entrypoint to the start script
ENTRYPOINT ["/start.sh"]

# This lightweight application image only contains the source code (~3.4M)
# and reuses the heavy base image layer (~7GB) with models and dependencies
# Example build: docker build -f Dockerfile.app -t your-dockerhub-username/autotube-app:latest .
#               docker push your-dockerhub-username/autotube-app:latest