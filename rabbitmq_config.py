RABBITMQ_CONFIG = {
    'host': 'localhost',
    'port': 5672,         
    'username': 'guest',  
    'password': 'guest',  
    'queue_name': 'photo-uploads',  
    'exchange': '',       
    'routing_key': 'bee_images'  
}

PROCESSING_CONFIG = {
    'background_size': 15,        
    'crop_polygon_file': 'crop_polygon.pkl',  
    'output_dir': 'output',       
    'save_intermediate': True,   
    'background_update_frequency': 1,
    'database_path': 'bee_detection.db',  
    'hive_id': None  
}

DETECTION_CONFIG = {
    'detection_thresholds': [15, 25, 35, 45],
    'min_bee_area': 20,
    'max_bee_area': 8000,
    'color_lower_bee': [5, 20, 20],
    'color_upper_bee': [25, 255, 180],
    'min_aspect_ratio': 0.3,
    'max_aspect_ratio': 3.0,
    'min_solidity': 0.3
}
