# System Architecture Documentation

## Table of Contents

1. [Overview](#overview)
2. [Layered Architecture](#layered-architecture)
3. [Data Flow](#data-flow)
4. [Digital Twin Architecture](#digital-twin-architecture)
5. [Scalability](#scalability)
6. [Security](#security)
7. [Naming Conventions](#naming-conventions)

## Overview

The Smart Farming Digital Twin System is a three-layered cyber-physical architecture:

- **EDGE**: ESP32/ESP8266 devices collecting sensor data
- **FOG**: Local gateway for preprocessing and buffering
- **CLOUD**: Backend services, digital twin engine, AI/ML models, and dashboard

## Layered Architecture

### Why Three Layers?

1. **Edge Layer**: Low latency local decision-making
2. **Fog Layer**: Reliability during internet outages
3. **Cloud Layer**: Unlimited compute for AI/simulation

### Edge Layer (ESP32/ESP8266)

**Purpose**: Real-time data collection and local actuation

**Components**:
- Sensor abstraction layer
- Calibration module
- MQTT client
- Power management
- OTA update system

**Design Decisions**:
- **Modular sensor design**: Easy to add new sensors
- **Calibration in EEPROM**: Persists across reboots
- **Deep sleep**: Extends battery life for remote deployments
- **Local buffering**: Handles temporary connectivity loss

### Fog Layer (Local Gateway)

**Purpose**: Edge intelligence and resilience

**Components**:
- MQTT broker (Mosquitto)
- Data validation engine
- Buffer manager (Redis + SQLite)
- Emergency control system
- Cloud sync service

**Design Decisions**:
- **Dual buffering**: Redis (hot) + SQLite (cold)
- **Autonomous control**: Can operate without cloud
- **Data validation**: Prevents bad data from reaching cloud
- **Gradual sync**: Bandwidth-efficient cloud synchronization

### Cloud Layer (Backend + Digital Twin)

**Purpose**: Advanced analytics, simulation, and optimization

**Components**:
- FastAPI backend
- InfluxDB (time-series)
- PostgreSQL (relational)
- Digital Twin Engine
- AI/ML inference
- React dashboard

**Design Decisions**:
- **Async architecture**: High concurrency with FastAPI
- **Time-series optimization**: InfluxDB for sensor data
- **Relational for metadata**: PostgreSQL for farms, users, etc.
- **Modular twin**: Separate physics, AI, and optimization modules

## Data Flow

### Real-time Sensor Data Flow

```
1. ESP32 Sensor Reading
   ↓
2. Calibration & Filtering
   ↓
3. MQTT Publish (Edge → Fog)
   ↓
4. Fog Validation & Buffering
   ↓
5. Cloud Sync (Fog → Cloud)
   ↓
6. InfluxDB Storage
   ↓
7. Digital Twin State Update
   ↓
8. WebSocket Push to Dashboard
```

### Command Flow (Cloud → Edge)

```
1. User Action on Dashboard
   ↓
2. REST API POST
   ↓
3. Validation & Authorization
   ↓
4. MQTT Publish (Cloud → Fog)
   ↓
5. Fog Emergency Check
   ↓
6. MQTT Forward (Fog → Edge)
   ↓
7. Edge Action Execution
   ↓
8. Confirmation MQTT
```

## Digital Twin Architecture

### State Synchronization Strategy

The digital twin maintains both **physical state** (from sensors) and **virtual state** (from simulation).

**Divergence Metric**:
```python
divergence = sqrt(mean((physical - virtual)² / range²))
```

When divergence > threshold (15%), the twin recalibrates.

### Physics-Based Models

1. **Soil Water Balance**
   - Inputs: Irrigation, Precipitation, ET₀
   - Outputs: Soil moisture prediction
   - Update: Every simulation step (5 min)

2. **Evapotranspiration (Penman-Monteith)**
   - Inputs: Temp, Humidity, Wind, Radiation
   - Outputs: Daily water loss
   - Standard: FAO-56

3. **Crop Growth (GDD)**
   - Inputs: Temperature
   - Outputs: Growth stage, biomass
   - Formula: GDD = Σ[(Tmax + Tmin)/2 - Tbase]

### AI/ML Models

1. **Yield Prediction (LSTM)**
   - Architecture: LSTM(128) → Dense(64) → Dense(1)
   - Input: 30-day sensor history
   - Output: Kg at harvest
   - Re-training: Weekly

2. **Anomaly Detection (Autoencoder)**
   - Architecture: [64,32,16] encoder, [16,32,64] decoder
   - Threshold: Reconstruction error > 2σ
   - Use: Equipment failure, pest/disease detection

3. **Optimization (Linear Programming)**
   - Solver: PuLP/OR-Tools
   - Objective: Minimize water/fertilizer
   - Constraints: Quality, yield targets

### Parallel Execution

**Real System** and **Digital Twin** run in parallel:
- Twin predicts future states
- Twin detects anomalies by comparing predicted vs actual
- Twin tests "what-if" scenarios

## Scalability

### Designed for 10,000+ Farms

**Horizontal Scaling**:
- Backend: Stateless API (scale with load balancer)
- Database: Read replicas for InfluxDB/PostgreSQL
- MQTT: Clustered Mosquitto brokers

**Vertical Optimization**:
- Efficient queries (indexes, query optimization)
- Caching (Redis for hot data)
- Data downsampling (store aggregates for old data)

**Multi-tenancy**:
- Farm-level isolation
- Tenant-specific schemas
- Resource quotas

**Data Management**:
- Raw data retention: 90 days
- Aggregated data: 2 years
- Historical snapshots: 10 years

## Security

### Authentication & Authorization

- **JWT tokens**: Stateless authentication
- **OAuth2**: Social login support
- **RBAC**: Role-based access control (Admin, Farmer, Viewer)
- **API keys**: For programmatic access

### Data Security

- **TLS/SSL**: All HTTP/WebSocket traffic
- **MQTT over TLS**: Encrypted sensor data
- **Database encryption**: At-rest encryption
- **Secrets management**: Environment variables, Vault

### Edge Security

- **OTA signatures**: Verify firmware authenticity
- **Device certificates**: Mutual TLS for MQTT
- **Secure boot**: Prevent unauthorized firmware

## Naming Conventions

### MQTT Topics

**Pattern**: `{layer}/{resource_type}/{resource_id}/{action}`

Examples:
- `farms/farm_001/sensors/soil_moisture/data`
- `farms/farm_001/commands/irrigation`
- `fog/fog_001/cloud/status`

**Rules**:
- Lowercase with underscores
- Hierarchical (for wildcard subscriptions)
- QoS: 0 (telemetry), 1 (commands/alerts)

### Database Tables

**Pattern**: `{plural_noun}` (e.g., `farms`, `sensors`, `users`)

**Columns**:
- Primary key: `id`
- Foreign keys: `{table}_id`
- Timestamps: `created_at`, `updated_at`

### API Endpoints

**Pattern**: `/api/v{version}/{resource}[/{id}][/{action}]`

Examples:
- `GET /api/v1/farms`
- `POST /api/v1/farms`
- `GET /api/v1/farms/farm_001`
- `POST /api/v1/farms/farm_001/twin/simulate`

**Rules**:
- RESTful verbs (GET, POST, PUT, DELETE)
- Plural resource names
- Version in URL

### Python/Python

- **Classes**: PascalCase (`SensorManager`)
- **Functions**: snake_case (`read_sensor_data`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_RETRIES`)
- **Files**: snake_case (`sensor_manager.py`)

### TypeScript/React

- **Components**: PascalCase (`SensorChart.tsx`)
- **Functions**: camelCase (`fetchSensorData`)
- **Constants**: UPPER_SNAKE_CASE (`API_BASE_URL`)
- **Files**: PascalCase for components, camelCase for utilities

### C++ (Edge)

- **Classes**: PascalCase (`SensorBase`)
- **Methods**: camelCase (`readCalibrated`)
- **Variables**: camelCase (`sensorValue`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_SENSORS`)
- **Files**: PascalCase (`.h`/`.cpp`)

## Architectural Trade-offs

### Decisions Made

1. **Three layers vs. Two**: Added fog layer for reliability
2. **MQTT vs. HTTP**: MQTT for lightweight IoT communication
3. **InfluxDB vs. PostgreSQL for sensors**: Time-series optimization
4. **Monorepo vs. Multiple repos**: Easier coordinated updates
5. **Docker vs. Bare metal**: Portability and consistency

### Future Considerations

- **Event sourcing**: For complete audit trail
- **GraphQL**: For flexible frontend queries
- **gRPC**: For high-performance inter-service communication
- **Kubernetes**: For production-scale orchestration
- **Machine learning on edge**: TensorFlow Lite on ESP32
