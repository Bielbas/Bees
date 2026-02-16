import os


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
    'output_dir': os.getenv('OUTPUT_DIR', 'output'),       
    'save_intermediate': os.getenv('SAVE_INTERMEDIATE', 'True').lower() == 'true',   
    'background_update_frequency': int(os.getenv('BACKGROUND_UPDATE_FREQ', '1')),
    'hive_id': os.getenv('HIVE_ID', None)  
}

MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', '3306')),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'bee_detection'),
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}