#!/bin/bash
set -euo pipefail

# Variables
IMAGE_NAME="temp_image"
CONTAINER_NAME="temp_container"
file_list="build_context_files.txt"

# Function to clean up the container if it exists
cleanup_container() {
    if docker ps -aq -f name=$CONTAINER_NAME > /dev/null; then
        echo "Removing existing container with the name $CONTAINER_NAME..."
        docker rm -f $CONTAINER_NAME
    fi
}

# Build Docker image
echo "Building Docker image..."
docker build -t $IMAGE_NAME -f ./compose/production/django/Dockerfile .

# Ensure no conflicting container is running
cleanup_container

# Create and start the container
echo "Creating and starting a temporary container..."
docker run -d --name $CONTAINER_NAME --entrypoint "/bin/sh" $IMAGE_NAME -c "while true; do sleep 1; done"

# Check logs to diagnose any issues
echo "Checking logs of the container..."
docker logs $CONTAINER_NAME || true

# List files in the container
echo "Listing files in the container and saving to $file_list:"
if docker ps -q -f name=$CONTAINER_NAME > /dev/null; then
    docker exec $CONTAINER_NAME find /app 2>&1 | tee -a "$file_list"
else
    echo "The container is not running. Check the logs above for details."
fi

# Clean up the container
echo "Removing the temporary container..."
cleanup_container

echo "Done."
