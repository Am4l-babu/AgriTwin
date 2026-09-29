"""
MQTT Client for Smart Farming System

Connects to MQTT broker and bridges sensor data to WebSocket clients.
"""

import json
import asyncio
import uuid
from typing import Optional, Callable
import paho.mqtt.client as mqtt
from loguru import logger


class MQTTClient:
    """
    MQTT Client that subscribes to sensor data and bridges to WebSocket
    """
    
    def __init__(
        self, 
        broker_host: str = "localhost",
        broker_port: int = 1883,
        username: Optional[str] = None,
        password: Optional[str] = None,
        event_loop=None
    ):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.username = username
        self.password = password
        
        self.client: Optional[mqtt.Client] = None
        self.is_connected = False
        self.message_callback: Optional[Callable] = None
        self.event_loop = event_loop  # Store the event loop reference
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker (callback API v1)"""
        if rc == 0:
            self.is_connected = True
            logger.info(f"✓ Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            
            # Subscribe to all farm sensor data topics
            # Pattern matches:  farms/001/sensors/temperature/data  etc.
            topics = [
                ("farms/+/sensors/+/data", 0),
                ("farms/+/status",         0),
            ]
            client.subscribe(topics)
            for t, _ in topics:
                logger.info(f"✓ Subscribed to MQTT topic: {t}")
        else:
            logger.error(f"✗ Failed to connect to MQTT broker. Return code: {rc}")
            self.is_connected = False
    
    def on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker (callback API v1)"""
        self.is_connected = False
        if rc != 0:
            logger.warning(f"⚠️  Unexpected MQTT disconnection. Return code: {rc}")
        else:
            logger.info("MQTT client disconnected")
    
    def on_message(self, client, userdata, msg):
        """Callback when MQTT message is received"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            logger.debug(f"MQTT message received on {topic}: {payload}")
            
            # Parse JSON payload
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in MQTT message: {payload}")
                return
            
            # Extract farm_id from topic.
            # New pattern:  farms/001/sensors/temperature/data  -> topic_parts[1] = "001"
            # Status:        farms/001/status                   -> topic_parts[1] = "001"
            topic_parts = topic.split('/')
            if len(topic_parts) >= 2:
                farm_id = topic_parts[1]   # e.g. "001"
            else:
                farm_id = "001"  # Default
            
            # Call the message callback if registered
            # Use asyncio's thread-safe call_soon_threadsafe to schedule the coroutine
            if self.message_callback and self.event_loop:
                try:
                    # Schedule the callback on the stored event loop
                    asyncio.run_coroutine_threadsafe(
                        self.message_callback(farm_id, data, topic),
                        self.event_loop
                    )
                except Exception as e:
                    logger.error(f"Error scheduling callback: {e}")
            
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def set_message_callback(self, callback: Callable):
        """Register callback for when messages are received"""
        self.message_callback = callback
    
    def start(self):
        """Start the MQTT client"""
        try:
            # Use callback API v1 with unique client ID to avoid conflicts
            unique_id = f"smart_farming_backend_{uuid.uuid4().hex[:8]}"
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, client_id=unique_id)
            
            # Set authentication if provided
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
            
            # Set callbacks
            self.client.on_connect = self.on_connect
            self.client.on_disconnect = self.on_disconnect
            self.client.on_message = self.on_message
            
            # Connect to broker
            logger.info(f"Connecting to MQTT broker at {self.broker_host}:{self.broker_port}...")
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
            
            # Start network loop in background thread
            self.client.loop_start()
            
            logger.info("✓ MQTT client started")
            
        except Exception as e:
            logger.error(f"✗ Failed to start MQTT client: {e}")
            raise
    
    def stop(self):
        """Stop the MQTT client"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("MQTT client stopped")
    
    def reconnect(self):
        """Attempt to reconnect to the MQTT broker."""
        try:
            if self.client is None:
                # Full restart if client was never created
                self.start()
                return
            logger.info(f"Attempting MQTT reconnect to {self.broker_host}:{self.broker_port}...")
            self.client.reconnect()
            self.client.loop_start()
            logger.info("MQTT reconnect initiated")
        except Exception as e:
            logger.error(f"MQTT reconnect failed: {e}")
            raise

    def publish(self, topic: str, payload: dict):
        """Publish message to MQTT topic"""
        if self.client and self.is_connected:
            message = json.dumps(payload)
            self.client.publish(topic, message)
            logger.debug(f"Published to {topic}: {message}")


# Global MQTT client instance
mqtt_client: Optional[MQTTClient] = None


def get_mqtt_client() -> MQTTClient:
    """Get global MQTT client instance"""
    return mqtt_client


def init_mqtt_client(broker_host: str = "localhost", broker_port: int = 1883, event_loop=None) -> MQTTClient:
    """Initialize global MQTT client"""
    global mqtt_client
    mqtt_client = MQTTClient(broker_host=broker_host, broker_port=broker_port, event_loop=event_loop)
    return mqtt_client
