# Bee Detection System - VPS Deployment Guide

## 🚀 Overview

This system processes bee images from RabbitMQ queues and stores detection results in MySQL database. It's designed for VPS deployment with external RabbitMQ and MySQL services.

## 📋 Prerequisites

### VPS Requirements
- Ubuntu 20.04+ or similar Linux distribution
- Docker and Docker Compose installed
- Network access to RabbitMQ and MySQL services
- At least 2GB RAM and 10GB storage

### External Services
- **RabbitMQ**: Message queue for receiving images
- **MySQL**: Database for storing detection results

## 🔧 Configuration

### 1. Environment Setup

```bash
# Clone or upload project to VPS
git clone <your-repo> bee-detection
cd bee-detection

# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

### 2. Environment Variables

Update `.env` with your actual values:

```env
# RabbitMQ Configuration
RABBITMQ_HOST=your-rabbitmq-host
RABBITMQ_PORT=5672
RABBITMQ_USER=your-username
RABBITMQ_PASS=your-password
RABBITMQ_QUEUE=photo-uploads

# MySQL Configuration
MYSQL_HOST=your-mysql-host
MYSQL_PORT=3306
MYSQL_USER=your-username
MYSQL_PASSWORD=your-password
MYSQL_DATABASE=bee_detection

# Processing Configuration
HIVE_ID=HIVE_01
BACKGROUND_SIZE=15
SAVE_INTERMEDIATE=true
```

### 3. Database Setup

Initialize MySQL database:

```bash
# Connect to MySQL
mysql -h your-mysql-host -u your-username -p

# Run initialization script
mysql -h your-mysql-host -u your-username -p < init-mysql.sql
```

## 🚀 Deployment

### Automatic Deployment

```bash
# Make deployment script executable
chmod +x deploy-vps.sh

# Run deployment
./deploy-vps.sh
```

### Manual Deployment

```bash
# Build Docker image
docker-compose -f docker-compose.vps.yml build

# Start service
docker-compose -f docker-compose.vps.yml up -d

# Check status
docker-compose -f docker-compose.vps.yml ps
```

## 📊 Monitoring

### View Logs
```bash
# Real-time logs
docker-compose -f docker-compose.vps.yml logs -f bee-processor

# Last 100 lines
docker-compose -f docker-compose.vps.yml logs --tail=100 bee-processor
```

### Check Health
```bash
# Service status
docker-compose -f docker-compose.vps.yml ps

# Health check
docker exec bee-processor python -c "print('✅ Service is running')"
```

### Database Monitoring
```bash
# Connect to database
mysql -h your-mysql-host -u your-username -p bee_detection

# Check recent detections
SELECT hive_id, filename, timestamp, bee_coverage 
FROM bee_detections 
ORDER BY timestamp DESC 
LIMIT 10;

# Count detections by hive
SELECT hive_id, COUNT(*) as detection_count 
FROM bee_detections 
GROUP BY hive_id;
```

## 🔄 Operations

### Start/Stop Service
```bash
# Start
docker-compose -f docker-compose.vps.yml up -d

# Stop
docker-compose -f docker-compose.vps.yml down

# Restart
docker-compose -f docker-compose.vps.yml restart bee-processor
```

### Update Application
```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose -f docker-compose.vps.yml down
docker-compose -f docker-compose.vps.yml build --no-cache
docker-compose -f docker-compose.vps.yml up -d
```

### Backup Data
```bash
# Backup MySQL database
mysqldump -h your-mysql-host -u your-username -p bee_detection > bee_detection_backup.sql

# Backup output files
tar -czf output_backup.tar.gz output/
```

## 📁 File Structure

```
bee-detection/
├── Dockerfile                 # Container definition
├── docker-compose.vps.yml     # VPS deployment configuration
├── deploy-vps.sh             # Deployment script
├── .env.example              # Environment template
├── .env                      # Your configuration (create from example)
├── init-mysql.sql            # Database initialization
├── requirements.txt          # Python dependencies
├── crop_polygon.pkl          # Crop region (created on first run)
├── bee_database.py           # MySQL database handler
├── bee_detector.py           # Bee detection logic
├── image_processor.py        # Image processing
├── rabbitmq_processor.py     # Main processor
├── run_rabbitmq_processor.py # Application entry point
├── input_photos/             # Input images (mounted)
└── output/                   # Detection results (mounted)
```

## 🐛 Troubleshooting

### Common Issues

**1. Connection to RabbitMQ fails**
```bash
# Check network connectivity
telnet your-rabbitmq-host 5672

# Verify credentials in .env file
# Check RabbitMQ logs
```

**2. MySQL connection fails**
```bash
# Test MySQL connection
mysql -h your-mysql-host -u your-username -p

# Check if database exists
SHOW DATABASES;

# Verify user permissions
SHOW GRANTS FOR 'your-username'@'%';
```

**3. Container fails to start**
```bash
# Check detailed logs
docker-compose -f docker-compose.vps.yml logs bee-processor

# Check container status
docker ps -a

# Debug inside container
docker exec -it bee-processor bash
```

**4. Crop polygon missing**
- The system will prompt for manual cropping on first image
- Ensure input_photos directory contains test images
- The crop_polygon.pkl file will be created automatically

### Performance Tuning

**Memory Optimization**
- Adjust `BACKGROUND_SIZE` (default: 15)
- Set `SAVE_INTERMEDIATE=false` to save disk space
- Monitor container memory usage

**Processing Speed**
- Adjust `BACKGROUND_UPDATE_FREQ` based on lighting changes
- Tune detection parameters in DETECTION_CONFIG

## 📞 Support

For issues and questions:
1. Check logs: `docker-compose -f docker-compose.vps.yml logs -f bee-processor`
2. Verify configuration in `.env`
3. Test external service connections
4. Check database connectivity and permissions

## 🔒 Security Notes

- Use strong passwords for database connections
- Limit database user permissions to necessary operations only
- Keep Docker images updated
- Use environment variables for sensitive configuration
- Consider using Docker secrets for production deployment
