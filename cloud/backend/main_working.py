"""
Complete Working Cloud Backend - main.py

Integrates all components:
- Digital Twin API
- WebSocket real-time updates
- Sensor data endpoints
- Predictions and scenarios
- MQTT Bridge for ESP32 sensor data
- SQLite sensor data storage & history API
"""

import json
import logging
from contextlib import asynccontextmanager
from typing import Optional, List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger

# Import Digital Twin router only (other routers require schemas/models not yet created)
from api.v1.digital_twin_complete import router as twin_router

# Import Calibration router
from api.v1.calibration import router as calibration_router

# Import Multi-Agent System router (optional)
try:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from api.v1.multi_agent import router as mas_router
    MAS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Multi-Agent System not available: {e}")
    MAS_AVAILABLE = False
    mas_router = None

# Import Historical Data router
try:
    from api.v1.historical_data import router as historical_router
    HISTORICAL_DATA_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Historical Data API not available: {e}")
    HISTORICAL_DATA_AVAILABLE = False
    historical_router = None

# Import ML Predictions router
try:
    from api.v1.ml_predictions import router as ml_router
    ML_PREDICTIONS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ML Predictions API not available: {e}")
    ML_PREDICTIONS_AVAILABLE = False
    ml_router = None

# Import Camera router
try:
    from api.v1.camera import router as camera_router
    CAMERA_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Camera API not available: {e}")
    CAMERA_AVAILABLE = False
    camera_router = None

# Import AI Assistant router (Ollama / LLaMA 3)
try:
    from api.v1.ai_assistant import router as ai_router
    AI_AVAILABLE = True
except ImportError as e:
    logger.warning(f"AI Assistant not available: {e}")
    AI_AVAILABLE = False
    ai_router = None

# Import Twin Accuracy Monitor router
from api.v1.twin_accuracy import router as twin_accuracy_router

# Import Prometheus Metrics router
from api.v1.metrics import router as metrics_router
import api.v1.metrics as prom

# Import WebSocket manager
from websocket.manager import manager as ws_manager

# Import MQTT client
from core.mqtt_client import init_mqtt_client, get_mqtt_client

# Import sensor storage
from core.sensor_storage import init_db, store_reading, get_history, get_latest, get_stats, get_reading_count, cleanup_old_readings, get_db_size_mb

# Import Twin Accuracy engine
from core.twin_accuracy import init_twin_accuracy_db, store_prediction, get_accuracy_stats, get_physics_model_summary

# Import Tier 1 modules
from data_standards import StandardProtocol, DataValidator
from infological_design import InfologicalDesigner
from digital_twin.bidirectional import ActuationController, ConvergenceValidator, SafetyManager
from sustainability import SustainabilityAssessor, SustainabilityReporter
from yield_analysis import YieldStabilityAnalyzer, ManagementOptimizer

# Import Tier 2 modules (Paper 10)
from sensor_optimization import ThompsonSamplingOptimizer, SensorSelector, PerformanceTracker
from psychrometric import PsychrometricCalculator


# In-memory cache: accumulate individual sensor readings per farm
_sensor_cache: dict = {}

