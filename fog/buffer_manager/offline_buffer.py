"""
Offline Buffer Manager - Fog Layer Data Persistence

Handles data buffering when cloud backend is unavailable.
Implements two-tier storage:
- Hot buffer: Redis (last 1 hour, fast access)
- Cold buffer: SQLite (last 7 days, persistence)
"""

import logging
import json
import sqlite3
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)


class OfflineBuffer:
    """
    Two-tier offline buffer for sensor data
    
    Hot tier (Redis): Recent data (configurable, default 1 hour)
    Cold tier (SQLite): Historical data (configurable, default 7 days)
    """
    
    def __init__(self, redis_client=None, sqlite_path: str = "data/offline_buffer.db",
                 hot_buffer_hours: int = 1, cold_buffer_days: int = 7):
        """
        Args:
            redis_client: Redis client for hot buffer
            sqlite_path: Path to SQLite database
            hot_buffer_hours: Hours to keep in hot buffer
            cold_buffer_days: Days to keep in cold buffer
        """
        self.redis = redis_client
        self.sqlite_path = Path(sqlite_path)
        self.hot_buffer_hours = hot_buffer_hours
        self.cold_buffer_days = cold_buffer_days
        
        # Ensure database directory exists
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize SQLite database
        self._init_sqlite()
        
        logger.info(
            f"✓ Offline buffer initialized "
            f"(hot: {hot_buffer_hours}h, cold: {cold_buffer_days}d)"
        )
    
    def _init_sqlite(self):
        """Initialize SQLite database schema"""
        conn = sqlite3.connect(str(self.sqlite_path))
        cursor = conn.cursor()
        
        # Sensor data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                farm_id TEXT NOT NULL,
                sensor_type TEXT NOT NULL,
                sensor_id TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT,
                metadata TEXT,
                synced INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON sensor_data(timestamp)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_farm_sensor 
            ON sensor_data(farm_id, sensor_type)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_synced 
            ON sensor_data(synced)
        """)
        
        conn.commit()
        conn.close()
        
        logger.info(f"✓ SQLite database initialized: {self.sqlite_path}")
    
    async def store(self, sensor_data: Dict[str, Any]):
        """
        Store sensor data in buffer
        
        Args:
            sensor_data: Sensor reading dictionary
        """
        try:
            # Extract fields
            timestamp = sensor_data.get('timestamp', datetime.now().isoformat())
            farm_id = sensor_data.get('farm_id', 'unknown')
            sensor_type = sensor_data.get('sensor_type', 'unknown')
            sensor_id = sensor_data.get('sensor_id', 'unknown')
            value = sensor_data.get('value', 0)
            unit = sensor_data.get('unit', '')
            
            # Store metadata as JSON
            metadata = json.dumps({
                k: v for k, v in sensor_data.items() 
                if k not in ['timestamp', 'farm_id', 'sensor_type', 'sensor_id', 'value', 'unit']
            })
            
            # Store in hot buffer (Redis)
            if self.redis:
                await self._store_hot(farm_id, sensor_type, sensor_id, sensor_data)
            
            # Store in cold buffer (SQLite)
            await self._store_cold(timestamp, farm_id, sensor_type, sensor_id, 
                                   value, unit, metadata)
            
        except Exception as e:
            logger.error(f"Error storing sensor data in buffer: {e}")
    
    async def _store_hot(self, farm_id: str, sensor_type: str, 
                        sensor_id: str, data: Dict[str, Any]):
        """Store in Redis hot buffer"""
        try:
            # Key format: sensor:{farm_id}:{sensor_type}:{sensor_id}
            key = f"sensor:{farm_id}:{sensor_type}:{sensor_id}"
            
            # Store as JSON
            await asyncio.to_thread(
                self.redis.setex,
                key,
                self.hot_buffer_hours * 3600,
                json.dumps(data)
            )
            
            # Also add to time-series list
            list_key = f"timeseries:{farm_id}:{sensor_type}"
            await asyncio.to_thread(
                self.redis.lpush,
                list_key,
                json.dumps(data)
            )
            
            # Trim list to keep only recent data
            await asyncio.to_thread(
                self.redis.ltrim,
                list_key,
                0,
                999  # Keep last 1000 readings
            )
            
        except Exception as e:
            logger.error(f"Error storing in Redis: {e}")
    
    async def _store_cold(self, timestamp: str, farm_id: str, 
                         sensor_type: str, sensor_id: str,
                         value: float, unit: str, metadata: str):
        """Store in SQLite cold buffer"""
        try:
            conn = sqlite3.connect(str(self.sqlite_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO sensor_data 
                (timestamp, farm_id, sensor_type, sensor_id, value, unit, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (timestamp, farm_id, sensor_type, sensor_id, value, unit, metadata))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing in SQLite: {e}")
    
    async def get_recent(self, farm_id: str, sensor_type: str, 
                        limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent sensor data (from hot buffer if available)
        
        Args:
            farm_id: Farm identifier
            sensor_type: Sensor type (soil_moisture, temperature, etc.)
            limit: Maximum number of records
            
        Returns:
            List of sensor readings
        """
        # Try hot buffer first
        if self.redis:
            try:
                list_key = f"timeseries:{farm_id}:{sensor_type}"
                data_json = await asyncio.to_thread(
                    self.redis.lrange,
                    list_key,
                    0,
                    limit - 1
                )
                
                if data_json:
                    return [json.loads(d) for d in data_json]
            except Exception as e:
                logger.error(f"Error reading from Redis: {e}")
        
        # Fallback to cold buffer
        return await self._get_recent_cold(farm_id, sensor_type, limit)
    
    async def _get_recent_cold(self, farm_id: str, sensor_type: str, 
                              limit: int) -> List[Dict[str, Any]]:
        """Get recent data from SQLite"""
        try:
            conn = sqlite3.connect(str(self.sqlite_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT timestamp, farm_id, sensor_type, sensor_id, 
                       value, unit, metadata
                FROM sensor_data
                WHERE farm_id = ? AND sensor_type = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (farm_id, sensor_type, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Convert to dictionaries
            results = []
            for row in rows:
                data = {
                    'timestamp': row[0],
                    'farm_id': row[1],
                    'sensor_type': row[2],
                    'sensor_id': row[3],
                    'value': row[4],
                    'unit': row[5]
                }
                
                # Merge metadata
                if row[6]:
                    metadata = json.loads(row[6])
                    data.update(metadata)
                
                results.append(data)
            
            return results
            
        except Exception as e:
            logger.error(f"Error reading from SQLite: {e}")
            return []
    
    async def get_unsynced(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Get data that hasn't been synced to cloud
        
        Args:
            limit: Maximum number of records
            
        Returns:
            List of unsynced sensor readings
        """
        try:
            conn = sqlite3.connect(str(self.sqlite_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, timestamp, farm_id, sensor_type, sensor_id, 
                       value, unit, metadata
                FROM sensor_data
                WHERE synced = 0
                ORDER BY timestamp ASC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            results = []
            for row in rows:
                data = {
                    '_db_id': row[0],
                    'timestamp': row[1],
                    'farm_id': row[2],
                    'sensor_type': row[3],
                    'sensor_id': row[4],
                    'value': row[5],
                    'unit': row[6]
                }
                
                if row[7]:
                    metadata = json.loads(row[7])
                    data.update(metadata)
                
                results.append(data)
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting unsynced data: {e}")
            return []
    
    async def mark_synced(self, db_ids: List[int]):
        """
        Mark records as synced to cloud
        
        Args:
            db_ids: List of database IDs to mark as synced
        """
        try:
            conn = sqlite3.connect(str(self.sqlite_path))
            cursor = conn.cursor()
            
            placeholders = ','.join('?' * len(db_ids))
            cursor.execute(f"""
                UPDATE sensor_data
                SET synced = 1
                WHERE id IN ({placeholders})
            """, db_ids)
            
            conn.commit()
            conn.close()
            
            logger.info(f"✓ Marked {len(db_ids)} records as synced")
            
        except Exception as e:
            logger.error(f"Error marking records as synced: {e}")
    
    async def cleanup_old_data(self):
        """Remove data older than cold_buffer_days"""
        try:
            cutoff = datetime.now() - timedelta(days=self.cold_buffer_days)
            cutoff_str = cutoff.isoformat()
            
            conn = sqlite3.connect(str(self.sqlite_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM sensor_data
                WHERE timestamp < ? AND synced = 1
            """, (cutoff_str,))
            
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            
            if deleted > 0:
                logger.info(f"✓ Cleaned up {deleted} old records")
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get buffer statistics"""
        try:
            conn = sqlite3.connect(str(self.sqlite_path))
            cursor = conn.cursor()
            
            # Total records
            cursor.execute("SELECT COUNT(*) FROM sensor_data")
            total = cursor.fetchone()[0]
            
            # Unsynced records
            cursor.execute("SELECT COUNT(*) FROM sensor_data WHERE synced = 0")
            unsynced = cursor.fetchone()[0]
            
            # Oldest record
            cursor.execute("SELECT MIN(timestamp) FROM sensor_data")
            oldest = cursor.fetchone()[0]
            
            # Newest record
            cursor.execute("SELECT MAX(timestamp) FROM sensor_data")
            newest = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_records': total,
                'unsynced_records': unsynced,
                'synced_records': total - unsynced,
                'oldest_record': oldest,
                'newest_record': newest,
                'database_path': str(self.sqlite_path),
                'database_size_mb': self.sqlite_path.stat().st_size / (1024 * 1024)
                    if self.sqlite_path.exists() else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting buffer stats: {e}")
            return {}
