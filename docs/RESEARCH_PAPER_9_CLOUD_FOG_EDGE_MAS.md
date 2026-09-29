# DIGITAL TWIN DEPLOYMENT IN CLOUD-FOG-EDGE WITH MULTI-AGENT SYSTEMS
## Based on "Digital twin deployment for smart agriculture in Cloud-Fog-Edge infrastructure" by Kalyani et al. (2023)

---

## 🎯 EXECUTIVE SUMMARY

This research paper provides a **practical implementation framework** for deploying Digital Twins in agriculture using **Cloud-Fog-Edge infrastructure with Multi-Agent Systems (MAS)**. It addresses real-world challenges like poor connectivity, resource allocation, and granular field management.

### Key Focus Areas:
1. **Three-Layer Architecture** - Cloud, Fog (static + mobile), Edge
2. **Multi-Agent Systems** - Autonomous decision-making agents
3. **Semantic Web & Linked Data** - JSON-LD, ontologies, interoperability
4. **Opportunistic Sensing** - Data collection in disconnected environments
5. **Granular Field Management** - 10m x 10m grid-level monitoring
6. **Four-Layer DT Architecture** - External, Microservices, Knowledge/Hypermedia, Decision

### Critical Insight:
**Your AgriTwin system already has Cloud-Fog-Edge foundation!** This paper shows how to enhance it with MAS and semantic web technologies.

---

## 📊 YOUR SYSTEM vs RESEARCH FRAMEWORK

### Current State Analysis:

| Component | Your AgriTwin | Research Framework | Gap |
|-----------|---------------|-------------------|-----|
| **Cloud Layer** | ✅ FastAPI backend, SQLite | ✅ Big data analytics, ML services | Minor |
| **Fog Layer (Static)** | ✅ Fog gateway, Redis, SQLite | ✅ Farm Management System | Good |
| **Fog Layer (Mobile)** | ❌ None | ⚠️ Tractors, drones, robots | MISSING |
| **Edge Layer** | ✅ ESP32 + sensors | ✅ Agricultural devices | Good |
| **Multi-Agent System** | ❌ None | ❌ CRITICAL | MISSING |
| **Semantic Web** | ❌ None | ❌ JSON-LD, ontologies | MISSING |
| **Opportunistic Sensing** | ❌ None | ⚠️ Offline data collection | MISSING |
| **Granular Management** | ⚠️ Farm-level only | ✅ 10m x 10m grid | NEEDS IMPROVEMENT |
| **Microservices** | ⚠️ Monolithic | ✅ Decoupled services | NEEDS REFACTORING |

---

## 🚀 CRITICAL IMPROVEMENTS FROM RESEARCH

### 1. MOBILE FOG NODES (HIGHEST PRIORITY - NEW CONCEPT)

**Current Issue**: Your system assumes constant internet connectivity
**Improvement**: Add mobile fog nodes for disconnected environments

#### What are Mobile Fog Nodes?
Mobile fog nodes are computing resources attached to **moving equipment** (tractors, drones, robots) that:
- Collect data in areas without internet
- Process data locally
- Sync when connectivity is restored
- Extend fog network reach

#### Implementation:

```python
# Add to fog/src/
- mobile_fog/
  - mobile_node_manager.py
  - opportunistic_collector.py
  - sync_manager.py
  - offline_processor.py
```

