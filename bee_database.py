import mysql.connector
from mysql.connector import Error
import os
from datetime import datetime
from pathlib import Path


class BeeDatabase:
    """Manages MySQL database for bee detection results"""
    
    def __init__(self, db_config=None, hive_id=None):
        """Initialize database connection with MySQL configuration"""

        self.db_config = db_config or {
            'host': os.getenv('MYSQL_HOST', 'localhost'),
            'port': int(os.getenv('MYSQL_PORT', '3306')),
            'user': os.getenv('MYSQL_USER', 'root'),
            'password': os.getenv('MYSQL_PASSWORD', ''),
            'database': os.getenv('MYSQL_DATABASE', 'bee_detection'),
            'charset': 'utf8mb4',
            'collation': 'utf8mb4_unicode_ci',
            'autocommit': False,
            'pool_name': 'bee_pool',
            'pool_size': 5,
            'pool_reset_session': True,
            'connect_timeout': 10,
            'use_pure': True
        }
        if db_config:
            self.db_config.update(db_config)
            
        self.connection = None
        self.hive_id = hive_id
        self._initialize_database()
    
    def _set_hive_id(self, filename):
        """Set hive_id from the part before the first underscore"""

        if self.hive_id is None: 
            name_without_ext = Path(filename).stem
            prefix = name_without_ext.split('_')[0] if '_' in name_without_ext else name_without_ext
            self.hive_id = f"HIVE_{prefix}"
    
    def _initialize_database(self):
        """Create database connection and tables if they don't exist"""

        try:
            self.connection = mysql.connector.connect(**self.db_config)
            
            if self.connection.is_connected():
                self._create_tables()
            else:
                raise Exception("Failed to connect to MySQL database")
                        
        except Error as e:
            print("Make sure MySQL is running and credentials are correct:")
            print(f"Host: {self.db_config['host']}:{self.db_config['port']}")
            print(f"Database: {self.db_config['database']}")
            print(f"User: {self.db_config['user']}")
            raise
    
    
    def _create_tables(self):
        """Create necessary tables"""

        cursor = self.connection.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.db_config['database']} "
                      f"CHARACTER SET {self.db_config['charset']} "
                      f"COLLATE {self.db_config['collation']}")
        
        cursor.execute(f"USE {self.db_config['database']}")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bee_detections (
                id INT AUTO_INCREMENT PRIMARY KEY,
                hive_id VARCHAR(50) NOT NULL,
                filename VARCHAR(255),
                timestamp DATETIME,
                bee_coverage DECIMAL(10, 6),
                INDEX idx_hive_timestamp (hive_id, timestamp)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        self.connection.commit()
    
    def _ensure_connection(self):
        """Ensure database connection is alive, reconnect if necessary"""
        try:
            if self.connection is None or not self.connection.is_connected():
                print("Database connection lost, reconnecting...")
                self.connection = mysql.connector.connect(**self.db_config)
                if self.connection.is_connected():
                    print("Database reconnected successfully")
                    cursor = self.connection.cursor()
                    cursor.execute(f"USE {self.db_config['database']}")
                    cursor.close()
                else:
                    raise Exception("Failed to reconnect to MySQL database")
            else:
                self.connection.ping(reconnect=True)
        except Error as e:
            print(f"Error ensuring database connection: {e}")
            try:
                self.connection = mysql.connector.connect(**self.db_config)
                if self.connection.is_connected():
                    print("Database reconnected after error")
                    cursor = self.connection.cursor()
                    cursor.execute(f"USE {self.db_config['database']}")
                    cursor.close()
            except Error as reconnect_error:
                print(f"Failed to reconnect: {reconnect_error}")
                raise
        
    
    def insert_detection_result(self, result_data):
        """Insert bee detection result into database
        
        Returns:
            bool: True if insert successful, False otherwise
        """
        print(f"Inserting detection result into database: {result_data}")
        
        try:
            self._ensure_connection()
            
            filename = result_data.get('filename', 'unknown.jpg')
            self._set_hive_id(filename)
            cursor = self.connection.cursor()
            
            timestamp_str = result_data.get('timestamp', datetime.now().isoformat())
            if isinstance(timestamp_str, str):
                if 'T' in timestamp_str:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                else:
                    timestamp = datetime.fromisoformat(timestamp_str)
            else:
                timestamp = datetime.now()
            
            timestamp = timestamp.replace(microsecond=0)
            
            cursor.execute("""
                INSERT INTO bee_detections 
                    (hive_id, filename, timestamp, bee_coverage) 
                VALUES 
                    (%s, %s, %s, %s)
            """, 
            (
                self.hive_id,
                filename,
                timestamp,
                result_data.get('bee_percentage', 0.0)
            ))
            
            self.connection.commit()
            print(f"Saved detection result: {filename} - {result_data.get('bee_percentage', 0.0):.2f}%")
            return True
            
        except Error as e:
            print(f"Database insert error: {e}")
            try:
                print("Attempting to reconnect and retry insert...")
                self._ensure_connection()
                
                cursor = self.connection.cursor()
                cursor.execute("""
                    INSERT INTO bee_detections 
                        (hive_id, filename, timestamp, bee_coverage) 
                    VALUES 
                        (%s, %s, %s, %s)
                """, 
                (
                    self.hive_id,
                    filename,
                    timestamp,
                    result_data.get('bee_percentage', 0.0)
                ))
                self.connection.commit()
                print(f"Retry successful: {filename}")
                return True
            except Exception as retry_error:
                print(f"Retry failed: {retry_error}")
                if self.connection:
                    self.connection.rollback()
                return False
        except Exception as e:
            print(f"Unexpected database error: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def close(self):
        """Close database connection"""
        try:
            if self.connection and self.connection.is_connected():
                self.connection.close()
                print("Database connection closed")
        except Exception as e:
            print(f"Error closing database connection: {e}")
