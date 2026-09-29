"""
Cloud Sync Service

Synchronizes buffered data with cloud backend when connectivity is available.
"""

import asyncio
from typing import Dict, List
from loguru import logger
import httpx


class CloudSyncService:
    """
    Synchronizes local buffer with cloud backend
    """
    
    def __init__(self, settings, buffer_manager):
        self.settings = settings
        self.buffer = buffer_manager
        self.running = False
        self.connected = False
        self._sync_task = None
        self._http_client = None
    
    async def start(self):
        """Start the sync service"""
        self.running = True
        self._http_client = httpx.AsyncClient(
            base_url=self.settings.cloud_api_url,
            timeout=self.settings.cloud_connection_timeout
        )
        
        # Start background sync task
        self._sync_task = asyncio.create_task(self._sync_loop())
        logger.info("Cloud Sync Service started")
    
    async def stop(self):
        """Stop the sync service"""
        self.running = False
        if self._sync_task:
            self._sync_task.cancel()
        if self._http_client:
            await self._http_client.aclose()
        logger.info("Cloud Sync Service stopped")
    
    async def _sync_loop(self):
        """Background task to periodically sync data"""
        while self.running:
            try:
                await self._check_cloud_connection()
                
                if self.connected:
                    await self._sync_buffered_data()
                    await self.buffer.cleanup_old_data()
                
                await asyncio.sleep(self.settings.cloud_sync_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Sync loop error: {e}")
                await asyncio.sleep(5)
    
    async def _check_cloud_connection(self):
        """Check if cloud backend is reachable"""
        try:
            response = await self._http_client.get("/health", timeout=5.0)
            if response.status_code == 200:
                if not self.connected:
                    logger.info("✓ Cloud connection established")
                self.connected = True
            else:
                self.connected = False
        except Exception as e:
            if self.connected:
                logger.warning(f"Cloud connection lost: {e}")
            self.connected = False
    
    async def _sync_buffered_data(self):
        """Sync buffered data to cloud"""
        try:
            # Get unsynced data from buffer
            unsynced_data = await self.buffer.get_unsynced_data(
                limit=self.settings.buffer_sync_batch_size
            )
            
            if not unsynced_data:
                return
            
            logger.info(f"Syncing {len(unsynced_data)} records to cloud...")
            
            # Upload to cloud
            response = await self._http_client.post(
                "/api/v1/data/bulk_upload",
                json={"data": unsynced_data}
            )
            
            if response.status_code == 200:
                # Mark as synced
                record_ids = [record["id"] for record in unsynced_data]
                await self.buffer.mark_as_synced(record_ids)
                logger.info(f"✓ Synced {len(unsynced_data)} records")
            else:
                logger.error(f"Sync failed with status: {response.status_code}")
        
        except Exception as e:
            logger.error(f"Error syncing data: {e}")
    
    def is_connected(self) -> bool:
        """Check if connected to cloud"""
        return self.connected
    
    async def trigger_manual_sync(self) -> Dict:
        """Manually trigger a sync operation"""
        if not self.connected:
            return {"status": "error", "message": "Cloud not reachable"}
        
        try:
            await self._sync_buffered_data()
            return {"status": "success", "message": "Sync completed"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
