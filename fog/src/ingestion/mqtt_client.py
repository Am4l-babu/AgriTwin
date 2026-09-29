"""
MQTT Ingestion Service

Subscribes to MQTT topics from edge devices and processes incoming data.
"""

import json
import asyncio
from typing import Callable, Optional
from loguru import logger
import paho.mqtt.client as mqtt

from src.config.settings import Settings
from src.preprocessing.validator import DataValidator
from src.buffer_manager.buffer import BufferManager
from src.emergency_control.controller import EmergencyController
from src.adaptive_sensing.thompson_sampler import AdaptiveSamplingTS


class MQTTIngestionService:
    """
    MQTT client for ingesting sensor data from edge devices
    """
    
    def __init__(
        self,
        settings: Settings,
        validator: DataValidator,
        buffer_manager: BufferManager,
        emergency_controller: EmergencyController,
        adaptive_ts: Optional[AdaptiveSamplingTS] = None,
    ):
        self.settings = settings
        self.validator = validator
        self.buffer = buffer_manager
        self.emergency = emergency_controller
        self.adaptive_ts = adaptive_ts

        self.client = mqtt.Client(client_id=f"{settings.device_id}_ingestion")
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        self._connected = False
        self._message_count = 0
        
    async def connect(self):
        """Connect to MQTT broker"""
        try:
            if self.settings.mqtt_username:
                self.client.username_pw_set(
                    self.settings.mqtt_username,
                    self.settings.mqtt_password
                )
            
            logger.info(
                f"Connecting to MQTT broker: {self.settings.mqtt_broker_host}:{self.settings.mqtt_broker_port}"
            )
            
            self.client.connect(
                self.settings.mqtt_broker_host,
                self.settings.mqtt_broker_port,
                self.settings.mqtt_keepalive
            )
            
            # Start loop in background
            self.client.loop_start()
            
            # Wait for connection
            for _ in range(10):
                if self._connected:
                    break
                await asyncio.sleep(0.5)
            
            if not self._connected:
                raise Exception("Failed to connect to MQTT broker")
                
        except Exception as e:
            logger.error(f"MQTT connection error: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from MQTT broker"""
        logger.info("Disconnecting from MQTT broker...")
        self.client.loop_stop()
        self.client.disconnect()
        self._connected = False
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to broker"""
        if rc == 0:
            logger.info("✓ Connected to MQTT broker")
            self._connected = True
            
            # Subscribe to topics
            topics = [
                (f"farms/+/sensors/+/data", self.settings.mqtt_qos),
                (f"farms/+/status", self.settings.mqtt_qos),
                (f"farms/+/alerts", self.settings.mqtt_qos),
            ]
            
            for topic, qos in topics:
                client.subscribe(topic, qos)
                logger.info(f"Subscribed to: {topic}")
        else:
            logger.error(f"MQTT connection failed with code: {rc}")
            self._connected = False
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from broker"""
        self._connected = False
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection (code: {rc})")
        else:
            logger.info("Disconnected from MQTT broker")
    
    def _on_message(self, client, userdata, msg):
        """Callback when message received"""
        try:
            self._message_count += 1
            
            # Parse topic
            topic_parts = msg.topic.split('/')
            farm_id = topic_parts[1]
            
            # Decode payload
            payload = json.loads(msg.payload.decode())
            
            logger.debug(f"Received message from {farm_id}: {msg.topic}")
            
            # Validate data
            if self.settings.validation_enabled:
                is_valid, errors = self.validator.validate_sensor_data(payload)
                if not is_valid:
                    logger.warning(f"Invalid data from {farm_id}: {errors}")
                    return
            
            # Store in buffer
            asyncio.create_task(self._process_message(farm_id, topic_parts, payload))
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
        except Exception as e:
            logger.error(f"Message processing error: {e}")
    
    async def _process_message(self, farm_id: str, topic_parts: list, payload: dict):
        """Process and store incoming message"""
        try:
            # Determine message type
            if "sensors" in topic_parts:
                # Sensor data
                sensor_type = topic_parts[3]
                await self.buffer.store_sensor_data(farm_id, sensor_type, payload)

                # Thompson Sampling: update bandit with new reading
                if self.adaptive_ts and "value" in payload:
                    self.adaptive_ts.on_reading(sensor_type, float(payload["value"]))
                    cmd = self.adaptive_ts.get_command()
                    if cmd:
                        cmd_topic = f"farms/{farm_id.split('/')[-1]}/commands"
                        self.client.publish(
                            cmd_topic,
                            json.dumps(cmd),
                            qos=1,
                            retain=False,
                        )
                        logger.info(f"TS command published → {cmd_topic}: {cmd}")

                # Check emergency conditions
                await self.emergency.evaluate_conditions(farm_id, sensor_type, payload)
                
            elif "status" in topic_parts:
                # Device status
                await self.buffer.store_status(farm_id, payload)
                
            elif "alerts" in topic_parts:
                # Alert message
                await self.buffer.store_alert(farm_id, payload)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def is_connected(self) -> bool:
        """Check if connected to broker"""
        return self._connected
    
    def get_message_count(self) -> int:
        """Get total message count"""
        return self._message_count