**Mobile Fog Node Architecture:**
```python
# fog/src/mobile_fog/mobile_node_manager.py

from dataclasses import dataclass
from typing import Dict, List, Any
from datetime import datetime
import asyncio
import json

@dataclass
class MobileFogNode:
    """
    Mobile fog node attached to farm equipment
    
    Examples:
    - Tractor with edge computer
    - Drone with processing unit
    - Agricultural robot
    - Combine harvester
    """
    node_id: str
    node_type: str  # "tractor", "drone", "robot", "harvester"
    location: Dict[str, float]  # GPS coordinates
    connectivity_status: str  # "connected", "disconnected"
    local_storage_capacity_gb: float
    processing_power: str  # "low", "medium", "high"
    battery_level: float = 100.0
    
    def __post_init__(self):
        self.data_buffer = []
        self.last_sync_time = None
        self.collected_data_count = 0

class OpportunisticDataCollector:
    """
    Collects data opportunistically when mobile fog node
    passes near edge devices in areas without connectivity
    """
    
    def __init__(self, mobile_node: MobileFogNode):
        self.mobile_node = mobile_node
        self.collection_radius_m = 50  # Collect from devices within 50m
        self.edge_devices_in_range = []
    
    async def scan_for_edge_devices(self) -> List[str]:
        """
        Scan for edge devices in range
        Uses Bluetooth, WiFi Direct, or LoRa
        """
        # Simulate scanning
        # In production, use actual wireless scanning
        devices_found = []
        
        # Example: Bluetooth Low Energy scan
        # devices_found = await self.ble_scan()
        
        # Example: WiFi Direct discovery
        # devices_found = await self.wifi_direct_discover()
        
        return devices_found
    
    async def collect_from_device(self, device_id: str) -> Dict:
        """
        Collect buffered data from edge device
        """
        # Request data from edge device
        data_request = {
            "collector_id": self.mobile_node.node_id,
            "device_id": device_id,
            "request_type": "data_harvest",
            "timestamp": datetime.now().isoformat()
        }
        
        # In production, send via Bluetooth/WiFi Direct
        # response = await self.send_request(device_id, data_request)
        
        # Simulate response
        response = {
            "device_id": device_id,
            "data": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "temperature": 25.0,
                    "humidity": 60.0,
                    "soil_moisture": 45.0
                }
            ],
            "data_count": 1
        }
        
        return response
    
    async def opportunistic_collection_cycle(self):
        """
        Main collection cycle for mobile fog node
        """
        while True:
            # Check connectivity
            if self.mobile_node.connectivity_status == "disconnected":
                # Scan for nearby edge devices
                devices = await self.scan_for_edge_devices()
                
                for device_id in devices:
                    # Collect data from each device
                    data = await self.collect_from_device(device_id)
                    
                    # Store in local buffer
                    self.mobile_node.data_buffer.append(data)
                    self.mobile_node.collected_data_count += data["data_count"]
                    
                    logger.info(f"Collected {data['data_count']} records from {device_id}")
            
            await asyncio.sleep(30)  # Scan every 30 seconds

class MobileFogSyncManager:
    """
    Manages synchronization between mobile fog nodes and static fog
    """
    
    def __init__(self, static_fog_endpoint: str):
        self.static_fog_endpoint = static_fog_endpoint
        self.sync_queue = []
    
    async def check_connectivity(self, mobile_node: MobileFogNode) -> bool:
        """Check if mobile node can reach static fog"""
        try:
            # Ping static fog
            response = await self.ping_static_fog()
            mobile_node.connectivity_status = "connected"
            return True
        except:
            mobile_node.connectivity_status = "disconnected"
            return False
    
    async def sync_data(self, mobile_node: MobileFogNode):
        """
        Sync buffered data to static fog when connectivity available
        """
        if mobile_node.connectivity_status == "connected":
            if mobile_node.data_buffer:
                # Upload buffered data
                for data_batch in mobile_node.data_buffer:
                    try:
                        await self.upload_to_static_fog(data_batch)
                        logger.info(f"Synced {len(data_batch)} records")
                    except Exception as e:
                        logger.error(f"Sync failed: {e}")
                        break
                
                # Clear buffer after successful sync
                mobile_node.data_buffer.clear()
                mobile_node.last_sync_time = datetime.now()
                mobile_node.collected_data_count = 0
    
    async def upload_to_static_fog(self, data: Dict):
        """Upload data to static fog"""
        # HTTP POST to static fog
        # response = await httpx.post(
        #     f"{self.static_fog_endpoint}/api/v1/mobile_sync",
        #     json=data
        # )
        pass
    
    async def continuous_sync_monitor(self, mobile_node: MobileFogNode):
        """
        Continuously monitor connectivity and sync when available
        """
        while True:
            # Check connectivity
            is_connected = await self.check_connectivity(mobile_node)
            
            if is_connected:
                # Sync data
                await self.sync_data(mobile_node)
            
            await asyncio.sleep(60)  # Check every minute

class MobileFogProcessor:
    """
    Process data locally on mobile fog node
    """
    
    def __init__(self, mobile_node: MobileFogNode):
        self.mobile_node = mobile_node
    
    async def process_locally(self, data: Dict) -> Dict:
        """
        Process data on mobile fog node
        
        Examples:
        - Calculate averages
        - Detect anomalies
        - Generate alerts
        - Compress data
        """
        processed = {
            "original_data": data,
            "processing_timestamp": datetime.now().isoformat(),
            "processor": self.mobile_node.node_id
        }
        
        # Calculate statistics
        if "data" in data:
            values = [d.get("soil_moisture", 0) for d in data["data"]]
            processed["statistics"] = {
                "count": len(values),
                "mean": sum(values) / len(values) if values else 0,
                "min": min(values) if values else 0,
                "max": max(values) if values else 0
            }
        
        # Anomaly detection
        processed["anomalies"] = self.detect_anomalies(data)
        
        return processed
    
    def detect_anomalies(self, data: Dict) -> List[Dict]:
        """Detect anomalies in collected data"""
        anomalies = []
        
        if "data" in data:
            for record in data["data"]:
                # Check for out-of-range values
                if record.get("temperature", 0) > 40:
                    anomalies.append({
                        "type": "high_temperature",
                        "value": record["temperature"],
                        "timestamp": record["timestamp"]
                    })
                
                if record.get("soil_moisture", 100) < 20:
                    anomalies.append({
                        "type": "low_moisture",
                        "value": record["soil_moisture"],
                        "timestamp": record["timestamp"]
                    })
        
        return anomalies

# Usage Example
async def deploy_mobile_fog_node():
    """Deploy mobile fog node on tractor"""
    # Create mobile fog node
    tractor_fog = MobileFogNode(
        node_id="tractor_001",
        node_type="tractor",
        location={"lat": 53.3498, "lon": -6.2603},
        connectivity_status="connected",
        local_storage_capacity_gb=128.0,
        processing_power="medium"
    )
    
    # Create components
    collector = OpportunisticDataCollector(tractor_fog)
    sync_manager = MobileFogSyncManager("http://static-fog:5000")
    processor = MobileFogProcessor(tractor_fog)
    
    # Start collection and sync tasks
    await asyncio.gather(
        collector.opportunistic_collection_cycle(),
        sync_manager.continuous_sync_monitor(tractor_fog)
    )
```

