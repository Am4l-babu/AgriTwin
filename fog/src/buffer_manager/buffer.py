"""
Buffer Manager

Manages local data buffering using Redis and SQLite for offline operation.
"""

import asyncio
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from loguru import logger
import redis.asyncio as aioredis
from contextlib import asynccontextmanager


class BufferManager:
    """
    Hybrid buffer using Redis (hot) and SQLite (cold) storage
    """
    
    def __init__(self, settings):
        self.settings = settings
        self.redis_client: Optional[aioredis.Redis] = None
        self.sqlite_conn: Optional[sqlite3.Connection] = None
        
    async def initialize(self):
        """Initialize storage backends"""
        # Initialize Redis
        try:
            self.redis_client = await aioredis.from_url(
                f"redis://{self.settings.redis_host}:{self.settings.redis_port}/{self.settings.redis_db}",
                password=self.settings.redis_password if self.settings.redis_password else None,
                max_connections=self.settings.redis_max_connections,
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("✓ Redis connected")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Running without Redis.")
            self.redis_client = None
        
        # Initialize SQLite
        try:
            import os
            os.makedirs(os.path.dirname(self.settings.sqlite_db_path), exist_ok=True)
            
            self.sqlite_conn = sqlite3.connect(
                self.settings.sqlite_db_path,
                check_same_thread=False
            )
            self._create_tables()
            logger.info("✓ SQLite database initialized")
        except Exception as e:
            logger.error(f"SQLite initialization failed: {e}")
            raise
    
    def _create_tables(self):
        """Create SQLite tables"""
        cursor = self.sqlite_conn.cursor()
        
        # Sensor data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_id TEXT NOT NULL,
                sensor_type TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT,
                timestamp INTEGER NOT NULL,
                quality TEXT,
                synced INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Create indexes separately (SQLite syntax)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_farm_sensor ON sensor_data (farm_id, sensor_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON sensor_data (timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_synced ON sensor_data (synced)")
        
        # Status table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS device_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_id TEXT NOT NULL,
                device_id TEXT NOT NULL,
                data TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                synced INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Alerts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                farm_id TEXT NOT NULL,
                alert_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                synced INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.sqlite_conn.commit()
    
    async def store_sensor_data(self, farm_id: str, sensor_type: str, data: Dict[str, Any]):
        """Store sensor data in buffer"""
        try:
            # Store in Redis (hot buffer)
            if self.redis_client:
                key = f"sensor:{farm_id}:{sensor_type}:latest"
                await self.redis_client.setex(
                    key,
                    3600,  # 1 hour TTL
                    json.dumps(data)
                )
                
                # Add to time-series list
                list_key = f"sensor:{farm_id}:{sensor_type}:history"
                await self.redis_client.lpush(list_key, json.dumps(data))
                await self.redis_client.ltrim(list_key, 0, 99)  # Keep last 100
                await self.redis_client.expire(list_key, 3600)
            
            # Store in SQLite (cold buffer)
            cursor = self.sqlite_conn.cursor()
            cursor.execute("""
                INSERT INTO sensor_data (farm_id, sensor_type, value, unit, timestamp, quality)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                farm_id,
                sensor_type,
                data.get("value"),
                data.get("unit"),
                data.get("timestamp"),
                data.get("quality", "unknown")
            ))
            self.sqlite_conn.commit()
            
            logger.debug(f"Stored sensor data: {farm_id}/{sensor_type}")
            
        except Exception as e:
            logger.error(f"Error storing sensor data: {e}")
    
    async def store_status(self, farm_id: str, data: Dict[str, Any]):
        """Store device status"""
        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute("""
                INSERT INTO device_status (farm_id, device_id, data, timestamp)
                VALUES (?, ?, ?, ?)
            """, (
                farm_id,
                data.get("device_id"),
                json.dumps(data),
                data.get("timestamp")
            ))
            self.sqlite_conn.commit()
            
        except Exception as e:
            logger.error(f"Error storing status: {e}")
    
    async def store_alert(self, farm_id: str, data: Dict[str, Any]):
        """Store alert"""
        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute("""
                INSERT INTO alerts (farm_id, alert_type, severity, message, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (
                farm_id,
                data.get("alert_type"),
                data.get("severity"),
                data.get("message"),
                data.get("timestamp")
            ))
            self.sqlite_conn.commit()
            
        except Exception as e:
            logger.error(f"Error storing alert: {e}")
    
    async def get_unsynced_data(self, limit: int = 100) -> List[Dict]:
        """Get unsynced data for cloud upload"""
        try:
            cursor = self.sqlite_conn.cursor()
            cursor.execute("""
                SELECT id, farm_id, sensor_type, value, unit, timestamp, quality
                FROM sensor_data
                WHERE synced = 0
                ORDER BY timestamp ASC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            data = []
            for row in rows:
                data.append({
                    "id": row[0],
                    "farm_id": row[1],
                    "sensor_type": row[2],
                    "value": row[3],
                    "unit": row[4],
                    "timestamp": row[5],
                    "quality": row[6]
                })
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching unsynced data: {e}")
            return []
    
    async def mark_as_synced(self, record_ids: List[int]):
        """Mark records as synced"""
        try:
            cursor = self.sqlite_conn.cursor()
            placeholders = ','.join('?' * len(record_ids))
            cursor.execute(f"""
                UPDATE sensor_data
                SET synced = 1
                WHERE id IN ({placeholders})
            """, record_ids)
            self.sqlite_conn.commit()
            
        except Exception as e:
            logger.error(f"Error marking as synced: {e}")
    
    async def cleanup_old_data(self):
        """Remove old synced data"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.settings.buffer_retention_days)
            cursor = self.sqlite_conn.cursor()
            
            cursor.execute("""
                DELETE FROM sensor_data
                WHERE synced = 1 AND created_at < ?
            """, (cutoff_date,))
            
            deleted = cursor.rowcount
            self.sqlite_conn.commit()
            
            if deleted > 0:
                logger.info(f"Cleaned up {deleted} old records")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    def is_healthy(self) -> bool:
        """Check if buffer is healthy"""
        try:
            # Check SQLite
            if not self.sqlite_conn:
                return False
            
            cursor = self.sqlite_conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sensor_data")
            
            # Check Redis (optional)
            # if self.redis_client:
            #     asyncio.create_task(self.redis_client.ping())
            
            return True
            
        except Exception:
            return False
    
    async def close(self):
        """Close connections"""
        if self.redis_client:
            await self.redis_client.close()
        if self.sqlite_conn:
            self.sqlite_conn.close()
