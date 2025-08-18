import sqlite3
import os
from datetime import datetime
from pathlib import Path
import sqlite3
import uuid


class BeeDatabase:
    """Manages SQLite database for bee detection results."""
    
    def __init__(self, db_path="bee_detection.db", hive_id=None):
        """Initialize database connection"""

        self.db_path = Path(db_path)
        self.connection = None
        self.hive_id = hive_id
        self._initialize_database()
        print(f"🗃️ Database: {self.db_path}")
    
    def _set_hive_id(self, filename):
        """Set hive_id from the last character of the first photo"""

        if self.hive_id is None: 
            name_without_ext = Path(filename).stem
            last_char = name_without_ext[-1] if name_without_ext else "X"
            self.hive_id = f"HIVE_{last_char}"
    
    def _initialize_database(self):
        """Create database and tables if they don't exist"""

        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.execute("PRAGMA foreign_keys = ON")  # Enable foreign keys
            self._create_tables()
                        
        except Exception as e:
            print(f"Database initialization error: {e}")
            raise
    
    
    def _create_tables(self):
        """Create necessary tables"""

        cursor = self.connection.cursor()
        cursor.execute("""
                        CREATE TABLE IF NOT EXISTS bee_detections (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            hive_id TEXT NOT NULL,
                            filename TEXT,
                            timestamp TIMESTAMP,
                            bee_coverage REAL)
                       """
                       )
        cursor.execute("""
                        CREATE INDEX IF NOT EXISTS idx_bee_detections_hive_timestamp 
                        ON bee_detections (hive_id, timestamp)
                        """)
        
        self.connection.commit()
        
    
    def insert_detection_result(self, result_data):
        """Insert bee detection result into database"""
        
        try:
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
                                (?, ?, ?, ?)
                           """, 
                           (
                self.hive_id,
                filename,
                timestamp,
                result_data.get('bee_percentage', 0.0)
                )
            )
            
            self.connection.commit()            
        except Exception as e:
            print(f"Database insert error: {e}")
    
    def close(self):
        if self.connection:
            self.connection.close()
            print("Database connection closed")
