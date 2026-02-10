import pika
import json
import cv2
import numpy as np
import base64
import pickle
import os
from datetime import datetime
from pathlib import Path
from collections import deque
import threading
import time

from manual_cropper import ManualCropper
from image_processor import ImageProcessor
from bee_detector import BeeDetector
from bee_database import BeeDatabase
from rabbitmq_config_docker import RABBITMQ_CONFIG, PROCESSING_CONFIG, DETECTION_CONFIG


class RabbitMQBeeProcessor:
    """Processes bee images from RabbitMQ queue in real time."""
    
    def __init__(self, rabbit_config=None):
        """Initialize processor"""

        self.config = rabbit_config or RABBITMQ_CONFIG
        self.processing_config = PROCESSING_CONFIG
        
        self.crop_polygon = None
        self.image_processor = None
        self.bee_detector = None
        self.bee_database = None 
        self.image_buffer = deque(maxlen=self.processing_config['background_size'])
        self.results = []
        self.image_count = 0
        self.is_running = False
        self.connection = None
        self.channel = None
        
        self.output_dir = Path(self.processing_config['output_dir'])
        self.output_dir.mkdir(exist_ok=True)
        
        if self.output_dir.exists() and self.output_dir.is_dir():
            try:
                import shutil
                for item in self.output_dir.iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                print(f"Clean: {self.output_dir}")
            except Exception as e:
                print(f"Could not clean: {e}")
                

    def load_crop_polygon(self, first_image=None):
        """Load or create crop polygon"""

        polygon_file = self.processing_config['crop_polygon_file']
        
        try:
            with open(polygon_file, "rb") as f:
                self.crop_polygon = pickle.load(f)
        except FileNotFoundError:
            if first_image is not None:
                temp_path = "temp_first_image.jpg"
                cv2.imwrite(temp_path, first_image)
                cropper = ManualCropper()
                self.crop_polygon = cropper.get_crop_polygon(temp_path)
                
                if self.crop_polygon:
                    with open(polygon_file, "wb") as f:
                        pickle.dump(self.crop_polygon, f)
                    
                    Path(temp_path).unlink()
                else:
                    print("Can't define crop polygon from first image")
                    return False
            else:
                print("Missing polygon file and first image")
                return False
        
        if self.crop_polygon:
            self.image_processor = ImageProcessor(self.crop_polygon)
            return True
        return False
    

    def connect_to_rabbitmq(self):
        """Connect with RabbitMQ."""

        try:
            credentials = pika.PlainCredentials(
                self.config['username'], 
                self.config['password']
            )
            
            parameters = pika.ConnectionParameters(
                host=self.config['host'],
                port=self.config['port'],
                credentials=credentials
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            self.channel.queue_declare(queue=self.config['queue_name'], durable=True)
            
            print(f"Connected with RabbitMQ: {self.config['host']}:{self.config['port']}")
            return True
            
        except Exception as e:
            print(f"Error connecting with RabbitMQ: {e}")
            return False
    
    def decode_image_from_message(self, body, properties=None):
        """
        Decode image from RabbitMQ message.
        
        Args:
            body: RabbitMQ message content (raw bytes image data)
            properties: Message properties (may contain filename)
            
        Returns:
            tuple: (numpy.ndarray, filename) - Image as OpenCV array and filename or (None, None)
        """
        try:
            filename = "unknown.jpg"
            
            if properties and hasattr(properties, 'headers') and properties.headers:
                if 'filename' in properties.headers:
                    filename = properties.headers['filename']
                    if isinstance(filename, bytes):
                        filename = filename.decode('utf-8')
            
            image_data = body
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                print("Failed to decode image")
                return None, None
                
            print(f"Decoded image: {image.shape}, file: {filename}")
            return image, filename
            
        except Exception as e:
            print(f"Image decoding error: {e}")
            return None, None
    

    def create_background_from_buffer(self):
        """Create background image from current image buffer"""
        
        if len(self.image_buffer) < 5: 
            print("Not enough images in buffer to create background")
            return None
                    
        background_images = []
        for img in self.image_buffer:
            background_images.append({
                'image': img,
                'mask': None 
            })
        
        background = self.image_processor.create_background(background_images)
        if background is not None:
            bg_path = self.output_dir / f"background_{self.image_count}.jpg"
            cv2.imwrite(str(bg_path), background)
        
        return background
    
    def process_single_image(self, image, timestamp=None, filename=None):
        """
        Process single image.
        
        Args:
            image: Image as numpy array
            timestamp: Timestamp from RabbitMQ properties (optional)
            filename: Filename from API (optional)
            
        Returns:
            dict: Detection results or None
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        if filename is None:
            filename = f"image_{self.image_count:06d}_{timestamp.replace(':', '_')}.jpg"
        else:
            import re
            filename = re.sub(r'[^\w\-_\.]', '_', filename)
            if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                filename = f"{filename}.jpg"
                
        cropped_img, crop_mask = self.image_processor.crop_image_array(image)
        if cropped_img is None:
            print("Failed to crop image")
            return None
        
        if self.processing_config['save_intermediate']:
            cropped_path = self.output_dir / f"cropped_{filename}"
            cv2.imwrite(str(cropped_path), cropped_img)
        
        self.image_buffer.append(cropped_img)
        
        if self.bee_detector is None:
            if len(self.image_buffer) >= self.processing_config['background_size']:
                background = self.create_background_from_buffer()
                if background is not None:
                    self.bee_detector = BeeDetector(background, self.image_processor.polygon_area)
                else:
                    print("Failed to create first background")
                    return None
            else:
                return None
        else:
            if (self.image_count % self.processing_config['background_update_frequency'] == 0 and 
                len(self.image_buffer) >= self.processing_config['background_size']):
                
                background = self.create_background_from_buffer()
                if background is not None:
                    self.bee_detector.update_background(background)
        
        if self.bee_detector is not None:
            result = self.bee_detector.analyze_image(cropped_img, filename)
            if result:
                result['original_timestamp'] = timestamp
                result['timestamp'] = timestamp 
                result['filename'] = filename
                result['image_count'] = self.image_count
                result['total_area'] = self.image_processor.polygon_area
                result['bee_area'] = int(result['bee_percentage'] * self.image_processor.polygon_area / 100)
                result['background_updated'] = (self.image_count % self.processing_config['background_update_frequency'] == 0)
                
                if self.processing_config['save_intermediate']:
                    mask_path = self.output_dir / f"bee_mask_{filename}"
                    cv2.imwrite(str(mask_path), result['bee_mask'])
                    
                    vis = self.bee_detector.create_visualization(cropped_img, result['bee_mask'], [])
                    vis_path = self.output_dir / f"visualization_{filename}"
                    cv2.imwrite(str(vis_path), vis)
                
                print(f"{filename}: {result['bee_percentage']:.2f}% bee coverage, {result['detection_method']})")
                
                return result
        
        return None
    
    
    def callback(self, ch, method, properties, body):
        """
        Callback called when receiving message from RabbitMQ.
        
        Args:
            ch: Channel
            method: Method frame
            properties: Properties (contain filename in headers)
            body: Message body (raw image bytes)
        """
        try:            
            image, filename = self.decode_image_from_message(body, properties)
            if image is None:
                print("Failed to decode image - skipping")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
            
            timestamp = None
            hive_id = None
            if properties and hasattr(properties, 'headers') and properties.headers:
                if 'timestamp' in properties.headers:
                    timestamp = properties.headers['timestamp']
                    if isinstance(timestamp, bytes):
                        timestamp = timestamp.decode('utf-8')
                
                if 'HiveId' in properties.headers:
                    hive_id = properties.headers['HiveId']
                    if isinstance(hive_id, bytes):
                        hive_id = hive_id.decode('utf-8')
            
            if self.crop_polygon is None:
                if not self.load_crop_polygon(image):
                    print("Failed to set crop polygon - stopping processing")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                    return
            
            self.image_count += 1
            result = self.process_single_image(image, timestamp=timestamp, filename=filename)
            
            if result:
                self.results.append(result)
                
                if self.bee_database:
                    if hive_id:
                        self.bee_database.hive_id = hive_id
                    
                    self.bee_database.insert_detection_result(result)
                    
                    if hive_id:
                        self.bee_database.hive_id = None
                
            
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            print(f"Message processing error: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    

    def start_consuming(self):
        """Start listening for messages from RabbitMQ"""

        if not self.connect_to_rabbitmq():
            return False
        
        db_config = {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('MYSQL_PORT', '3306')),
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', ''),
            'database': os.getenv('MYSQL_DATABASE', 'bee_detection'),
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci'
        }
        self.bee_database = BeeDatabase(db_config, hive_id=None)
        
        if not self.crop_polygon:
            self.load_crop_polygon()
        
        try:
            self.channel.basic_qos(prefetch_count=1)
            
            self.channel.basic_consume(
                queue=self.config['queue_name'],
                on_message_callback=self.callback
            )
            
            self.is_running = True
            self.channel.start_consuming()
            
        except KeyboardInterrupt:
            self.stop_consuming()
        except Exception as e:
            print(f"Error during listening: {e}")
            return False
        
        return True
    
    
    def stop_consuming(self):
        """Stop listening and save results"""
        
        if self.channel and self.is_running:
            self.channel.stop_consuming()
        
        if self.bee_database:
            self.bee_database.close()
        
        if self.connection and not self.connection.is_closed:
            self.connection.close()
        
        self.is_running = False
        print("Processor stopped")
