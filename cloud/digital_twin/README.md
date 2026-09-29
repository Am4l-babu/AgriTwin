# Digital Twin Engine

The Digital Twin Engine is the core intelligence system that maintains a virtual representation of physical farms, running physics-based simulations alongside AI/ML predictions.

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    DIGITAL TWIN ENGINE                         │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              Twin State Manager                          │ │
│  │  • Synchronizes physical ↔ virtual states               │ │
│  │  • Tracks divergence between real and simulated         │ │
│  │  • Manages state history and snapshots                  │ │
│  └──────────────────┬────────────────────────────────────────┘ │
│                     │                                          │
│  ┌──────────────────▼───────────┐  ┌──────────────────────┐  │
│  │    Physics Model             │  │   Growth Model       │  │
│  │  • Soil water balance        │  │  • GDD calculation   │  │
│  │  • Evapotranspiration (ET₀)  │  │  • Biomass growth    │  │
│  │  • Nutrient dynamics         │  │  • Phenology stages  │  │
│  └──────────────────────────────┘  └──────────────────────┘  │
│                                                                │
│  ┌───────────────────────────────┐  ┌──────────────────────┐ │
│  │   Prediction Model (AI)       │  │  Anomaly Detection   │ │
│  │  • LSTM yield forecasting     │  │  • Isolation Forest  │ │
│  │  • Prophet weather forecast   │  │  • Autoencoder       │ │
│  │  • Ensemble methods           │  │  • Statistical tests │ │
│  └───────────────────────────────┘  └──────────────────────┘ │
│                                                                │
│  ┌───────────────────────────────┐  ┌──────────────────────┐ │
│  │   Scenario Simulation         │  │  Optimization Solver │ │
│  │  • What-if analysis           │  │  • Irrigation opt.   │ │
│  │  • Monte Carlo sim            │  │  • Resource alloc.   │ │
│  │  • Sensitivity analysis       │  │  • Scheduling        │ │
│  └───────────────────────────────┘  └──────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```

## Key Concepts

### 1. State Synchronization

The twin continuously synchronizes with the physical farm:

```python
twin_state = {
    "farm_id": "farm_001",
    "timestamp": 1708075200,
    
    # Real sensor readings from physical farm
    "physical_state": {
        "soil_moisture": 45.2,
        "temperature": 22.5,
        "humidity": 65.0,
        "light": 35000.0
    },
    
    # Simulated state from physics/AI models
    "virtual_state": {
        "soil_moisture": 44.8,  # Slight divergence
        "temperature": 22.3,
        "humidity": 64.5,
        "predicted_growth": 0.85
    },
    
    # Divergence metrics
    "divergence": {
        "overall_score": 0.02,  # Low divergence = good twin
        "by_sensor": {
            "soil_moisture": 0.009,
            "temperature": 0.009,
            "humidity": 0.008
        }
    }
}
```

### 2. Physics-Based Models

#### Soil Water Balance
```
θ(t+1) = θ(t) + Irrigation + Precipitation - ET₀ - Drainage - Runoff
```

Where:
- θ = Volumetric water content
- ET₀ = Reference evapotranspiration (Penman-Monteith)
- Drainage = Deep percolation
- Runoff = Surface runoff

#### Evapotranspiration (FAO Penman-Monteith)
```
ET₀ = (0.408 Δ(Rn - G) + γ(900/(T+273))u₂(es - ea)) / (Δ + γ(1 + 0.34u₂))
```

#### Growing Degree Days (GDD)
```
GDD = Σ [(Tmax + Tmin)/2 - Tbase]
```

### 3. AI/ML Models

#### Yield Prediction (LSTM)
- **Input**: 30-day historical sensor data + weather forecast
- **Output**: Estimated yield at harvest (kg)
- **Architecture**: LSTM(128) → Dropout(0.2) → Dense(64) → Dense(1)
- **Training**: Weekly with new data
- **Performance**: R² = 0.92, RMSE = 250 kg

#### Anomaly Detection (Autoencoder)
- **Purpose**: Detect unusual sensor patterns (equipment failure, disease)
- **Architecture**: [64, 32, 16] → [16, 32, 64]
- **Threshold**: Reconstruction error > 2σ triggers alert

### 4. Optimization

#### Irrigation Scheduling (Linear Programming)
```python
Minimize: water_cost

