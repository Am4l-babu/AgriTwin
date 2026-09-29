"""
MQTT Listener - Fog Layer Ingestion
Subscribes to sensor data from ESP32-S3 devices
"""

import asyncio
import json
import logging
from typing import Dict, Any, Callable
import paho.mqtt.client as mqtt
from datetime import datetime

logger = logging.getLogger(__name__)


class MQTTListener:
    """
    MQTT client for receiving sensor data from edge devices
    """
    
    def __init__(self, broker: str, port: int = 1883, 
                 on_message_callback: Callable = None):
        """
        Initialize MQTT listener
        
        Args:
            broker: MQTT broker hostname/IP
            port: MQTT broker port
            on_message_callback: Async callback for incoming messages
        """
        self.broker = broker
        self.port = port
        self.on_message_callback = on_message_callback
        
        self.client = mqtt.Client(client_id="fog_listener")
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect
        
        self.connected = False
        self.message_count = 0
        
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            self.connected = True
            logger.info(f"✓ Connected to MQTT broker {self.broker}:{self.port}")
            
            # Subscribe to all farm sensor data
            client.subscribe("farms/+/sensors/+/data", qos=1)
            client.subscribe("farms/+/status", qos=1)
            
            logger.info("✓ Subscribed to: farms/+/sensors/+/data")
            logger.info("✓ Subscribed to: farms/+/status")
        else:
            logger.error(f"✗ Connection failed with code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from broker"""
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected disconnection. Code: {rc}")
            logger.info("Attempting to reconnect...")
    
    def _on_message(self, client, userdata, msg):
        """Callback when message received"""
        try:
            # Parse JSON payload
            payload = json.loads(msg.payload.decode())
            
            # Add metadata
            payload['_mqtt_topic'] = msg.topic
            payload['_received_at'] = datetime.utcnow().isoformat()
            
            self.message_count += 1
            
            # Log periodically
            if self.message_count % 100 == 0:
                logger.info(f"Processed {self.message_count} messages")
            
            # Call async callback
            if self.on_message_callback:
                asyncio.create_task(self.on_message_callback(msg.topic, payload))
            else:
                logger.debug(f"Received: {msg.topic} -> {payload}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in topic {msg.topic}: {msg.payload}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            logger.info(f"Connecting to MQTT broker {self.broker}:{self.port}...")
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("Disconnected from MQTT broker")
    
    def publish(self, topic: str, payload: Dict[str, Any], qos: int = 1):
        """
        Publish message to MQTT topic
        
        Args:
            topic: MQTT topic
            payload: Message payload (will be JSON encoded)
            qos: Quality of Service (0, 1, or 2)
        """
        if not self.connected:
            logger.warning("Not connected to MQTT broker, cannot publish")
            return False
        
        try:
            payload_json = json.dumps(payload)
            result = self.client.publish(topic, payload_json, qos=qos)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published to {topic}: {payload_json}")
                return True
            else:
                logger.error(f"Failed to publish to {topic}")
                return False
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            return False
