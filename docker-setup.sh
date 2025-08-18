#!/bin/bash

# Bee Detection Docker Setup Script
echo "🐳 Setting up Docker environment for Bee Detection System"
echo "=" * 60

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"

# Build and start services
echo "🔨 Building Docker image..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service status
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📋 Available commands:"
echo "  View logs:           docker-compose logs -f bee-processor"
echo "  Stop services:       docker-compose down"
echo "  Restart processor:   docker-compose restart bee-processor"
echo "  Access RabbitMQ UI:  http://localhost:15672 (guest/guest)"
echo ""
echo "📁 Mounted directories:"
echo "  Input photos:        ./input_photos (read-only)"
echo "  Output results:      ./output"
echo "  Database:            ./bee_detection.db"
echo "  Crop polygon:        ./crop_polygon.pkl"
echo ""
echo "🔍 To monitor processing:"
echo "  docker-compose logs -f bee-processor"
