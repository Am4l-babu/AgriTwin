"""
Fog Gateway - Main Entry Point

Starts all services:
- FastAPI server
- MQTT ingestion service
- Buffer manager
- Cloud sync service
- Emergency control service
"""

import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from src.config.settings import get_settings
from src.ingestion.mqtt_client import MQTTIngestionService
from src.preprocessing.validator import DataValidator
from src.buffer_manager.buffer import BufferManager
from src.emergency_control.controller import EmergencyController
from src.cloud_sync.sync_service import CloudSyncService
from src.api.routes import router
from src.adaptive_sensing.thompson_sampler import AdaptiveSamplingTS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Global service instances
mqtt_service = None
buffer_manager = None
emergency_controller = None
cloud_sync_service = None

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifespan
    """
    global mqtt_service, buffer_manager, emergency_controller, cloud_sync_service
    
    logger.info("=" * 60)
    logger.info("Starting Fog Gateway Services")
    logger.info(f"Farm ID: {settings.farm_id}")
    logger.info(f"Device ID: {settings.device_id}")
    logger.info("=" * 60)
    
    try:
        # Initialize buffer manager
        logger.info("Initializing Buffer Manager...")
        buffer_manager = BufferManager(settings)
        await buffer_manager.initialize()
        
        # Initialize data validator
        logger.info("Initializing Data Validator...")
        validator = DataValidator(settings)
        
        # Initialize emergency controller
        logger.info("Initializing Emergency Controller...")
        emergency_controller = EmergencyController(settings, buffer_manager)
        await emergency_controller.start()
        
        # Initialize cloud sync service
        logger.info("Initializing Cloud Sync Service...")
        cloud_sync_service = CloudSyncService(settings, buffer_manager)
        await cloud_sync_service.start()
        
        # Initialize Thompson Sampling adaptive sensing
        logger.info("Initializing Adaptive Sensing (Thompson Sampling)...")
        adaptive_ts = AdaptiveSamplingTS()
        app.state.adaptive_ts = adaptive_ts

        # Initialize MQTT ingestion service
        logger.info("Initializing MQTT Ingestion Service...")
        mqtt_service = MQTTIngestionService(
            settings=settings,
            validator=validator,
            buffer_manager=buffer_manager,
            emergency_controller=emergency_controller,
            adaptive_ts=adaptive_ts,
        )
        await mqtt_service.connect()
        
        logger.info("✓ All services started successfully")
        logger.info("=" * 60)
        
        # Store in app state for access in routes
        app.state.mqtt_service = mqtt_service
        app.state.buffer_manager = buffer_manager
        app.state.emergency_controller = emergency_controller
        app.state.cloud_sync_service = cloud_sync_service
        
        yield
        
    finally:
        # Cleanup on shutdown
        logger.info("=" * 60)
        logger.info("Shutting down Fog Gateway Services...")
        logger.info("=" * 60)
        
        if mqtt_service:
            logger.info("Stopping MQTT Ingestion Service...")
            await mqtt_service.disconnect()
        
        if emergency_controller:
            logger.info("Stopping Emergency Controller...")
            await emergency_controller.stop()
        
        if cloud_sync_service:
            logger.info("Stopping Cloud Sync Service...")
            await cloud_sync_service.stop()
        
        if buffer_manager:
            logger.info("Closing Buffer Manager...")
            await buffer_manager.close()
        
        logger.info("✓ All services stopped")


# Create FastAPI application
app = FastAPI(
    title="Smart Farming Fog Gateway",
    description="Local edge gateway for IoT farm data processing and buffering",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Smart Farming Fog Gateway",
        "version": "1.0.0",
        "status": "operational",
        "farm_id": settings.farm_id,
        "device_id": settings.device_id
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "services": {
            "mqtt": mqtt_service.is_connected() if mqtt_service else False,
            "buffer": buffer_manager.is_healthy() if buffer_manager else False,
            "emergency_control": emergency_controller.is_running() if emergency_controller else False,
            "cloud_sync": cloud_sync_service.is_connected() if cloud_sync_service else False
        }
    }
    
    all_healthy = all(health_status["services"].values())
    health_status["status"] = "healthy" if all_healthy else "degraded"
    
    return health_status


def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {sig}, shutting down gracefully...")
    sys.exit(0)


if __name__ == "__main__":
    import uvicorn
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run the application
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level="info"
    )