**Benefits:**
- ✅ Works in areas without internet
- ✅ No data loss
- ✅ Local processing reduces bandwidth
- ✅ Extends fog network reach
- ✅ Resilient to connectivity issues

---


### 2. MULTI-AGENT SYSTEM (MAS) ARCHITECTURE (CRITICAL PRIORITY)

**Current Issue**: Monolithic system, no autonomous decision-making
**Improvement**: Implement MAS with specialized agents

#### Agent Types from Research:

**A. Field Agent** - Oversees each field's digital twin
**B. Sensor Harvester Agent** - Collects data from edge devices
**C. Task Agent** - Executes specific tasks
**D. Decision Agent** - Makes intelligent decisions
**E. Initialization Agent** - Sets up digital twins

#### Implementation:

```python
# Add to cloud/backend/
- multi_agent_system/
  - agent_base.py
  - field_agent.py
  - sensor_harvester_agent.py
  - decision_agent.py
  - task_agent.py
  - agent_communication.py
```

**Multi-Agent System Implementation:**
```python
# cloud/backend/multi_agent_system/agent_base.py

from abc import ABC, abstractmethod
from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum
import asyncio
import uuid

class AgentState(Enum):
    IDLE = "idle"
    ACTIVE = "active"
    BUSY = "busy"
    ERROR = "error"
    TERMINATED = "terminated"

@dataclass
class AgentMessage:
    """Message between agents"""
    message_id: str
    sender_id: str
    receiver_id: str
    message_type: str  # "request", "response", "inform", "command"
    content: Dict
    priority: int  # 1=low, 5=critical
    timestamp: str
    
    def __post_init__(self):
        if not self.message_id:
            self.message_id = str(uuid.uuid4())

class BaseAgent(ABC):
    """
    Base class for all agents in MAS
    
    Agents are autonomous entities that:
    - Perceive their environment
    - Make decisions
    - Take actions
    - Communicate with other agents
    """
    
    def __init__(self, agent_id: str, agent_type: str):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.state = AgentState.IDLE
        self.inbox: List[AgentMessage] = []
        self.knowledge_base: Dict = {}
        self.other_agents: Dict[str, 'BaseAgent'] = {}
        self.capabilities: List[str] = []
    
    async def run(self):
        """Main agent loop"""
        while self.state != AgentState.TERMINATED:
            try:
                # Process messages
                await self.process_inbox()
                
                # Perceive environment
                perceptions = await self.perceive()
                
                # Make decisions
                decisions = await self.decide(perceptions)
                
                # Execute actions
                if decisions:
                    await self.act(decisions)
                
                # Update knowledge
                await self.learn(perceptions, decisions)
                
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Agent {self.agent_id} error: {e}")
                self.state = AgentState.ERROR
                await asyncio.sleep(5)
    
    @abstractmethod
    async def perceive(self) -> Dict:
        """Perceive environment - implemented by subclasses"""
        pass
    
    @abstractmethod
    async def decide(self, perceptions: Dict) -> List[Dict]:
        """Make decisions - implemented by subclasses"""
        pass
    
    @abstractmethod
    async def act(self, decisions: List[Dict]):
        """Execute actions - implemented by subclasses"""
        pass
    
    async def send_message(self, receiver_id: str, message_type: str,
                          content: Dict, priority: int = 3):
        """Send message to another agent"""
        message = AgentMessage(
            message_id=str(uuid.uuid4()),
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            message_type=message_type,
            content=content,
            priority=priority,
            timestamp=datetime.now().isoformat()
        )
        
        if receiver_id in self.other_agents:
            await self.other_agents[receiver_id].receive_message(message)
        else:
            logger.warning(f"Agent {receiver_id} not found")
    
    async def receive_message(self, message: AgentMessage):
        """Receive message from another agent"""
        self.inbox.append(message)
        # Sort by priority
        self.inbox.sort(key=lambda m: m.priority, reverse=True)
    
    async def process_inbox(self):
        """Process messages in inbox"""
        while self.inbox:
            message = self.inbox.pop(0)
            await self.handle_message(message)
    
    @abstractmethod
    async def handle_message(self, message: AgentMessage):
        """Handle received message - implemented by subclasses"""
        pass
    
    async def learn(self, perceptions: Dict, decisions: List[Dict]):
        """Update knowledge base"""
        self.knowledge_base[datetime.now().isoformat()] = {
            "perceptions": perceptions,
            "decisions": decisions
        }
    
    def register_agent(self, agent: 'BaseAgent'):
        """Register another agent for communication"""
        self.other_agents[agent.agent_id] = agent
    
    def add_capability(self, capability: str):
        """Add capability to agent"""
        if capability not in self.capabilities:
            self.capabilities.append(capability)

# cloud/backend/multi_agent_system/field_agent.py

class FieldAgent(BaseAgent):
    """
    Field Agent oversees a specific field's digital twin
    
    Responsibilities:
    - Monitor field conditions
    - Make field-level decisions
    - Coordinate with other agents
    - Update field digital twin
    """
    
    def __init__(self, field_id: str):
        super().__init__(f"field_agent_{field_id}", "field_agent")
        self.field_id = field_id
        self.field_digital_twin = None
        self.field_plan = None
        self.sensor_data = {}
        
        # Capabilities
        self.add_capability("monitor_field")
        self.add_capability("irrigation_decision")
        self.add_capability("fertilization_decision")
        self.add_capability("pest_detection")
    
    async def perceive(self) -> Dict:
        """Perceive field conditions"""
        # Get latest sensor data
        sensor_data = await self.get_sensor_data()
        
        # Get weather data
        weather_data = await self.get_weather_data()
        
        # Get digital twin state
        twin_state = await self.get_twin_state()
        
        return {
            "sensor_data": sensor_data,
            "weather_data": weather_data,
            "twin_state": twin_state,
            "timestamp": datetime.now().isoformat()
        }
    
    async def decide(self, perceptions: Dict) -> List[Dict]:
        """Make field-level decisions"""
        decisions = []
        
        sensor_data = perceptions.get("sensor_data", {})
        weather_data = perceptions.get("weather_data", {})
        
        # Decision 1: Irrigation
        if sensor_data.get("soil_moisture", 100) < 30:
            # Check weather forecast
            if weather_data.get("rain_forecast_24h", 0) < 5:
                decisions.append({
                    "type": "irrigation",
                    "action": "irrigate",
                    "duration": 300,  # seconds
                    "reason": "Low soil moisture, no rain forecast",
                    "priority": 4
                })
        
        # Decision 2: Fertilization
        if sensor_data.get("nitrogen", 100) < 20:
            decisions.append({
                "type": "fertilization",
                "action": "apply_nitrogen",
                "amount_kg": 50,
                "reason": "Nitrogen deficiency detected",
                "priority": 3
            })
        
        # Decision 3: Pest alert
        if sensor_data.get("pest_detected", False):
            decisions.append({
                "type": "alert",
                "action": "notify_farmer",
                "message": "Pest detected in field",
                "priority": 5
            })
        
        return decisions
    
    async def act(self, decisions: List[Dict]):
        """Execute decisions"""
        for decision in decisions:
            if decision["type"] == "irrigation":
                # Send command to irrigation system
                await self.send_message(
                    "irrigation_agent",
                    "command",
                    {
                        "action": "irrigate",
                        "field_id": self.field_id,
                        "duration": decision["duration"]
                    },
                    priority=decision["priority"]
                )
            
            elif decision["type"] == "fertilization":
                # Create task for fertilization
                await self.send_message(
                    "task_agent",
                    "request",
                    {
                        "task_type": "fertilization",
                        "field_id": self.field_id,
                        "details": decision
                    },
                    priority=decision["priority"]
                )
            
            elif decision["type"] == "alert":
                # Send alert to farmer
                await self.send_message(
                    "notification_agent",
                    "inform",
                    {
                        "alert_type": "pest_detection",
                        "field_id": self.field_id,
                        "message": decision["message"]
                    },
                    priority=decision["priority"]
                )
    
    async def handle_message(self, message: AgentMessage):
        """Handle messages from other agents"""
        if message.message_type == "request":
            if message.content.get("query") == "field_status":
                # Send field status
                status = await self.get_field_status()
                await self.send_message(
                    message.sender_id,
                    "response",
                    {"field_status": status},
                    priority=2
                )
        
        elif message.message_type == "inform":
            # Update knowledge base
            self.knowledge_base[message.timestamp] = message.content
    
    async def get_sensor_data(self) -> Dict:
        """Get latest sensor data for field"""
        # Query database or API
        return {
            "soil_moisture": 45.0,
            "temperature": 22.0,
            "humidity": 60.0,
            "nitrogen": 25.0
        }
    
    async def get_weather_data(self) -> Dict:
        """Get weather data"""
        return {
            "temperature": 20.0,
            "rain_forecast_24h": 0.0
        }
    
    async def get_twin_state(self) -> Dict:
        """Get digital twin state"""
        if self.field_digital_twin:
            return self.field_digital_twin.get_state()
        return {}
    
    async def get_field_status(self) -> Dict:
        """Get comprehensive field status"""
        return {
            "field_id": self.field_id,
            "state": self.state.value,
            "sensor_data": await self.get_sensor_data(),
            "recent_decisions": list(self.knowledge_base.values())[-5:]
        }

# cloud/backend/multi_agent_system/sensor_harvester_agent.py

class SensorHarvesterAgent(BaseAgent):
    """
    Sensor Harvester Agent collects data from edge devices
    
    Responsibilities:
    - Discover edge devices
    - Collect sensor data
    - Validate data quality
    - Forward to appropriate agents
    """
    
    def __init__(self):
        super().__init__("sensor_harvester", "sensor_harvester")
        self.edge_devices = {}
        self.collection_interval = 10  # seconds
        
        self.add_capability("data_collection")
        self.add_capability("data_validation")
    
    async def perceive(self) -> Dict:
        """Perceive available edge devices"""
        # Discover edge devices
        devices = await self.discover_edge_devices()
        
        return {
            "available_devices": devices,
            "timestamp": datetime.now().isoformat()
        }
    
    async def decide(self, perceptions: Dict) -> List[Dict]:
        """Decide which devices to harvest from"""
        decisions = []
        
        for device in perceptions.get("available_devices", []):
            decisions.append({
                "type": "harvest",
                "device_id": device["device_id"],
                "priority": 3
            })
        
        return decisions
    
    async def act(self, decisions: List[Dict]):
        """Harvest data from devices"""
        for decision in decisions:
            if decision["type"] == "harvest":
                data = await self.harvest_from_device(decision["device_id"])
                
                # Validate data
                if self.validate_data(data):
                    # Forward to field agent
                    field_id = self.get_field_for_device(decision["device_id"])
                    await self.send_message(
                        f"field_agent_{field_id}",
                        "inform",
                        {"sensor_data": data},
                        priority=3
                    )
    
    async def handle_message(self, message: AgentMessage):
        """Handle messages"""
        if message.message_type == "request":
            if message.content.get("action") == "harvest_now":
                device_id = message.content.get("device_id")
                data = await self.harvest_from_device(device_id)
                await self.send_message(
                    message.sender_id,
                    "response",
                    {"data": data},
                    priority=3
                )
    
    async def discover_edge_devices(self) -> List[Dict]:
        """Discover available edge devices"""
        # Query device registry
        return [
            {"device_id": "esp32_001", "type": "sensor", "status": "online"},
            {"device_id": "esp32_002", "type": "sensor", "status": "online"}
        ]
    
    async def harvest_from_device(self, device_id: str) -> Dict:
        """Harvest data from specific device"""
        # MQTT subscribe or HTTP GET
        return {
            "device_id": device_id,
            "temperature": 22.0,
            "humidity": 60.0,
            "timestamp": datetime.now().isoformat()
        }
    
    def validate_data(self, data: Dict) -> bool:
        """Validate data quality"""
        # Check for required fields
        required = ["device_id", "timestamp"]
        if not all(field in data for field in required):
            return False
        
        # Check value ranges
        if "temperature" in data:
            if not (-40 <= data["temperature"] <= 80):
                return False
        
        return True
    
    def get_field_for_device(self, device_id: str) -> str:
        """Get field ID for device"""
        # Query device-field mapping
        return "field_001"

# cloud/backend/multi_agent_system/agent_communication.py

class AgentCommunicationManager:
    """
    Manages communication between agents
    """
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.message_log: List[AgentMessage] = []
    
    def register_agent(self, agent: BaseAgent):
        """Register agent in system"""
        self.agents[agent.agent_id] = agent
        
        # Register with all other agents
        for other_agent in self.agents.values():
            if other_agent.agent_id != agent.agent_id:
                agent.register_agent(other_agent)
                other_agent.register_agent(agent)
    
    async def broadcast_message(self, sender_id: str, message_type: str,
                               content: Dict, priority: int = 3):
        """Broadcast message to all agents"""
        for agent_id, agent in self.agents.items():
            if agent_id != sender_id:
                message = AgentMessage(
                    message_id=str(uuid.uuid4()),
                    sender_id=sender_id,
                    receiver_id=agent_id,
                    message_type=message_type,
                    content=content,
                    priority=priority,
                    timestamp=datetime.now().isoformat()
                )
                await agent.receive_message(message)
                self.message_log.append(message)
    
    def get_agent_status(self) -> Dict:
        """Get status of all agents"""
        return {
            "total_agents": len(self.agents),
            "agents": {
                agent_id: {
                    "type": agent.agent_type,
                    "state": agent.state.value,
                    "capabilities": agent.capabilities,
                    "inbox_size": len(agent.inbox)
                }
                for agent_id, agent in self.agents.items()
            }
        }

# Usage Example
async def initialize_mas():
    """Initialize Multi-Agent System"""
    comm_manager = AgentCommunicationManager()
    
    # Create agents
    field_agent = FieldAgent("field_001")
    sensor_harvester = SensorHarvesterAgent()
    
    # Register agents
    comm_manager.register_agent(field_agent)
    comm_manager.register_agent(sensor_harvester)
    
    # Start agents
    await asyncio.gather(
        field_agent.run(),
        sensor_harvester.run()
    )
```

**Benefits:**
- ✅ Autonomous decision-making
- ✅ Distributed intelligence
- ✅ Scalable architecture
- ✅ Fault-tolerant
- ✅ Flexible and extensible

---

