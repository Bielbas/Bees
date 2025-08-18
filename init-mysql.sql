-- MySQL Database Initialization for Bee Detection System
-- Run this script to create the database and tables

-- Create database
CREATE DATABASE IF NOT EXISTS bee_detection 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- Use the database
USE bee_detection;

-- Create bee_detections table
CREATE TABLE IF NOT EXISTS bee_detections (
    id INT AUTO_INCREMENT PRIMARY KEY,
    hive_id VARCHAR(50) NOT NULL,
    filename VARCHAR(255),
    timestamp DATETIME,
    bee_coverage DECIMAL(10, 6),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_hive_timestamp (hive_id, timestamp),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create a user for the application (optional, recommended for security)
-- CREATE USER IF NOT EXISTS 'bee_app'@'%' IDENTIFIED BY 'your_secure_password';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON bee_detection.* TO 'bee_app'@'%';
-- FLUSH PRIVILEGES;

-- Show table structure
DESCRIBE bee_detections;

-- Show that database is ready
SELECT 'Database bee_detection is ready!' as status;
