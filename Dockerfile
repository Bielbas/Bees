# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies required for OpenCV and image processing
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libatlas-base-dev \
    gfortran \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY bee_database.py .
COPY bee_detector.py .
COPY image_processor.py .
COPY manual_cropper.py .
COPY rabbitmq_config.py .
COPY rabbitmq_processor.py .
COPY run_rabbitmq_processor.py .

# Copy the crop polygon file if it exists
COPY crop_polygon.pkl* ./

# Create necessary directories
RUN mkdir -p output input_photos

# Create a non-root user for security
RUN groupadd -r beeuser && useradd -r -g beeuser beeuser
RUN chown -R beeuser:beeuser /app
USER beeuser

# Expose any ports if needed (none required for this RabbitMQ consumer)
# EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import pika; from rabbitmq_config import RABBITMQ_CONFIG; \
  conn = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_CONFIG['host'])); \
  conn.close()" || exit 1

# Default command
CMD ["python", "run_rabbitmq_processor.py"]
