import sqlite3
import os
from datetime import datetime
from pathlib import Path
import uuid


class BeeDatabase:
    """Manages SQLite database for bee detection results."""
    
    def __init__(self, db_path="bee_detection.db", hive_id=None):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
            hive_id: Unique identifier for this hive (auto-generated if None)
        """
        self.db_path = Path(db_path)
        self.connection = None
        # Initialize database first
        self._initialize_database()
        self.hive_id = hive_id or self._generate_hive_id()
        print(f"🗃️ Database: {self.db_path}")
        print(f"🏠 Hive ID: {self.hive_id}")
    
    def _generate_hive_id(self):
        """Generate unique hive ID."""
        import socket
        hostname = socket.gethostname()
        timestamp = datetime.now().strftime("%Y%m%d")
        return f"HIVE_{hostname}_{timestamp}"[:32]
    
    def _initialize_database(self):
        """Create database and tables if they don't exist."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.execute("PRAGMA foreign_keys = ON")  # Enable foreign keys

            # Create tables
            self._create_tables()
                        
        except Exception as e:
            print(f"❌ Database initialization error: {e}")
            raise
    
    
    def _create_tables(self):
        """Create necessary tables."""
        cursor = self.connection.cursor()
        
        # Bee detection results table - ULTRA PROSTA
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bee_detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hive_id TEXT NOT NULL,
                filename TEXT,
                timestamp TIMESTAMP,
                bee_coverage REAL
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bee_detections_hive_timestamp 
            ON bee_detections (hive_id, timestamp)
        """)
        
        self.connection.commit()
        
    
    def insert_detection_result(self, result_data):
        """
        Insert bee detection result into database.
        
        Args:
            result_data: Dict with detection results from bee_detector
        """
        try:
            cursor = self.connection.cursor()
            
            # Parse timestamp bez mikrosekund
            timestamp_str = result_data.get('timestamp', datetime.now().isoformat())
            if isinstance(timestamp_str, str):
                if 'T' in timestamp_str:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                else:
                    timestamp = datetime.fromisoformat(timestamp_str)
            else:
                timestamp = datetime.now()
            
            # Usuń mikrosekundy - tylko sekundy!
            timestamp = timestamp.replace(microsecond=0)
            
            # Insert detection result - TYLKO 5 kolumn!
            cursor.execute("""
                INSERT INTO bee_detections (
                    hive_id, filename, timestamp, bee_coverage
                ) VALUES (?, ?, ?, ?)
            """, (
                self.hive_id,
                result_data.get('filename', 'unknown.jpg'),
                timestamp,
                result_data.get('bee_percentage', 0.0)
            ))
            
            self.connection.commit()
            
            cursor.execute("SELECT last_insert_rowid()")
            record_id = cursor.fetchone()[0]
            
            print(f"💾 Saved to DB: ID {record_id} - {result_data.get('bee_percentage', 0):.2f}% coverage")
            return record_id
            
        except Exception as e:
            print(f"❌ Database insert error: {e}")
            return None
    
    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            print("🗃️ Database connection closed")