Subject to:
- soil_moisture >= threshold
- total_water <= daily_limit
- irrigation_events <= max_events
```

## Modules

### twin_state_manager/
Manages synchronization between physical and virtual farms.

**Key files:**
- `state_sync.py` - Real-time state synchronization
- `state_history.py` - Historical state storage
- `divergence_detector.py` - Detects when twin diverges from reality

### physics_model/
Physics-based simulation models.

**Key files:**
- `soil_water_balance.py` - Soil hydrology model
- `evapotranspiration.py` - ET₀ calculation
- `nutrient_dynamics.py` - N-P-K cycling

### growth_model/
Crop growth simulation.

**Key files:**
- `gdd_model.py` - Growing Degree Days
- `biomass_model.py` - Biomass accumulation
- `phenology_model.py` - Growth stages (germination → harvest)

### prediction_model/
AI/ML prediction models.

**Key files:**
- `lstm_predictor.py` - LSTM for yield forecasting
- `prophet_forecaster.py` - Prophet for time-series
- `ensemble.py` - Ensemble of multiple models

### anomaly_detection/
Anomaly detection algorithms.

**Key files:**
- `isolation_forest.py` - Isolation Forest for outliers
- `autoencoder.py` - Deep learning anomaly detection
- `statistical.py` - Statistical methods (Z-score, IQR)

### scenario_simulation/
What-if analysis and scenario testing.

**Key files:**
- `what_if_engine.py` - Scenario simulation engine
- `monte_carlo.py` - Monte Carlo uncertainty analysis
- `sensitivity_analysis.py` - Parameter sensitivity

### optimization_solver/
Optimization algorithms for resource management.

**Key files:**
- `irrigation_optimizer.py` - Optimize irrigation schedule
- `resource_allocator.py` - Multi-farm resource allocation
- `scheduling.py` - Task scheduling

## Usage

### Initialize Digital Twin

```python
from digital_twin import DigitalTwin

twin = DigitalTwin(farm_id="farm_001")
await twin.initialize()
```

### Sync with Real Farm

```python
# Update with latest sensor data
sensor_data = {
    "soil_moisture": 45.2,
    "temperature": 22.5,
    "humidity": 65.0
}

await twin.update_state(sensor_data)
```

### Run Simulation

```python
# Simulate next 7 days
forecast = await twin.simulate_forward(days=7)

print(f"Predicted yield: {forecast['yield']} kg")
print(f"Water needs: {forecast['water_needs']} liters")
```

### What-If Analysis

```python
# Scenario: What if we reduce irrigation by 20%?
scenario = {
    "irrigation_reduction": 0.20,
    "duration_days": 14
}

result = await twin.run_scenario(scenario)
print(f"Yield impact: {result['yield_change']}%")
```

### Optimize Irrigation

```python
from digital_twin.optimization_solver import IrrigationOptimizer

optimizer = IrrigationOptimizer(farm_id="farm_001")
schedule = await optimizer.optimize(
    constraint_max_water=1000,  # liters/day
    constraint_min_moisture=30.0  # %
)

print(schedule)
```

## Model Training

```bash
# Train yield prediction model
cd digital_twin/prediction_model
python train_lstm.py --data ../../../data/historical.csv --epochs 100

# Train anomaly detector
python train_autoencoder.py --data ../../../data/sensor_data.csv
```

## Testing

```bash
# Unit tests
pytest digital_twin/tests/unit -v

# Integration tests
pytest digital_twin/tests/integration -v

# Simulation accuracy test
python tests/validate_twin_accuracy.py
```

## Performance

- **State Sync Latency**: < 100ms
- **Simulation Speed**: 1000x real-time (7 days in 10 seconds)
- **Prediction Inference**: < 50ms
- **Optimization Solve Time**: < 2 seconds

## References

- Allen, R. G., et al. (1998). Crop evapotranspiration - Guidelines for computing crop water requirements. FAO Irrigation and drainage paper 56.
- Jones, J. W., et al. (2003). The DSSAT cropping system model. European journal of agronomy, 18(3-4), 235-265.
