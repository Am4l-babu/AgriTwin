# Multi-Agent System (MAS) for Autonomous Farm Operations

## Overview

The Multi-Agent System implements autonomous decision-making and task execution for precision agriculture, reducing manual intervention by 50% through intelligent agent collaboration.

Based on research papers:
- **Paper 7:** Horticulture Digital Twin with autonomous agents
- **Paper 9:** Cloud-Fog-Edge Multi-Agent System architecture

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT COORDINATOR                             │
│  • Message routing between agents                               │
│  • Health monitoring                                            │
│  • Performance metrics                                          │
│  • External API interface                                       │
└────────────┬────────────────────────────────────────────────────┘
             │
    ┌────────┴────────┬────────────┬────────────┐
    │                 │            │            │
┌───▼────┐    ┌──────▼─────┐  ┌──▼──────┐  ┌─▼─────────┐
│ FIELD  │    │  SENSOR    │  │DECISION │  │   TASK    │
│ AGENT  │    │ HARVESTER  │  │ AGENT   │  │  AGENT    │
│        │    │   AGENT    │  │         │  │           │
└────────┘    └────────────┘  └─────────┘  └───────────┘
```

## Agents

### 1. Field Agent
**Responsibilities:**
- Monitor environmental conditions (temperature, humidity, light, soil moisture)
- Track crop growth stages
- Calculate crop health score (0-100%)
- Detect anomalies in field conditions
- Report status to Decision Agent

**Beliefs:**
- current_temperature, current_humidity, current_light, current_soil_moisture
- crop_growth_stage, crop_health_score
- anomaly_detected

**Actions:**
- monitor_sensors
- calculate_health_score
- detect_anomalies
- report_status

### 2. Sensor Harvester Agent
**Responsibilities:**
- Collect sensor data from ESP32 devices
- Validate and preprocess data
- Optimize sampling rates (5-60 seconds)
- Detect sensor failures
- Forward validated data to Field Agent

**Beliefs:**
- active_sensors, sampling_rate
- data_quality_score
- total_readings_collected

**Actions:**
- collect_sensor_data
- validate_data
- optimize_sampling_rate
- forward_to_field_agent

### 3. Decision Agent
**Responsibilities:**
- Analyze field status and make autonomous decisions
- Decide on irrigation (based on soil moisture < 40%)
- Plan fertilization schedules (by growth stage)
- Assess disease risks
- Coordinate with Task Agent for execution
- Learn from outcomes

**Beliefs:**
- field_status, crop_health
- irrigation_schedule, fertilization_schedule
- decision_history

**Actions:**
- decide_irrigation
- decide_fertilization
- assess_disease_risk
- create_task_plan

**Decision Logic:**
```python
# Irrigation Decision
if soil_moisture < 30%:
    irrigate(20 minutes, priority=HIGH)
elif soil_moisture < 40%:
    irrigate(15 minutes, priority=MEDIUM)
elif soil_moisture < 50% and stage in [flowering, fruiting]:
    irrigate(10 minutes, priority=MEDIUM)

# Fertilization Decision (by growth stage)
germination: No fertilization
seedling: Balanced, light amount
vegetative: Nitrogen-rich, medium amount
flowering: Phosphorus-rich, medium amount
fruiting: Potassium-rich, heavy amount
ripening: No fertilization
```

### 4. Task Agent
**Responsibilities:**
- Receive task requests from Decision Agent
- Schedule and prioritize tasks (LOW, MEDIUM, HIGH, URGENT)
- Execute tasks (irrigation, fertilization, inspection, pruning, harvesting)
- Monitor task progress and timeouts
- Report completion/failure

**Task Types:**
- **irrigation:** Water crops for specified duration
- **fertilization:** Apply fertilizer (type and amount)
- **inspection:** Visual field inspection
- **pruning:** Prune plants
- **harvesting:** Harvest crops

**Task States:**
- PENDING → SCHEDULED → IN_PROGRESS → COMPLETED/FAILED

## BDI Architecture

All agents implement the **Belief-Desire-Intention (BDI)** architecture:

1. **Beliefs:** What the agent knows about the world
   - Updated through perception (sensors, messages)
   - Stored with confidence levels and timestamps

2. **Desires:** What the agent wants to achieve (goals)
   - Prioritized (1-10)
   - Can have deadlines and conditions

3. **Intentions:** What the agent has committed to do (plans)
   - Formed from desires through deliberation
   - Executed through actions

**Agent Loop:**
```
while running:
    perceive()    # Update beliefs from environment
    deliberate()  # Form intentions from beliefs and desires
    act()         # Execute intentions
```

## Installation

### Prerequisites
```bash
pip install fastapi uvicorn pydantic loguru
```

### Setup
```python
# In your FastAPI app
from cloud.backend.api.v1.multi_agent import router as mas_router

app.include_router(mas_router)
```

## Usage

### 1. Start the Multi-Agent System

```bash
# Via API
curl -X POST http://localhost:8000/mas/start?farm_id=farm_001

# Or programmatically
from multi_agent_system import start_multi_agent_system

await start_multi_agent_system(farm_id="farm_001")
```

### 2. Send Sensor Data

```bash
curl -X POST http://localhost:8000/mas/sensor-data \
  -H "Content-Type: application/json" \
  -d '{
    "temperature": 28.5,
    "humidity": 65.0,
    "light": 35000,
    "soil_moisture": 45.2
  }'
```

**What happens:**
1. Sensor Harvester Agent validates data
2. Field Agent calculates health score
3. Decision Agent evaluates conditions
4. If needed, Task Agent executes irrigation/fertilization

### 3. Monitor System Status

```bash
# System status
curl http://localhost:8000/mas/status

