"""
Fog Layer Configuration Settings
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Fog layer configuration"""
    
    # Farm identification
    farm_id: str = "farm_001"
    device_id: str = "fog_001"
    
    # MQTT Configuration
    # On the Raspberry Pi, Mosquitto runs locally so "localhost" is correct.
    mqtt_broker: str = "localhost"
    mqtt_port: int = 1883
    mqtt_username: Optional[str] = None
    mqtt_password: Optional[str] = None
    mqtt_qos: int = 1
    
    # Redis Configuration (hot buffer)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # Cloud Backend Configuration
    # Set CLOUD_BACKEND_URL to the laptop's IP or hostname, e.g.:
    #   export CLOUD_BACKEND_URL=http://192.168.x.x:8000
    cloud_backend_url: str = "http://localhost:8000"
    cloud_api_key: Optional[str] = None
    cloud_sync_interval_sec: int = 30
    
    # Emergency Control
    emergency_control_enabled: bool = True
    irrigation_threshold: float = 30.0  # Soil moisture %
    temperature_alert: float = 35.0     # Temperature °C
    
    # Digital Twin Configuration
    digital_twin_enabled: bool = True
    simulation_interval_sec: int = 300  # 5 minutes
    enable_physics: bool = True
    enable_ai: bool = True
    enable_optimization: bool = True
    
    # Buffering
    hot_buffer_hours: int = 1
    cold_buffer_days: int = 7
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/fog.log"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
