import pika
import json
import cv2
import numpy as np
import base64
import pickle
from datetime import datetime
from pathlib import Path
from collections import deque
import threading
import time

from manual_cropper import ManualCropper
from image_processor import ImageProcessor
from bee_detector import BeeDetector
from bee_database import BeeDatabase
from rabbitmq_config import RABBITMQ_CONFIG, PROCESSING_CONFIG, DETECTION_CONFIG


class RabbitMQBeeProcessor:
    """Przetwarza zdjęcia pszczół z RabbitMQ kolejki w czasie rzeczywistym."""
    
    def __init__(self, rabbit_config=None):
        """
        Inicjalizacja processora.
        
        Args:
            rabbit_config: Dict z konfiguracją RabbitMQ (host, port, username, password, queue_name)
        """
        self.config = rabbit_config or RABBITMQ_CONFIG
        self.processing_config = PROCESSING_CONFIG
        
        # Stan przetwarzania
        self.crop_polygon = None
        self.image_processor = None
        self.bee_detector = None
        self.bee_database = None  # Database instance
        self.image_buffer = deque(maxlen=self.processing_config['background_size'])
        self.results = []
        self.image_count = 0
        self.is_running = False
        self.connection = None
        self.channel = None
        
        # Przygotuj katalog wyjściowy
        self.output_dir = Path(self.processing_config['output_dir'])
        if self.output_dir.exists():
            import shutil
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        print("🐰 RabbitMQ Bee Processor initialized")
        
    def load_crop_polygon(self, first_image=None):
        """
        Załaduj lub stwórz crop polygon.
        
        Args:
            first_image: Pierwsze zdjęcie do manualnego cropowania (jako array)
        """
        polygon_file = self.processing_config['crop_polygon_file']
        
        try:
            with open(polygon_file, "rb") as f:
                self.crop_polygon = pickle.load(f)
            print(f"✅ Załadowano polygon z pliku: {len(self.crop_polygon)} punktów")
        except FileNotFoundError:
            if first_image is not None:
                print("🖼️ Pierwszy obraz - definiowanie obszaru cropowania...")
                # Zapisz pierwsze zdjęcie tymczasowo
                temp_path = "temp_first_image.jpg"
                cv2.imwrite(temp_path, first_image)
                
                # Manualny crop
                cropper = ManualCropper()
                self.crop_polygon = cropper.get_crop_polygon(temp_path)
                
                if self.crop_polygon:
                    # Zapisz polygon do pliku
                    with open(polygon_file, "wb") as f:
                        pickle.dump(self.crop_polygon, f)
                    print(f"✅ Polygon zapisany: {self.crop_polygon}")
                    
                    # Usuń tymczasowy plik
                    Path(temp_path).unlink()
                else:
                    print("❌ Nie udało się zdefiniować polygon!")
                    return False
            else:
                print("❌ Brak pliku polygon i pierwszego zdjęcia!")
                return False
        
        # Inicjalizuj image processor
        if self.crop_polygon:
            self.image_processor = ImageProcessor(self.crop_polygon)
            print(f"✅ Image processor zainicjalizowany (polygon area: {self.image_processor.polygon_area} px)")
            return True
        return False
    
    def connect_to_rabbitmq(self):
        """Nawiąż połączenie z RabbitMQ."""
        try:
            # Stwórz credentials
            credentials = pika.PlainCredentials(
                self.config['username'], 
                self.config['password']
            )
            
            # Stwórz connection parameters
            parameters = pika.ConnectionParameters(
                host=self.config['host'],
                port=self.config['port'],
                credentials=credentials
            )
            
            # Nawiąż połączenie
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Zadeklaruj kolejkę (upewnij się, że istnieje)
            self.channel.queue_declare(queue=self.config['queue_name'], durable=True)
            
            print(f"✅ Połączono z RabbitMQ: {self.config['host']}:{self.config['port']}")
            print(f"📡 Nasłuchiwanie kolejki: {self.config['queue_name']}")
            return True
            
        except Exception as e:
            print(f"❌ Błąd połączenia z RabbitMQ: {e}")
            return False
    
    def decode_image_from_message(self, body, properties=None):
        """
        Dekoduj obraz z wiadomości RabbitMQ.
        
        Args:
            body: Treść wiadomości z RabbitMQ (raw bytes image data)
            properties: Message properties (mogą zawierać filename)
            
        Returns:
            tuple: (numpy.ndarray, filename) - Obraz jako array OpenCV i nazwa pliku lub (None, None)
        """
        try:
            filename = "unknown.jpg"  # Domyślna nazwa
            
            # Sprawdź czy filename jest w properties
            if properties and hasattr(properties, 'headers') and properties.headers:
                if 'filename' in properties.headers:
                    filename = properties.headers['filename']
                    if isinstance(filename, bytes):
                        filename = filename.decode('utf-8')
                    print(f"📁 Nazwa pliku z headers: {filename}")
            
            # Nowy format: body to raw bytes image data
            image_data = body
            
            # Próba alternatywna: sprawdź czy to JSON (dla kompatybilności wstecznej)
            if len(body) > 0 and body[0:1] == b'{':
                try:
                    message = json.loads(body.decode('utf-8'))
                    if 'image' in message:
                        # Base64 encoded image (stary format)
                        image_data = base64.b64decode(message['image'])
                        if 'filename' in message:
                            filename = message['filename']
                        print("📊 Stary format JSON wykryty")
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass  # Kontynuuj z raw bytes
            
            # Dekoduj obraz z raw bytes
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                print("⚠️ Nie udało się zdekodować obrazu")
                return None, None
                
            print(f"✅ Zdekodowano obraz: {image.shape}, plik: {filename}")
            return image, filename
            
        except Exception as e:
            print(f"❌ Błąd dekodowania obrazu: {e}")
            return None, None
    
    def create_background_from_buffer(self):
        """Stwórz obraz tła z aktualnego buffera zdjęć."""
        if len(self.image_buffer) < 5:  # Minimum 5 zdjęć
            print("⚠️ Za mało zdjęć w bufferze do tworzenia tła")
            return None
            
        print(f"🌅 Tworzenie tła z {len(self.image_buffer)} zdjęć...")
        
        # Konwertuj buffer do formatu wymaganego przez create_background
        background_images = []
        for img in self.image_buffer:
            background_images.append({
                'image': img,
                'mask': None  # Mask zostanie utworzona w image_processor
            })
        
        background = self.image_processor.create_background(background_images)
        if background is not None:
            print("✅ Tło utworzone pomyślnie")
            # Zapisz tło
            bg_path = self.output_dir / f"background_{self.image_count}.jpg"
            cv2.imwrite(str(bg_path), background)
        
        return background
    
    def process_single_image(self, image, timestamp=None, filename=None):
        """
        Przetwórz pojedyncze zdjęcie.
        
        Args:
            image: Obraz jako numpy array
            timestamp: Znacznik czasu (opcjonalny)
            filename: Nazwa pliku z API (opcjonalna)
            
        Returns:
            dict: Wyniki detekcji lub None
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        # Użyj filename z API lub stwórz własny
        if filename is None:
            filename = f"image_{self.image_count:06d}_{timestamp.replace(':', '_')}.jpg"
        else:
            # Sanityzuj filename z API
            import re
            filename = re.sub(r'[^\w\-_\.]', '_', filename)
            if not filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                filename = f"{filename}.jpg"
        
        print(f"🔄 Przetwarzanie obrazu {self.image_count}: {filename}")
        
        # Crop image
        cropped_img, crop_mask = self.image_processor.crop_image_array(image)
        if cropped_img is None:
            print("❌ Nie udało się ściąć obrazu")
            return None
        
        # Zapisz cropped image
        if self.processing_config['save_intermediate']:
            cropped_path = self.output_dir / f"cropped_{filename}"
            cv2.imwrite(str(cropped_path), cropped_img)
        
        # Dodaj do buffera
        self.image_buffer.append(cropped_img)
        
        # Sprawdź czy można utworzyć/zaktualizować tło
        if self.bee_detector is None:
            # Pierwsze tło - czekamy na wystarczającą liczbę zdjęć
            if len(self.image_buffer) >= self.processing_config['background_size']:
                background = self.create_background_from_buffer()
                if background is not None:
                    self.bee_detector = BeeDetector(background, self.image_processor.polygon_area)
                    print("🐝 BeeDetector zainicjalizowany z pierwszym tłem")
                else:
                    print("❌ Nie udało się utworzyć pierwszego tła")
                    return None
            else:
                print(f"⏳ Czekanie na więcej zdjęć do tła ({len(self.image_buffer)}/{self.processing_config['background_size']})")
                return None
        else:
            # Aktualizuj tło co określoną liczbę zdjęć
            if (self.image_count % self.processing_config['background_update_frequency'] == 0 and 
                len(self.image_buffer) >= self.processing_config['background_size']):
                
                background = self.create_background_from_buffer()
                if background is not None:
                    self.bee_detector.update_background(background)
                    print(f"🔄 Tło zaktualizowane (zdjęcie {self.image_count})")
        
        # Jeśli mamy detector, rób detekcję
        if self.bee_detector is not None:
            result = self.bee_detector.analyze_image(cropped_img, filename)
            if result:
                result['original_timestamp'] = timestamp
                result['timestamp'] = timestamp  # For database compatibility
                result['filename'] = filename    # Add filename to result
                result['image_count'] = self.image_count
                result['total_area'] = self.image_processor.polygon_area
                result['bee_area'] = int(result['bee_percentage'] * self.image_processor.polygon_area / 100)
                result['background_updated'] = (self.image_count % self.processing_config['background_update_frequency'] == 0)
                
                # Zapisz wyniki wizualizacji
                if self.processing_config['save_intermediate']:
                    # Bee mask
                    mask_path = self.output_dir / f"bee_mask_{filename}"
                    cv2.imwrite(str(mask_path), result['bee_mask'])
                    
                    # Visualization
                    vis = self.bee_detector.create_visualization(cropped_img, result['bee_mask'], [])
                    vis_path = self.output_dir / f"visualization_{filename}"
                    cv2.imwrite(str(vis_path), vis)
                
                print(f"  ✅ {filename}: {result['bee_percentage']:.2f}% bee coverage "
                      f"({result['num_bee_contours']} contours, {result['detection_method']})")
                
                return result
        
        return None
    
    
    def callback(self, ch, method, properties, body):
        """
        Callback wywoływany przy otrzymaniu wiadomości z RabbitMQ.
        
        Args:
            ch: Channel
            method: Method frame
            properties: Properties (zawierają filename w headers)
            body: Message body (raw image bytes)
        """
        try:
            print(f"\n📨 Otrzymano wiadomość z RabbitMQ (rozmiar: {len(body)} bajtów)")
            
            # Dekoduj obraz (nowy format z filename w properties)
            image, filename = self.decode_image_from_message(body, properties)
            if image is None:
                print("❌ Nie udało się zdekodować obrazu - pomijam")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return
            
            # Pierwszy obraz - ustaw crop polygon
            if self.crop_polygon is None:
                if not self.load_crop_polygon(image):
                    print("❌ Nie udało się ustawić crop polygon - zatrzymuję przetwarzanie")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                    return
            
            # Przetwórz obraz
            self.image_count += 1
            result = self.process_single_image(image, filename=filename)
            
            if result:
                self.results.append(result)
                
                # Zapisz do bazy danych
                if self.bee_database:
                    self.bee_database.insert_detection_result(result)
                
            
            # Potwierdź przetworzenie wiadomości
            ch.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            print(f"❌ Błąd przetwarzania wiadomości: {e}")
            # Odrzuć wiadomość
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    def start_consuming(self):
        """Rozpocznij nasłuchiwanie wiadomości z RabbitMQ."""
        if not self.connect_to_rabbitmq():
            return False
        
        # Inicjalizuj bazę danych
        db_path = self.processing_config.get('database_path', 'bee_detection.db')
        hive_id = self.processing_config.get('hive_id', None)
        self.bee_database = BeeDatabase(db_path, hive_id)
        
        # Załaduj polygon jeśli już istnieje
        if not self.crop_polygon:
            self.load_crop_polygon()
        
        print("🚀 Rozpoczynam nasłuchiwanie RabbitMQ...")
        
        try:
            # Ustaw QoS - przetwarzaj po jednej wiadomości na raz
            self.channel.basic_qos(prefetch_count=1)
            
            # Rozpocznij konsumpcję
            self.channel.basic_consume(
                queue=self.config['queue_name'],
                on_message_callback=self.callback
            )
            
            self.is_running = True
            self.channel.start_consuming()
            
        except KeyboardInterrupt:
            print("\n🛑 Zatrzymywanie przez użytkownika...")
            self.stop_consuming()
        except Exception as e:
            print(f"❌ Błąd podczas nasłuchiwania: {e}")
            return False
        
        return True
    
    def stop_consuming(self):
        """Zatrzymaj nasłuchiwanie i zapisz wyniki."""
        print("🛑 Zatrzymywanie nasłuchiwania...")
        
        if self.channel and self.is_running:
            self.channel.stop_consuming()
        
        
        # Zamknij bazę danych
        if self.bee_database:
            self.bee_database.close()
        
        if self.connection and not self.connection.is_closed:
            self.connection.close()
        
        self.is_running = False
        print("✅ Processor zatrzymany")
