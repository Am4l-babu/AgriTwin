"""
Configuration settings for Fog Gateway
"""

from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    """
    
    # Device identification
    farm_id: str = Field(default="farm_001", env="FARM_ID")
    device_id: str = Field(default="fog_gateway_001", env="FOG_DEVICE_ID")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
   # API configuration
    api_host: str = Field(default="0.0.0.0", env="FOG_API_HOST")
    api_port: int = Field(default=8001, env="FOG_API_PORT")
    api_reload: bool = Field(default=True, env="FOG_API_RELOAD")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="CORS_ORIGINS"
    )
    
    # MQTT configuration
    # mqtt_broker_host is "localhost" because on the Raspberry Pi the Mosquitto
    # broker runs on the same machine as the fog gateway.
    mqtt_broker_host: str = Field(default="localhost", env="MQTT_BROKER_HOST")
    mqtt_broker_port: int = Field(default=1883, env="MQTT_BROKER_PORT")
    mqtt_username: str = Field(default="smart_farming", env="MQTT_USERNAME")
    mqtt_password: str = Field(default="", env="MQTT_PASSWORD")
    mqtt_keepalive: int = Field(default=60, env="MQTT_KEEPALIVE")
    mqtt_qos: int = Field(default=1, env="MQTT_QOS")
    
    # Cloud configuration
    # cloud_api_url must point to the laptop running the cloud backend.
    # Set CLOUD_API_URL env var on the Raspberry Pi, e.g.:
    #   export CLOUD_API_URL=http://<laptop-ip>:8000
    # Avoid hardcoding IPs; prefer using mDNS if your router supports it.
    cloud_api_url: str = Field(default="http://localhost:8000", env="CLOUD_API_URL")
    cloud_mqtt_broker: str = Field(default="localhost", env="CLOUD_MQTT_BROKER")
    cloud_sync_interval: int = Field(default=30, env="CLOUD_SYNC_INTERVAL")
    cloud_connection_timeout: int = Field(default=10, env="CLOUD_CONNECTION_TIMEOUT")
    
    # Redis configuration
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_password: str = Field(default="", env="REDIS_PASSWORD")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_max_connections: int = Field(default=10, env="REDIS_MAX_CONNECTIONS")
    
    # SQLite configuration
    sqlite_db_path: str = Field(default="./data/fog_buffer.db", env="SQLITE_DB_PATH")
    
    # Buffer configuration
    buffer_max_size_mb: int = Field(default=100, env="BUFFER_MAX_SIZE_MB")
    buffer_max_records: int = Field(default=100000, env="BUFFER_MAX_RECORDS")
    buffer_retention_days: int = Field(default=7, env="BUFFER_RETENTION_DAYS")
    buffer_sync_batch_size: int = Field(default=100, env="BUFFER_SYNC_BATCH_SIZE")
    
    # Emergency control
    emergency_control_enabled: bool = Field(default=True, env="EMERGENCY_CONTROL_ENABLED")
    emergency_rules_file: str = Field(
        default="./config/emergency_rules.yaml",
        env="EMERGENCY_RULES_FILE"
    )
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file_path: str = Field(default="./logs/fog_gateway.log", env="LOG_FILE_PATH")
    
    # Data validation
    validation_enabled: bool = Field(default=True, env="VALIDATION_ENABLED")
    validation_schema_path: str = Field(
        default="./config/schemas",
        env="VALIDATION_SCHEMA_PATH"
    )
    
    # Performance
    max_workers: int = Field(default=4, env="MAX_WORKERS")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance
    """
    return Settings()
