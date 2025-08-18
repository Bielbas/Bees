#!/bin/bash

# Docker Build Script with Fallback Options
echo "🔨 Building Bee Detection Docker Image"
echo "=" * 50

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed!"
    exit 1
fi

# Function to build with specific dockerfile
build_with_dockerfile() {
    local dockerfile=$1
    local tag=$2
    
    echo "🔨 Attempting build with $dockerfile..."
    
    if docker build -f "$dockerfile" -t "$tag" .; then
        echo "✅ Successfully built with $dockerfile"
        return 0
    else
        echo "❌ Build failed with $dockerfile"
        return 1
    fi
}

# Try building with fixed dockerfile first (addresses NumPy/OpenCV compatibility)
if build_with_dockerfile "Dockerfile.fixed" "bee-processor:fixed"; then
    echo "🎉 Build successful with fixed Dockerfile!"
    
    # Update docker-compose to use the built image
    echo "📝 Updating docker-compose to use built image..."
    sed -i 's/dockerfile: Dockerfile.minimal/# dockerfile: Dockerfile.minimal/' docker-compose.vps.yml
    sed -i '/container_name: bee-processor/a\    image: bee-processor:fixed' docker-compose.vps.yml
    
elif build_with_dockerfile "Dockerfile.minimal" "bee-processor:minimal"; then
    echo "🎉 Build successful with minimal Dockerfile!"
    
    # Update docker-compose to use the built image
    echo "📝 Updating docker-compose to use built image..."
    sed -i 's/dockerfile: Dockerfile.minimal/# dockerfile: Dockerfile.minimal/' docker-compose.vps.yml
    sed -i '/container_name: bee-processor/a\    image: bee-processor:minimal' docker-compose.vps.yml
    
elif build_with_dockerfile "Dockerfile" "bee-processor:full"; then
    echo "🎉 Build successful with full Dockerfile!"
    
    # Update docker-compose to use the built image
    echo "📝 Updating docker-compose to use built image..."
    sed -i 's/dockerfile: Dockerfile/# dockerfile: Dockerfile/' docker-compose.vps.yml
    sed -i '/container_name: bee-processor/a\    image: bee-processor:full' docker-compose.vps.yml
    
else
    echo "❌ All build attempts failed!"
    echo ""
    echo "🔍 Troubleshooting steps:"
    echo "1. Check internet connection"
    echo "2. Try: docker system prune -f"
    echo "3. Update Docker: sudo apt update && sudo apt upgrade docker.io"
    echo "4. Check available disk space: df -h"
    echo "5. Try building on a different machine and push to registry"
    echo ""
    echo "📋 Manual build options:"
    echo "  docker build -f Dockerfile.minimal -t bee-processor:minimal ."
    echo "  docker build -f Dockerfile -t bee-processor:full ."
    exit 1
fi

echo ""
echo "✅ Docker image ready for deployment!"
echo "🚀 Next steps:"
echo "  1. Configure .env file"
echo "  2. Run: docker-compose -f docker-compose.vps.yml up -d"