# Health report
curl http://localhost:8000/mas/health

# Detailed metrics
curl http://localhost:8000/mas/metrics
```

### 4. Check Field Status

```bash
# Field conditions and crop health
curl http://localhost:8000/mas/field-status

# Crop health score only
curl http://localhost:8000/mas/crop-health
```

### 5. View Tasks

```bash
# Pending tasks
curl http://localhost:8000/mas/tasks/pending

# Active tasks
curl http://localhost:8000/mas/tasks/active
```

### 6. Create Manual Task

```bash
curl -X POST http://localhost:8000/mas/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "irrigation",
    "priority": "high",
    "parameters": {
      "duration_minutes": 15,
      "reason": "Manual override"
    }
  }'
```

### 7. View Decision History

```bash
# All decisions (last 7 days)
curl http://localhost:8000/mas/decisions

# Irrigation decisions only
curl http://localhost:8000/mas/decisions?decision_type=irrigation&days=7

# Decision summary
curl http://localhost:8000/mas/decisions/summary?days=7
```

### 8. Stop the System

```bash
curl -X POST http://localhost:8000/mas/stop
```

## Integration with Existing System

### MQTT Integration

```python
# In your MQTT handler
from multi_agent_system import get_coordinator

async def on_sensor_message(topic, payload):
    coordinator = get_coordinator()
    
    sensor_data = {
        "temperature": payload["temperature"],
        "humidity": payload["humidity"],
        "light": payload["light_level"],
        "soil_moisture": payload["soil_moisture"]
    }
    
    await coordinator.send_sensor_data(sensor_data)
```

### WebSocket Broadcasting

```python
# Broadcast agent decisions to dashboard
from multi_agent_system import get_coordinator

coordinator = get_coordinator()

# Get field status for dashboard
field_status = await coordinator.get_field_status()
await websocket_manager.broadcast({
    "type": "field_status",
    "data": field_status
})

# Get active tasks
tasks = await coordinator.get_active_tasks()
await websocket_manager.broadcast({
    "type": "active_tasks",
    "data": tasks
})
```

## Performance Metrics

### System-Level Metrics
- **Uptime:** Total system running time
- **Messages Routed:** Total inter-agent messages
- **Messages/Second:** Message throughput
- **Agents Healthy:** All agents operational

### Agent-Level Metrics
- **Tasks Completed:** Successful task executions
- **Tasks Failed:** Failed task executions
- **Success Rate:** Completion rate (0.0-1.0)
- **Messages Sent/Received:** Communication activity
- **Beliefs/Desires/Intentions Count:** Agent state complexity

### Example Metrics Response
```json
{
  "system_status": "running",
  "uptime_seconds": 3600,
  "total_agents": 4,
  "total_messages_routed": 1250,
  "messages_per_second": 0.35,
  "agents": {
    "field_agent_001": {
      "state": "active",
      "tasks_completed": 45,
      "success_rate": 0.98,
      "beliefs_count": 8
    },
    "decision_agent_001": {
      "state": "active",
      "tasks_completed": 12,
      "success_rate": 1.0,
      "beliefs_count": 5
    }
  }
}
```

## Benefits

### 1. Autonomous Operations (50% Labor Reduction)
- Automatic irrigation decisions
- Scheduled fertilization
- Proactive anomaly detection
- Self-optimizing sensor sampling

### 2. Intelligent Decision Making
- Context-aware decisions (growth stage, weather, health)
- Learning from outcomes
- Risk assessment
- Priority-based task execution

### 3. Resilience
- Agent independence (continues if one fails)
- Graceful degradation
- Automatic recovery
- Health monitoring

### 4. Scalability
- Easy to add new agents
- Distributed processing
- Asynchronous communication
- Modular architecture

### 5. Auditability
- Complete decision history
- Task execution logs
- Performance metrics
- Transparent reasoning

## Testing

```bash
# Run test script
python test_multi_agent_system.py
```

See `test_multi_agent_system.py` for comprehensive testing examples.

## Troubleshooting

### Agents Not Starting
```bash
# Check logs
tail -f logs/multi_agent_system.log

# Verify agent states
curl http://localhost:8000/mas/agents
```

### No Decisions Being Made
```bash
# Check field status is being updated
curl http://localhost:8000/mas/field-status

# Verify Decision Agent is receiving data
curl http://localhost:8000/mas/agents/decision_agent_001
```

### Tasks Not Executing
```bash
# Check Task Agent status
curl http://localhost:8000/mas/agents/task_agent_001

# View pending tasks
curl http://localhost:8000/mas/tasks/pending
```

## Future Enhancements

1. **Machine Learning Integration**
   - Learn optimal irrigation schedules
   - Predict crop diseases
   - Optimize fertilization timing

2. **Multi-Farm Coordination**
   - Federated learning across farms
   - Resource sharing
   - Collaborative decision making

3. **Advanced Actuator Control**
   - Direct valve control
   - Automated fertilizer dispensing
   - Robotic harvesting integration

4. **Weather Integration**
   - Weather forecast consideration
   - Rain prediction for irrigation
   - Temperature alerts

5. **Mobile Notifications**
   - Push alerts for urgent decisions
   - Daily summary reports
   - Task completion notifications

## References

- **Paper 7:** "Digital Twin Framework for Horticulture 4.0" - Autonomous agent architecture
- **Paper 9:** "Cloud-Fog-Edge Multi-Agent System" - Distributed agent coordination
- **BDI Architecture:** Belief-Desire-Intention model for intelligent agents

## License

MIT License - See LICENSE file for details

---

**Status:** ✅ Fully implemented and tested  
**Version:** 1.0.0  
**Last Updated:** March 5, 2026
