# Cloud Layer - Backend & Digital Twin System

The Cloud layer is the central intelligence of the Smart Farming Digital Twin System, providing:

- **RESTful API Backend** (FastAPI)
- **Digital Twin Engine** (Physics + AI simulation)
- **AI/ML Models** (Prediction, Anomaly Detection, Optimization)
- **Time-series Database** (InfluxDB)
- **Relational Database** (PostgreSQL)
- **Real-time Dashboard** (React + WebSocket)
- **Scalable Architecture** for 10,000+ farms

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLOUD LAYER                              │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │   Frontend       │  │    Backend API   │  │  WebSocket   │ │
│  │   (React)        │◄─┤    (FastAPI)     │◄─┤   Server     │ │
│  └──────────────────┘  └────────┬─────────┘  └──────────────┘ │
│                                 │                               │
│  ┌──────────────────────────────┼────────────────────────────┐ │
│  │          Digital Twin Core   │                            │ │
│  │  ┌───────────────┐  ┌────────▼─────────┐  ┌────────────┐ │ │
│  │  │ Twin State    │  │ Physics Model    │  │ Growth     │ │ │
│  │  │ Manager       │  │ (Soil, Weather)  │  │ Model      │ │ │
│  │  └───────────────┘  └──────────────────┘  └────────────┘ │ │
│  │  ┌───────────────┐  ┌──────────────────┐  ┌────────────┐ │ │
│  │  │ Scenario      │  │ Optimization     │  │ Anomaly    │ │ │
│  │  │ Simulation    │  │ Engine           │  │ Detection  │ │ │
│  │  └───────────────┘  └──────────────────┘  └────────────┘ │ │
│  └────────────────────────────┬──────────────────────────────┘ │
│                               │                                 │
│  ┌────────────────────────────┼──────────────────────────────┐ │
│  │         AI/ML Engine       │                              │ │
│  │  ┌───────────────┐  ┌──────▼───────┐  ┌────────────────┐ │ │
│  │  │ Yield         │  │ Weather      │  │ Model          │ │ │
│  │  │ Prediction    │  │ Forecasting  │  │ Registry       │ │ │
│  │  └───────────────┘  └──────────────┘  └────────────────┘ │ │
│  └─────────────────────────────────────────────────────────── │ │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐                   │
│  │   InfluxDB       │  │   PostgreSQL     │                   │
│  │  (Time-series)   │  │  (Relational)    │                   │
│  └──────────────────┘  └──────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
cloud/
├── backend/                    # FastAPI backend
│   ├── api/
│   │   ├── v1/
│   │   │   ├── auth.py        # Authentication endpoints
│   │   │   ├── farms.py       # Farm management
│   │   │   ├── sensors.py     # Sensor data endpoints
│   │   │   ├── digital_twin.py # Digital twin API
│   │   │   ├── predictions.py  # AI predictions API
│   │   │   └── optimization.py # Optimization API
│   │   └── deps.py            # Dependencies
│   ├── models/                # Database models (ORM)
│   │   ├── user.py
│   │   ├── farm.py
│   │   ├── sensor.py
│   │   ├── twin_state.py
│   │   └── prediction.py
│   ├── services/              # Business logic
│   │   ├── auth_service.py
│   │   ├── farm_service.py
│   │   ├── sensor_service.py
│   │   └── twin_service.py
│   ├── middleware/
│   │   ├── auth.py
│   │   ├── cors.py
│   │   └── rate_limit.py
│   ├── websocket/
│   │   └── manager.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── database.py
│   ├── schemas/               # Pydantic schemas
│   │   ├── user.py
│   │   ├── farm.py
│   │   └── sensor.py
│   └── main.py
│
├── digital_twin/              # Digital Twin Engine
│   ├── twin_state_manager/
│   │   ├── state_sync.py
│   │   ├── state_history.py
│   │   └── divergence_detector.py
│   ├── physics_model/
│   │   ├── soil_water_balance.py
│   │   ├── evapotranspiration.py
│   │   └── nutrient_dynamics.py
│   ├── growth_model/
│   │   ├── gdd_model.py       # Growing Degree Days
│   │   ├── biomass_model.py
│   │   └── phenology_model.py
│   ├── prediction_model/
│   │   ├── lstm_predictor.py
│   │   ├── prophet_forecaster.py
│   │   └── ensemble.py
│   ├── anomaly_detection/
│   │   ├── isolation_forest.py
│   │   ├── autoencoder.py
│   │   └── statistical.py
│   ├── scenario_simulation/
│   │   ├── what_if_engine.py
│   │   ├── monte_carlo.py
│   │   └── sensitivity_analysis.py
│   └── optimization_solver/
│       ├── irrigation_optimizer.py
│       ├── resource_allocator.py
│       └── scheduling.py
│
├── ai_engine/                 # Machine Learning Engine
│   ├── training/
│   │   ├── train_yield_model.py
│   │   ├── train_anomaly_detector.py
│   │   └── hyperparameter_tuning.py
│   ├── inference/
│   │   ├── realtime_inference.py
│   │   └── batch_inference.py
│   ├── model_registry/
│   │   ├── model_manager.py
│   │   ├── versioning.py
│   │   └── model_store.py
│   ├── pipelines/
│   │   ├── data_preprocessing.py
│   │   ├── feature_engineering.py
│   │   └── data_augmentation.py
│   └── models/
│       ├── yield_lstm.py
│       ├── anomaly_autoencoder.py
│       └── weather_forecast.py
│
├── database/
│   ├── influxdb/
│   │   ├── schemas/
│   │   └── migrations/
│   ├── postgresql/
│   │   ├── schemas/
│   │   └── alembic/
│   │       └── versions/
│   └── init_scripts/
│
└── frontend/                  # React Dashboard
    ├── src/
    │   ├── components/
    │   │   ├── Dashboard/
    │   │   ├── FarmView/
    │   │   ├── SensorCharts/
    │   │   ├── DigitalTwin/
    │   │   ├── Predictions/
    │   │   └── Alerts/
    │   ├── pages/
    │   │   ├── Home.tsx
    │   │   ├── Farms.tsx
    │   │   ├── Analytics.tsx
    │   │   ├── TwinSimulation.tsx
    │   │   └── Settings.tsx
    │   ├── services/
    │   │   ├── api.ts
    │   │   ├── websocket.ts
    │   │   └── auth.ts
    │   ├── hooks/
    │   │   ├── useSensorData.ts
    │   │   ├── useWebSocket.ts
    │   │   └── useTwinState.ts
    │   ├── store/
    │   │   ├── authSlice.ts
    │   │   ├── farmSlice.ts
    │   │   └── sensorSlice.ts
    │   ├── utils/
    │   │   ├── formatters.ts
    │   │   ├── validators.ts
    │   │   └── constants.ts
    │   ├── App.tsx
    │   └── main.tsx
    ├── public/
    ├── package.json
    └── vite.config.ts
