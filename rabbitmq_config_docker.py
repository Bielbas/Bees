import os

# RabbitMQ configuration with Docker support
RABBITMQ_CONFIG = {
    'host': os.getenv('RABBITMQ_HOST', 'localhost'),
    'port': int(os.getenv('RABBITMQ_PORT', '5672')),         
    'username': os.getenv('RABBITMQ_USER', 'guest'),  
    'password': os.getenv('RABBITMQ_PASS', 'guest'),  
    'queue_name': os.getenv('RABBITMQ_QUEUE', 'photo-uploads'),  
    'exchange': os.getenv('RABBITMQ_EXCHANGE', ''),       
    'routing_key': os.getenv('RABBITMQ_ROUTING_KEY', 'bee_images')  
}

PROCESSING_CONFIG = {
    'background_size': int(os.getenv('BACKGROUND_SIZE', '15')),        
    'crop_polygon_file': os.getenv('CROP_POLYGON_FILE', 'crop_polygon.pkl'),  
    'output_dir': os.getenv('OUTPUT_DIR', 'output'),       
    'save_intermediate': os.getenv('SAVE_INTERMEDIATE', 'True').lower() == 'true',   
    'background_update_frequency': int(os.getenv('BACKGROUND_UPDATE_FREQ', '1')),
    'database_path': os.getenv('DATABASE_PATH', 'bee_detection.db'),  
    'hive_id': os.getenv('HIVE_ID', None)  
}

DETECTION_CONFIG = {
    'detection_thresholds': [15, 25, 35, 45],
    'min_bee_area': int(os.getenv('MIN_BEE_AREA', '20')),
    'max_bee_area': int(os.getenv('MAX_BEE_AREA', '8000')),
    'color_lower_bee': [5, 20, 20],
    'color_upper_bee': [25, 255, 180],
    'min_aspect_ratio': float(os.getenv('MIN_ASPECT_RATIO', '0.3')),
    'max_aspect_ratio': float(os.getenv('MAX_ASPECT_RATIO', '3.0')),
    'min_solidity': float(os.getenv('MIN_SOLIDITY', '0.3'))
}