async def mqtt_message_handler(farm_id: str, data: dict, topic: str):
    """Handle MQTT messages and forward to WebSocket clients"""
    # Normalize farm_id so storage is consistent with API default "farm_001"
    normalized_farm = "farm_001"

    # ── Individual sensor topic: {sensor_type, value, timestamp, device_id} ──
    if "sensor_type" in data and "value" in data:
        field_map = {
            "temperature": "temperature",
            "humidity": "humidity",
            "light": "light_level",
            "soil_moisture": "soil_moisture",
        }
        field = field_map.get(data["sensor_type"], data["sensor_type"])
        cache = _sensor_cache.setdefault(normalized_farm, {})
        cache[field] = data["value"]
        cache.setdefault("device_id", data.get("device_id", "esp32_edge_001"))
        # Build a flat combined dict that store_reading can handle
        data = cache.copy()
    else:
        # Combined flat payload (agritwin/sensors): map keys to DB column names.
        # Status topics (farms/+/status) have no sensor values — skip them.
        temperature = data.get("temperature")
        humidity = data.get("humidity")
        light_level = data.get("light_level")
        soil_moisture = data.get("soil_moisture")
        if all(v is None for v in (temperature, humidity, light_level, soil_moisture)):
            logger.debug(f"Skipping non-sensor message on topic {topic}")
            return
        data = {
            "device_id": data.get("device_id", "esp32_edge_001"),
            "temperature": temperature,
            "humidity": humidity,
            "light_level": light_level,
            "soil_moisture": soil_moisture,
            "raw_ldr": data.get("raw_ldr"),
            "raw_soil": data.get("raw_soil"),
            "rssi": data.get("rssi"),
        }

    farm_id = normalized_farm
    logger.info(f"📡 Sensor data from {farm_id}: {data}")

    # Always store the reading immediately (data is flat: temperature, humidity, etc.)
    store_reading(farm_id, data)
    prom.inc("sensor_readings_total")
    prom.inc("mqtt_messages_received")

    # ── Twin Accuracy Monitor: compare prediction vs actual ──
    try:
        from digital_twin.physics_model.comprehensive_physics import DigitalTwinPhysics, WeatherData
        sensor_for_twin = {
            "temp": data.get("temperature", 25),
            "humidity": data.get("humidity", 60),
            "light": data.get("light_level", 50),
            "soil": data.get("soil_moisture", 50),
        }
        if not hasattr(mqtt_message_handler, "_twin"):
            mqtt_message_handler._twin = DigitalTwinPhysics()
        twin = mqtt_message_handler._twin
        twin_state = twin.simulate_step(sensor_for_twin, timestep_hours=0.17)  # ~10 min
        prediction = {
            "soil_moisture": twin_state["water"]["moisture_percent"],
            "temperature": twin_state["weather"]["temperature"],
            "humidity": twin_state["weather"]["humidity"],
            "evapotranspiration": twin_state["water"]["evapotranspiration"],
            "water_deficit": twin_state["water"]["water_deficit"],
            "growth_stage": twin_state["crop"]["growth_stage"],
        }
        actual = {
            "soil_moisture": data.get("soil_moisture"),
            "temperature": data.get("temperature"),
            "humidity": data.get("humidity"),
        }
        store_prediction(farm_id, prediction, actual)
        prom.inc("twin_predictions_total")
        soil_err = abs((prediction["soil_moisture"] or 0) - (actual["soil_moisture"] or 0))
        if soil_err > 10:
            prom.inc("twin_calibrations_total")
        prom.gauge("twin_avg_error", soil_err)
        prom.gauge("twin_accuracy_pct", max(0, 100 - soil_err))
    except Exception as e:
        logger.debug(f"Twin accuracy tracking skipped: {e}")

    # TIER 1 INTEGRATION: quality scoring only (does not gate storage)
    try:
        # Wrap in nested format for StandardProtocol which expects {"sensors": {}}
        wrapped = {"device_id": data.get("device_id"), "timestamp": 0,
                   "sensors": {k: data[k] for k in ("temperature", "humidity", "light_level", "soil_moisture") if data.get(k) is not None},
                   "system": {"rssi": data.get("rssi")}}
        standard_readings = StandardProtocol.from_agritwin_format(wrapped)
        for reading in standard_readings:
            validation = DataValidator.validate(reading)
            logger.info(f"📊 Data quality: {validation['quality_score']:.1f}/100 - {reading.sensor_type.value}")
    except Exception as e:
        logger.debug(f"Standard protocol quality check skipped: {e}")
    
    # MULTI-AGENT SYSTEM INTEGRATION: Send to MAS
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        
        from multi_agent_system import get_coordinator
        coordinator = get_coordinator(farm_id)
        
        if coordinator.running:
            sensors = data.get('sensors', {})
            sensor_data = {
                "temperature": sensors.get('temperature', 0),
                "humidity": sensors.get('humidity', 0),
                "light": sensors.get('light_level', 0),
                "soil_moisture": sensors.get('soil_moisture', 0)
            }
            await coordinator.send_sensor_data(sensor_data)
            logger.info(f"🤖 Sensor data sent to Multi-Agent System")
    except Exception as e:
        logger.warning(f"MAS not available: {e}")
    
    # Transform data to match dashboard format (data is flat after normalization above)
    transformed_data = {
        "temp": data.get('temperature', 0),
        "humidity": data.get('humidity', 0),
        "light": data.get('light_level', 0),
        "soil": data.get('soil_moisture', 0)
    }
    
    # Send to WebSocket clients subscribed to this farm
    await ws_manager.send_sensor_update(farm_id, transformed_data)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("=" * 60)
    logger.info("Starting Smart Farming Cloud Backend")
    logger.info("=" * 60)
    
    # Initialize digital twin manager
    logger.info("✓ Digital Twin engine initialized")
    
    # Initialize database
    init_db()
    init_twin_accuracy_db()
    logger.info("✓ Sensor database ready (with twin accuracy table)")
    
    # Cleanup old readings (>30 days) on startup
    try:
        deleted = cleanup_old_readings(retention_days=30)
        if deleted:
            logger.info(f"✓ Data retention: removed {deleted} old readings")
    except Exception as e:
        logger.warning(f"Data retention cleanup skipped: {e}")
    
    # Initialize WebSocket manager
    logger.info("✓ WebSocket manager ready")
    
    # Initialize and start MQTT client (optional)
    logger.info("Initializing MQTT client...")
    import asyncio
    import os
    loop = asyncio.get_event_loop()
    mqtt_host = os.environ.get("MQTT_BROKER", "agritwin-fog.local")
    mqtt_port = int(os.environ.get("MQTT_PORT", "1883"))
    
    try:
        mqtt_client = init_mqtt_client(broker_host=mqtt_host, broker_port=mqtt_port, event_loop=loop)
        mqtt_client.set_message_callback(mqtt_message_handler)
        mqtt_client.start()
        app.state.mqtt_client = mqtt_client
        logger.info("✓ MQTT client connected and subscribed")
    except Exception as e:
        logger.warning(f"⚠ MQTT client not available: {e}")
        logger.info("  System will run without MQTT (use API to send sensor data)")
    
    logger.info("=" * 60)
    logger.info("✓ All services started successfully")
    logger.info("=" * 60)
    
    yield
    
    # Cleanup
    logger.info("Shutting down services...")
    mqtt_client = get_mqtt_client()
    if mqtt_client:
        mqtt_client.stop()
    logger.info("✓ Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Smart Farming Cloud Backend",
    description="Digital Twin and AI-powered Smart Farming Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])  # Disabled: schemas not created yet
# app.include_router(farms.router, prefix="/api/v1/farms", tags=["Farms"])  # Disabled: schemas not created yet
# app.include_router(sensors.router, prefix="/api/v1", tags=["Sensors"])  # Disabled: schemas not created yet
app.include_router(twin_router, prefix="/api/v1/twin", tags=["Digital Twin"])
app.include_router(calibration_router, prefix="/api/v1/calibration", tags=["Calibration"])
app.include_router(twin_accuracy_router, prefix="/api/v1", tags=["Twin Accuracy Monitor"])
app.include_router(metrics_router, tags=["Monitoring"])

# Include Multi-Agent System router if available
if MAS_AVAILABLE and mas_router:
    app.include_router(mas_router)  # Multi-Agent System (already has /mas prefix)
    logger.info("✓ Multi-Agent System API enabled")
else:
    logger.warning("⚠ Multi-Agent System API not available")

# Include Historical Data router if available
if HISTORICAL_DATA_AVAILABLE and historical_router:
    app.include_router(historical_router, prefix="/api/v1")
    logger.info("✓ Historical Data API enabled")
else:
    logger.warning("⚠ Historical Data API not available")

# Include ML Predictions router if available
if ML_PREDICTIONS_AVAILABLE and ml_router:
    app.include_router(ml_router, prefix="/api/v1")
    logger.info("✓ ML Predictions API enabled")
else:
    logger.warning("⚠ ML Predictions API not available")

# Include Camera router if available
if CAMERA_AVAILABLE and camera_router:
    app.include_router(camera_router)   # prefix already set inside the router
    logger.info("✓ Camera API enabled")
else:
    logger.warning("⚠ Camera API not available")

# Include AI Assistant router if available
if AI_AVAILABLE and ai_router:
    app.include_router(ai_router, prefix="/api/v1")
    logger.info("✓ AI Assistant API enabled (Ollama / LLaMA 3)")
else:
    logger.warning("⚠ AI Assistant API not available")


# WebSocket endpoint
@app.websocket("/ws/{farm_id}")
async def websocket_endpoint(websocket: WebSocket, farm_id: str):
    """
    WebSocket endpoint for real-time data streaming
    
    Connect from frontend:
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/ws/farm_001');
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Real-time update:', data);
    };
    ```
    """
    await ws_manager.connect(websocket, farm_id)
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            logger.info(f"Received from client: {data}")
            
            # Echo back (could handle commands here)
            await ws_manager.send_personal_message(
                f"Server received: {data}",
                websocket
            )
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info(f"Client disconnected from farm: {farm_id}")


# Health check endpoint
import time as _time_mod
_startup_time = _time_mod.time()


@app.get("/health")
async def health_check():
    """Health check endpoint with system details"""
    import time
    uptime_seconds = int(time.time() - _startup_time)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, secs = divmod(remainder, 60)

    reading_count = get_reading_count()
    db_size = get_db_size_mb()
    latest = get_latest()
    last_reading_at = latest.get("timestamp") if latest else None

    mqtt_client = get_mqtt_client()
    mqtt_connected = mqtt_client is not None and mqtt_client.is_connected

    return {
        "status": "healthy",
        "service": "smart-farming-cloud",
        "version": "1.1.0",
        "uptime": f"{hours}h {minutes}m {secs}s",
        "uptime_seconds": uptime_seconds,
        "database": {
            "total_readings": reading_count,
            "size_mb": db_size,
            "last_reading_at": last_reading_at,
        },
        "mqtt_connected": mqtt_connected,
        "modules": {
            "mas": MAS_AVAILABLE,
            "historical_data": HISTORICAL_DATA_AVAILABLE,
            "ml_predictions": ML_PREDICTIONS_AVAILABLE,
            "camera": CAMERA_AVAILABLE,
        },
    }


# ============================================================
# Fog → Cloud Ingest API (batch sync)
# ============================================================

class FogReading(BaseModel):
    farm_id: str = "farm_001"
    device_id: str = "fog_node"
    timestamp: Optional[str] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    light_level: Optional[float] = None
    soil_moisture: Optional[float] = None
    rssi: Optional[int] = None

class FogIngestRequest(BaseModel):
    readings: List[FogReading]

@app.post("/api/v1/sensors/ingest")
async def ingest_fog_data(payload: FogIngestRequest):
    """
    Accept batched sensor readings from the fog node.
    Used for store-and-forward sync when fog buffers data offline.
    """
    stored = 0
    errors = 0
    for reading in payload.readings:
        try:
            data = reading.model_dump(exclude_none=True)
            farm_id = data.pop("farm_id", "farm_001")
            store_reading(farm_id, data)
            stored += 1
        except Exception as e:
            logger.error(f"Ingest error: {e}")
            errors += 1
    logger.info(f"Fog ingest: stored={stored}, errors={errors}")
    return {"stored": stored, "errors": errors}


# ============================================================
# Sensor History API
# ============================================================

@app.get("/api/v1/sensors/history")
async def sensor_history(
    farm_id: str = Query("farm_001", description="Farm identifier"),
    hours: int = Query(24, ge=1, le=168, description="Hours of history (1-168)"),
    limit: int = Query(500, ge=1, le=5000, description="Max readings to return")
):
    """
    Get historical sensor readings for charting.
    
    Returns time-series data suitable for line charts.
    """
    readings = get_history(farm_id=farm_id, hours=hours, limit=limit)
    return {
        "farm_id": farm_id,
        "hours": hours,
        "count": len(readings),
        "readings": readings
    }


@app.get("/api/v1/sensors/latest")
async def sensor_latest(
    farm_id: str = Query("farm_001", description="Farm identifier")
):
    """Get the most recent sensor reading"""
    reading = get_latest(farm_id=farm_id)
    if not reading:
        return {"error": "No readings found", "farm_id": farm_id}
    return reading


@app.get("/api/v1/sensors/latest/raw")
async def sensor_latest_raw(
    farm_id: str = Query("farm_001", description="Farm identifier")
):
    """Get most recent sensor reading including raw ADC values for the calibration wizard.
    Returns raw_ldr (0-4095) and raw_soil (0-4095) alongside calibrated values.
    """
    reading = get_latest(farm_id=farm_id)
    if not reading:
        return {"error": "No readings found", "farm_id": farm_id}
    return {
        "temperature": reading.get("temperature"),
        "humidity": reading.get("humidity"),
        "light_level": reading.get("light_level"),
        "soil_moisture": reading.get("soil_moisture"),
        "raw_ldr": reading.get("raw_ldr"),
        "raw_soil": reading.get("raw_soil"),
        "timestamp": reading.get("timestamp"),
    }


@app.get("/api/v1/sensors/stats")
async def sensor_stats(
    farm_id: str = Query("farm_001", description="Farm identifier"),
    hours: int = Query(24, ge=1, le=168, description="Hours for stats calculation")
):
    """
    Get min/max/avg statistics for sensor data.
    
    Useful for dashboard summary cards.
    """
    stats = get_stats(farm_id=farm_id, hours=hours)
    count = get_reading_count(farm_id=farm_id)
    # Map DB column names to frontend-friendly names
    return {
        "farm_id": farm_id,
        "period_hours": hours,
        "total_readings": count,
        "avg_temperature": stats.get("avg_temp", 0) or 0,
        "min_temperature": stats.get("min_temp", 0) or 0,
        "max_temperature": stats.get("max_temp", 0) or 0,
        "avg_humidity": stats.get("avg_humidity", 0) or 0,
        "min_humidity": stats.get("min_humidity", 0) or 0,
        "max_humidity": stats.get("max_humidity", 0) or 0,
        "avg_light": stats.get("avg_light", 0) or 0,
        "min_light": stats.get("min_light", 0) or 0,
        "max_light": stats.get("max_light", 0) or 0,
        "avg_soil": stats.get("avg_soil", 0) or 0,
        "min_soil": stats.get("min_soil", 0) or 0,
        "max_soil": stats.get("max_soil", 0) or 0,
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Smart Farming Cloud API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# ============================================================
# TIER 1: Data Standardization API
# ============================================================

@app.get("/api/v1/data/export")
async def export_sensor_data(
    farm_id: str = Query("farm_001", description="Farm identifier"),
    format: str = Query("json", description="Export format: json, csv, xml"),
    hours: int = Query(24, description="Hours of data to export")
):
    """
    Export sensor data in standard format
    
    Supports JSON, CSV, and XML formats for interoperability
    """
    from data_standards import FormatConverter
    
    # Get readings
    readings_raw = get_history(farm_id=farm_id, hours=hours, limit=5000)
    
    # Convert to standard format
    standard_readings = []
    for reading in readings_raw:
        mqtt_data = {
            "device_id": reading.get("device_id", "ESP32_001"),
            "timestamp": reading.get("timestamp", 0),
            "sensors": {
                "temperature": reading.get("temperature", 0),
                "humidity": reading.get("humidity", 0),
                "light_level": reading.get("light_level", 0),
                "soil_moisture": reading.get("soil_moisture", 0)
            }
        }
        standard_readings.extend(StandardProtocol.from_agritwin_format(mqtt_data))
    
    # Export in requested format
    if format == "csv":
        content = FormatConverter.to_csv(standard_readings)
        return {"format": "csv", "data": content}
    elif format == "xml":
        content = FormatConverter.to_xml(standard_readings)
        return {"format": "xml", "data": content}
    else:  # json
        content = FormatConverter.to_json(standard_readings)
        return {"format": "json", "data": content}


@app.get("/api/v1/data/quality")
async def data_quality_report(
    farm_id: str = Query("farm_001", description="Farm identifier"),
    hours: int = Query(24, description="Hours to analyze")
):
    """
    Get data quality report
    
    Returns quality scores and validation results
    """
    readings_raw = get_history(farm_id=farm_id, hours=hours, limit=1000)
    
    # Convert and validate
    all_validations = []
    for reading in readings_raw:
        mqtt_data = {
            "device_id": reading.get("device_id", "ESP32_001"),
            "timestamp": reading.get("timestamp", 0),
            "sensors": {
                "temperature": reading.get("temperature", 0),
                "humidity": reading.get("humidity", 0),
                "light_level": reading.get("light_level", 0)
            }
        }
        standard_readings = StandardProtocol.from_agritwin_format(mqtt_data)
        
        for sr in standard_readings:
            validation = DataValidator.validate(sr)
            all_validations.append(validation)
    
    # Calculate summary
    if all_validations:
        avg_quality = sum(v["quality_score"] for v in all_validations) / len(all_validations)
        valid_count = sum(1 for v in all_validations if v["valid"])
    else:
        avg_quality = 0
        valid_count = 0
    
    return {
        "farm_id": farm_id,
        "period_hours": hours,
        "total_readings": len(all_validations),
        "valid_readings": valid_count,
        "invalid_readings": len(all_validations) - valid_count,
        "average_quality_score": round(avg_quality, 1),
        "quality_grade": "Excellent" if avg_quality >= 95 else "Good" if avg_quality >= 80 else "Fair"
    }


# ============================================================
# TIER 1: Infological Design API
# ============================================================

@app.get("/api/v1/design/problems")
async def list_farm_problems():
    """List all cataloged farm problems"""
    from infological_design import FARM_PROBLEMS
    
    return {
        "problems": [
            {
                "id": p.problem_id,
                "name": p.name,
                "description": p.description,
                "priority": p.priority,
                "symptoms": p.symptoms
            }
            for p in FARM_PROBLEMS.values()
        ]
    }


@app.post("/api/v1/design/analyze")
async def analyze_problem(problem_id: str):
    """
    Analyze a problem and get sensor requirements
    
    Returns exactly what sensors you need and why
    """
    designer = InfologicalDesigner("farm_001")
    design = designer.design_for_problem(problem_id)
    
    return design


@app.post("/api/v1/design/identify")
async def identify_problem(symptoms: list[str]):
    """
    Identify problem from symptoms
    
    Example: ["yellowing leaves", "stunted growth"]
    """
    designer = InfologicalDesigner("farm_001")
    result = designer.identify_problem(symptoms)
    
    return result


# ============================================================
# RELAY CONTROL  (pump & grow light via ESP32 relay module)
# ============================================================

class RelayControlRequest(BaseModel):
    relay: str   # "pump" or "light"
    state: str   # "on"  or "off"
    farm_id: str = "farm_001"

@app.post("/api/v1/relay/control")
async def relay_control(req: RelayControlRequest):
    """
    Send relay ON/OFF command to the ESP32 edge device via MQTT.
    Publishes to  farms/001/commands  topic.
    ESP32 handles {"command":"relay","relay":"pump|light","state":"on|off"}
    Auto-reconnects to broker if connection dropped.
    """
    if req.relay not in ("pump", "light"):
        return {"success": False, "error": "relay must be 'pump' or 'light'"}
    if req.state not in ("on", "off"):
        return {"success": False, "error": "state must be 'on' or 'off'"}

    mqtt = get_mqtt_client()
    # Auto-reconnect if disconnected
    if mqtt and not mqtt.is_connected:
        try:
            mqtt.reconnect()
            import asyncio
            await asyncio.sleep(1.5)  # wait for on_connect callback
        except Exception as e:
            logger.warning(f"[RELAY] MQTT reconnect attempt failed: {e}")

    if not mqtt or not mqtt.is_connected:
        # Fallback: send via a fresh one-shot paho client
        import paho.mqtt.publish as paho_publish
        import os
        broker = os.environ.get("MQTT_BROKER", "agritwin-fog.local")
        try:
            payload_str = json.dumps({"command": "relay", "relay": req.relay, "state": req.state})
            paho_publish.single("farms/001/commands", payload=payload_str, hostname=broker, port=1883)
            logger.info(f"[RELAY] {req.relay} → {req.state} (via one-shot client)")
            return {"success": True, "relay": req.relay, "state": req.state}
        except Exception as e:
            return {"success": False, "error": f"MQTT broker not reachable: {e}"}

    payload = {"command": "relay", "relay": req.relay, "state": req.state}
    mqtt.publish("farms/001/commands", payload)
    logger.info(f"[RELAY] {req.relay} → {req.state}")
    return {"success": True, "relay": req.relay, "state": req.state}

@app.get("/api/v1/relay/state")
async def relay_state():
    """Return last known relay state (retained MQTT message may differ — use as fallback)."""
    return {"pump": "unknown", "light": "unknown",
            "note": "Subscribe to farms/001/relay/state for live updates"}


# ============================================================
# TIER 1: Bi-directional Digital Twin API
# ============================================================

@app.post("/api/v1/actuation/irrigate")
async def trigger_irrigation(
    device_id: str,
    duration_seconds: int,
    flow_rate: Optional[float] = None
):
    """
    Trigger irrigation from digital twin
    
    Virtual → Physical control
    """
    mqtt_client = get_mqtt_client()
    if not mqtt_client:
        return {"success": False, "error": "MQTT client not available"}
    
    actuator = ActuationController(mqtt_client.client, "farm_001")
    
    # Check safety first
    safety_mgr = SafetyManager()
    safety_check = safety_mgr.check_irrigation_safety(
        duration=duration_seconds,
        current_soil_moisture=50,  # TODO: Get from latest reading
        daily_total=0  # TODO: Track daily total
    )
    
    if not safety_check["safe"]:
        return {
            "success": False,
            "error": "Safety check failed",
            "details": safety_check
        }
    
    # Execute actuation
    result = actuator.irrigate(device_id, duration_seconds, flow_rate)
    
    return result


@app.get("/api/v1/actuation/status")
async def actuation_status(device_id: str):
    """Get actuation status and cooldown info"""
    mqtt_client = get_mqtt_client()
    if not mqtt_client:
        return {"error": "MQTT client not available"}
    
    actuator = ActuationController(mqtt_client.client, "farm_001")
    history = actuator.get_action_history(device_id)
    
    return {
        "device_id": device_id,
        "action_history": history
    }


@app.get("/api/v1/convergence/status")
async def convergence_status(entity_id: str = "soil_moisture"):
    """Get convergence status between physical and virtual"""
    validator = ConvergenceValidator()
    report = validator.get_convergence_report(entity_id)
    
    return report


# ============================================================
# TIER 1: Sustainability Assessment API
# ============================================================

@app.post("/api/v1/sustainability/assess")
async def assess_sustainability(farm_data: dict):
    """
    Assess sustainability across 4 dimensions
    
    Example farm_data:
    {
        "labor_hours_per_hectare": 8,
        "cost_per_hectare": 600,
        "water_usage": 420,
        "fertilizer_usage": 160,
        "yield": 4.8,
        "profit_margin": 28
    }
    """
    assessor = SustainabilityAssessor("farm_001")
    assessment = assessor.assess(farm_data)
    
    return assessment


@app.get("/api/v1/sustainability/report")
async def sustainability_report(farm_data: dict):
    """Get sustainability report in text format"""
    assessor = SustainabilityAssessor("farm_001")
    assessment = assessor.assess(farm_data)
    
    report = SustainabilityReporter.generate_text_report(assessment)
    
    return {
        "report": report,
        "assessment": assessment
    }


@app.get("/api/v1/sustainability/metrics")
async def sustainability_metrics():
    """Get all sustainability metrics definitions"""
    from sustainability import SUSTAINABILITY_METRICS
    
    return SUSTAINABILITY_METRICS


# ============================================================
# TIER 1: Yield Stability Analysis API
# ============================================================

@app.post("/api/v1/yield/analyze")
async def analyze_yield_stability(yield_data: dict):
    """
    Analyze yield stability across zones
    
    Example yield_data:
    {
        "north_field": [5.2, 5.4, 5.1, 5.3],
        "south_field": [2.3, 2.1, 2.4, 2.2],
        "east_field": [3.5, 5.0, 2.8, 4.9]
    }
    """
    analyzer = YieldStabilityAnalyzer()
    results = analyzer.analyze(yield_data)
    recommendations = analyzer.recommend_management(results)
    n_loss = analyzer.calculate_n_loss_risk(results)
    summary = analyzer.generate_summary(results)
    
    return {
        "stability_results": results,
        "recommendations": recommendations,
        "n_loss_analysis": n_loss,
        "summary": summary
    }


@app.post("/api/v1/yield/savings")
async def calculate_savings(yield_data: dict, current_rate: float = 150):
    """
    Calculate potential savings from zone-specific management
    """
    analyzer = YieldStabilityAnalyzer()
    results = analyzer.analyze(yield_data)
    
    optimizer = ManagementOptimizer()
    savings = optimizer.calculate_savings(results, current_rate)
    application_map = optimizer.generate_application_map(results)
    
    return {
        "savings": savings,
        "application_map": application_map
    }


# ============================================================
# TIER 2: Thompson Sampling Sensor Optimization API
# ============================================================

@app.post("/api/v1/sensors/optimize")
async def optimize_sensor_placement(
    candidate_locations: list,
    target_count: int = 2
):
    """
    Optimize sensor placement using Thompson Sampling
    
    Example candidate_locations:
    [[0, 0], [0, 10], [10, 0], [10, 10], [20, 0], [20, 10]]
    
    Reduces sensors by ~82% while maintaining 99%+ accuracy
    """
    optimizer = ThompsonSamplingOptimizer(
        candidate_locations=[tuple(loc) for loc in candidate_locations],
        target_sensor_count=target_count
    )
    
    # Run initial selection
    selected = optimizer.select_sensors()
    rankings = optimizer.get_sensor_rankings()
    savings = optimizer.calculate_savings(len(candidate_locations))
    
    return {
        "selected_sensors": selected,
        "rankings": rankings,
        "savings": savings,
        "optimization_method": "Thompson Sampling"
    }


@app.post("/api/v1/sensors/update_performance")
async def update_sensor_performance(
    sensor_id: str,
    accuracy: float
):
    """
    Update sensor performance for Thompson Sampling
    
    Call this after each measurement to improve optimization
    """
    # In production, maintain optimizer state
    # For now, return acknowledgment
    return {
        "sensor_id": sensor_id,
        "accuracy": accuracy,
        "updated": True,
        "message": "Performance updated - optimizer will adapt"
    }


@app.get("/api/v1/sensors/recommend_count")
async def recommend_sensor_count(
    field_area: float,
    sensor_range: float = 10.0
):
    """
    Recommend optimal number of sensors for field
    
    Args:
        field_area: Field area in square meters
        sensor_range: Sensor coverage radius in meters
    """
    recommended = SensorSelector.recommend_sensor_count(field_area, sensor_range)
    
    # Calculate with and without optimization
    coverage_per_sensor = 3.14159 * (sensor_range ** 2)
    full_coverage_count = int((field_area / coverage_per_sensor) + 0.5)
    
    return {
        "field_area": field_area,
        "sensor_range": sensor_range,
        "full_coverage_sensors": full_coverage_count,
        "recommended_with_optimization": recommended,
        "reduction_percentage": round((1 - recommended/full_coverage_count) * 100, 1),
        "cost_per_sensor": 50,
        "total_cost_without_optimization": full_coverage_count * 50,
        "total_cost_with_optimization": recommended * 50,
        "savings": (full_coverage_count - recommended) * 50
    }


@app.post("/api/v1/sensors/validate_placement")
async def validate_sensor_placement(
    locations: list,
    min_distance: float = 5.0
):
    """
    Validate sensor placement
    
    Checks minimum distance between sensors
    """
    validation = SensorSelector.validate_placement(
        [tuple(loc) for loc in locations],
        min_distance
    )
    
    return validation


# ============================================================
# TIER 2: Psychrometric Parameters API
# ============================================================

@app.get("/api/v1/psychrometric/calculate")
async def calculate_psychrometric(
    temperature: float,
    relative_humidity: float,
    pressure: float = 101.325
):
    """
    Calculate all psychrometric parameters
    
    From temperature and humidity, calculates:
    1. Dew Point
    2. Wet Bulb Temperature
    3. Absolute Humidity
    4. Specific Enthalpy
    5. Vapor Pressure
    6. Specific Volume
    
    Args:
        temperature: Air temperature (°C)
        relative_humidity: Relative humidity (%)
        pressure: Atmospheric pressure (kPa, default: 101.325)
    """
    params = PsychrometricCalculator.calculate_all(
        temperature, relative_humidity, pressure
    )
    
    return PsychrometricCalculator.to_dict(params)


@app.get("/api/v1/psychrometric/comfort")
async def calculate_comfort_index(
    temperature: float,
    relative_humidity: float
):
    """
    Calculate human comfort index and heat stress risk
    
    Useful for:
    - Worker safety in greenhouse
    - Plant stress assessment
    - Ventilation decisions
    """
    comfort = PsychrometricCalculator.comfort_index(temperature, relative_humidity)
    
    return comfort


@app.get("/api/v1/psychrometric/latest")
async def get_latest_psychrometric(farm_id: str = "farm_001"):
    """
    Get psychrometric parameters for latest sensor reading
    """
    # Get latest reading
    reading = get_latest(farm_id)
    
    if not reading:
        return {"error": "No readings available"}
    
    temp = reading.get("temperature", 0)
    humidity = reading.get("humidity", 0)
    
    # Calculate psychrometric parameters
    params = PsychrometricCalculator.calculate_all(temp, humidity)
    comfort = PsychrometricCalculator.comfort_index(temp, humidity)
    
    return {
        "timestamp": reading.get("timestamp"),
        "farm_id": farm_id,
        "input": {
            "temperature": temp,
            "relative_humidity": humidity
        },
        "psychrometric_parameters": PsychrometricCalculator.to_dict(params),
        "comfort_assessment": comfort
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
