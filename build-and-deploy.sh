#!/bin/bash

# Multi-stage Docker Build and Deploy Script for AutoTube Endpoint
# This script builds and pushes both the base image and application image to Docker Hub

set -e  # Exit on any error

# Configuration - Update these variables with your Docker Hub details
DOCKER_HUB_USERNAME="${DOCKER_HUB_USERNAME:-your-dockerhub-username}"
BASE_IMAGE_NAME="${BASE_IMAGE_NAME:-autotube-base}"
APP_IMAGE_NAME="${APP_IMAGE_NAME:-autotube-app}"
BASE_TAG="${BASE_TAG:-latest}"
APP_TAG="${APP_TAG:-latest}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Function to check if user is logged into Docker Hub
check_docker_login() {
    if ! docker info | grep -q "Username:"; then
        print_warning "You may not be logged into Docker Hub. Run 'docker login' if needed."
    else
        print_success "Docker Hub login detected"
    fi
}

# Function to build base image
build_base_image() {
    local full_image_name="${DOCKER_HUB_USERNAME}/${BASE_IMAGE_NAME}:${BASE_TAG}"
    
    print_status "Building base image: ${full_image_name}"
    print_status "This will take a while as it downloads ~7GB of models..."
    
    docker build \
        -f Dockerfile.base \
        -t "${full_image_name}" \
        . || {
        print_error "Failed to build base image"
        exit 1
    }
    
    print_success "Base image built successfully: ${full_image_name}"
    
    # Show image size
    local image_size=$(docker images "${full_image_name}" --format "table {{.Size}}" | tail -n 1)
    print_status "Base image size: ${image_size}"
}

# Function to push base image
push_base_image() {
    local full_image_name="${DOCKER_HUB_USERNAME}/${BASE_IMAGE_NAME}:${BASE_TAG}"
    
    print_status "Pushing base image to Docker Hub: ${full_image_name}"
    
    docker push "${full_image_name}" || {
        print_error "Failed to push base image"
        exit 1
    }
    
    print_success "Base image pushed successfully"
}

# Function to update application Dockerfile with correct base image
update_app_dockerfile() {
    local base_image="${DOCKER_HUB_USERNAME}/${BASE_IMAGE_NAME}:${BASE_TAG}"
    
    print_status "Updating Dockerfile.app to use base image: ${base_image}"
    
    # Create a temporary file with the updated Dockerfile
    sed "s|your-dockerhub-username/autotube-base:latest|${base_image}|g" Dockerfile.app > Dockerfile.app.tmp
    mv Dockerfile.app.tmp Dockerfile.app
    
    print_success "Dockerfile.app updated"
}

# Function to build application image
build_app_image() {
    local full_image_name="${DOCKER_HUB_USERNAME}/${APP_IMAGE_NAME}:${APP_TAG}"
    
    print_status "Building application image: ${full_image_name}"
    
    docker build \
        -f Dockerfile.app \
        -t "${full_image_name}" \
        . || {
        print_error "Failed to build application image"
        exit 1
    }
    
    print_success "Application image built successfully: ${full_image_name}"
    
    # Show image size
    local image_size=$(docker images "${full_image_name}" --format "table {{.Size}}" | tail -n 1)
    print_status "Application image size: ${image_size}"
}

# Function to push application image
push_app_image() {
    local full_image_name="${DOCKER_HUB_USERNAME}/${APP_IMAGE_NAME}:${APP_TAG}"
    
    print_status "Pushing application image to Docker Hub: ${full_image_name}"
    
    docker push "${full_image_name}" || {
        print_error "Failed to push application image"
        exit 1
    }
    
    print_success "Application image pushed successfully"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS] COMMAND"
    echo ""
    echo "Commands:"
    echo "  base-only     Build and push only the base image"
    echo "  app-only      Build and push only the application image (requires base image)"
    echo "  full          Build and push both base and application images"
    echo "  build-only    Build both images but don't push to Docker Hub"
    echo ""
    echo "Environment Variables:"
    echo "  DOCKER_HUB_USERNAME  Your Docker Hub username (default: your-dockerhub-username)"
    echo "  BASE_IMAGE_NAME      Base image name (default: autotube-base)"
    echo "  APP_IMAGE_NAME       Application image name (default: autotube-app)"
    echo "  BASE_TAG             Base image tag (default: latest)"
    echo "  APP_TAG              Application image tag (default: latest)"
    echo ""
    echo "Examples:"
    echo "  DOCKER_HUB_USERNAME=myusername $0 full"
    echo "  DOCKER_HUB_USERNAME=myusername BASE_TAG=v1.0 APP_TAG=v1.0 $0 full"
}

# Main script logic
main() {
    if [ $# -eq 0 ]; then
        show_usage
        exit 1
    fi
    
    local command=$1
    
    # Validate Docker Hub username
    if [ "${DOCKER_HUB_USERNAME}" = "your-dockerhub-username" ]; then
        print_error "Please set DOCKER_HUB_USERNAME environment variable"
        print_error "Example: DOCKER_HUB_USERNAME=myusername $0 ${command}"
        exit 1
    fi
    
    print_status "Starting multi-stage Docker build process"
    print_status "Docker Hub Username: ${DOCKER_HUB_USERNAME}"
    print_status "Base Image: ${DOCKER_HUB_USERNAME}/${BASE_IMAGE_NAME}:${BASE_TAG}"
    print_status "App Image: ${DOCKER_HUB_USERNAME}/${APP_IMAGE_NAME}:${APP_TAG}"
    
    check_docker
    check_docker_login
    
    case $command in
        "base-only")
            build_base_image
            push_base_image
            ;;
        "app-only")
            update_app_dockerfile
            build_app_image
            push_app_image
            ;;
        "full")
            build_base_image
            push_base_image
            update_app_dockerfile
            build_app_image
            push_app_image
            ;;
        "build-only")
            build_base_image
            update_app_dockerfile
            build_app_image
            print_status "Images built but not pushed to Docker Hub"
            ;;
        *)
            print_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
    
    print_success "Multi-stage Docker build process completed!"
    print_status "Next steps:"
    print_status "1. Use ${DOCKER_HUB_USERNAME}/${APP_IMAGE_NAME}:${APP_TAG} in your deployment"
    print_status "2. For code changes, only rebuild the app image with: $0 app-only"
    print_status "3. The base image (~7GB) will be cached and reused"
}

# Run main function with all arguments
main "$@"