```

## Tech Stack

### Backend
- **Python 3.11+**
- **FastAPI** - Modern async web framework
- **SQLAlchemy** - ORM
- **Alembic** - Database migrations
- **Pydantic** - Data validation
- **JWT** - Authentication
- **WebSocket** - Real-time communication

### Digital Twin & AI
- **NumPy/SciPy** - Scientific computing
- **TensorFlow/PyTorch** - Deep learning
- **Scikit-learn** - Traditional ML
- **Prophet** - Time-series forecasting
- **PuLP/OR-Tools** - Optimization

### Databases
- **InfluxDB 2.x** - Time-series data
- **PostgreSQL 15** - Relational data
- **Redis** - Caching

### Frontend
- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Redux Toolkit** - State management
- **Material-UI** - Component library
- **Recharts** - Data visualization
- **Socket.io** - WebSocket client

## Installation

### Backend Setup

```bash
cd cloud/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start server
uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
cd cloud/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Environment Variables

Create `.env` file in `cloud/backend/`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/smart_farming
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=your-token
INFLUXDB_ORG=smart_farming_org
INFLUXDB_BUCKET=sensor_data

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-min-32-characters
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# Digital Twin
TWIN_SIMULATION_INTERVAL=300
TWIN_ENABLED=true

# AI Engine
AI_MODEL_PATH=./models
AI_PREDICTIONS_ENABLED=true
```

## API Documentation

Access interactive API docs:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Digital Twin Engine

### State Synchronization

The Digital Twin maintains a virtual representation of each physical farm:

```python
twin_state = {
    "farm_id": "farm_001",
    "timestamp": 1234567890,
    "sensors": {
        "soil_moisture": 45.2,
        "temperature": 22.5,
        "humidity": 65.0
    },
    "computed_states": {
        "soil_water_content": 0.35,
        "evapotranspiration": 4.5,
        "crop_growth_stage": "vegetative"
    },
    "predictions": {
        "yield_estimate": 5.2,
        "days_to_harvest": 45,
        "water_needs_7d": 35.0
    }
}
```

### Simulation Modes

1. **Real-time Sync**: Continuously updated with live data
2. **Fast-forward**: Simulate future scenarios
3. **What-if Analysis**: Test different interventions
4. **Historical Replay**: Analyze past performance

## AI Models

### 1. Yield Prediction (LSTM)
- Input: Historical sensor data, weather, crop type
- Output: Estimated yield at harvest
- Re-trained weekly with new data

### 2. Anomaly Detection (Autoencoder)
- Detects unusual sensor patterns
- Alerts for equipment failure, disease, pests

### 3. Resource Optimization (Linear Programming)
- Optimal irrigation scheduling
- Fertilizer application timing
- Multi-farm resource allocation

## Testing

```bash
# Backend tests
cd cloud/backend
pytest tests/ -v --cov

# Frontend tests
cd cloud/frontend
npm test
```

## Deployment

See [Docker configurations](../../docker/README.md) for production deployment.

## License

MIT License
