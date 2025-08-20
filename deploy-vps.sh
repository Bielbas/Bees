#!/bin/bash

# VPS Deployment Script for Bee Detection System
echo "🚀 Deploying Bee Detection System to VPS"
echo "=" * 60

# Check if required files exist
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "📋 Please create .env file from .env.example:"
    echo "   cp .env.example .env"
    echo "   # Then edit .env with your actual configuration"
    exit 1
fi

if [ ! -f "crop_polygon.pkl" ]; then
    echo "⚠️  crop_polygon.pkl not found!"
    echo "📋 This file will be created when you first run the processor"
    echo "   Make sure to have input photos available for cropping"
fi

# Load environment variables
source .env

echo "🔍 Configuration Check:"
echo "  RabbitMQ: ${RABBITMQ_HOST}:${RABBITMQ_PORT}"
echo "  MySQL: ${MYSQL_HOST}:${MYSQL_PORT}"
echo "  Database: ${MYSQL_DATABASE}"
echo "  Hive ID: ${HIVE_ID}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Installing Docker..."
    # Install Docker (Ubuntu/Debian)
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "🔄 Please log out and back in to use Docker without sudo"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Installing..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

echo "✅ Docker and Docker Compose are ready"

# Create directories
echo "📁 Creating directories..."
mkdir -p input_photos output

# Build and start the service
echo "🔨 Building Docker image..."

# Make build script executable
chmod +x build-docker.sh

# Try building with fallback options
if ./build-docker.sh; then
    echo "✅ Docker image built successfully"
else
    echo "❌ Docker build failed. Trying alternative approach..."
    
    # Fallback: try to pull a pre-built image or build with different options
    echo "🔄 Attempting minimal build with specific options..."
    
    # Clear Docker cache and try again
    docker system prune -f
    
    # Try building minimal version with more specific options
    if docker build -f Dockerfile.minimal --no-cache --progress=plain -t bee-processor:minimal .; then
        echo "✅ Minimal build successful"
        # Update docker-compose
        sed -i 's/build:/# build:/' docker-compose.vps.yml
        sed -i 's/context: ./# context: ./' docker-compose.vps.yml
        sed -i 's/dockerfile: Dockerfile.minimal/# dockerfile: Dockerfile.minimal/' docker-compose.vps.yml
        sed -i '/container_name: bee-processor/a\    image: bee-processor:minimal' docker-compose.vps.yml
    else
        echo "❌ All build attempts failed. Please check the error messages above."
        echo "💡 Try running: docker build -f Dockerfile.minimal --no-cache --progress=plain -t bee-processor:minimal ."
        exit 1
    fi
fi

echo "🚀 Starting bee processor..."
docker-compose -f docker-compose.vps.yml up -d

# Wait for service to start
echo "⏳ Waiting for service to start..."
sleep 15

# Check service status
echo "📊 Service Status:"
docker-compose -f docker-compose.vps.yml ps

echo "📋 Checking logs:"
docker-compose -f docker-compose.vps.yml logs --tail=20 bee-processor

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📋 Available commands:"
echo "  View logs:           docker-compose -f docker-compose.vps.yml logs -f bee-processor"
echo "  Stop service:        docker-compose -f docker-compose.vps.yml down"
echo "  Restart service:     docker-compose -f docker-compose.vps.yml restart bee-processor"
echo "  Update and restart:  ./deploy-vps.sh"
echo ""
echo "📁 Directories:"
echo "  Input photos:        ./input_photos"
echo "  Output results:      ./output"
echo "  Crop polygon:        ./crop_polygon.pkl"
echo ""
echo "🔍 To monitor processing:"
echo "  docker-compose -f docker-compose.vps.yml logs -f bee-processor"
echo ""
echo "📊 To check MySQL database:"
echo "  mysql -h ${MYSQL_HOST} -u ${MYSQL_USER} -p ${MYSQL_DATABASE}"
echo "  SELECT * FROM bee_detections ORDER BY timestamp DESC LIMIT 10;"
