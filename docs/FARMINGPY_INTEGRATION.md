# External Crop Modeling Library Integration Guide

## Overview

This project can integrate the farmingpy library to enhance agricultural modeling capabilities in the Digital Twin system.

**farmingpy** is a Python library for Smart Farming data and modelling that provides:
- ISOBUS (ISO 11783) task file reading for farm equipment data
- Earth Observation data integration from SentinelHub
- APSIM crop simulation model interface
- Professional agricultural data structures

## Why farmingpy?

This external library brings enterprise-grade agricultural modeling to our IoT system:

1. **Validated Crop Models**: Access to APSIM, one of the world's most widely used crop simulation platforms
2. **Satellite Integration**: Direct access to Sentinel satellite imagery for NDVI and crop health monitoring
3. **Equipment Data**: Process data from modern farm equipment using ISO standards
4. **Research-Backed**: Built by agricultural scientists and used in production systems

## Installation

### Requirements

Add to your `requirements.txt`:
```txt
farmingpy>=0.1.0
pyeto>=0.1.0  # For FAO Penman-Monteith ET calculations
```

### Install

```bash
cd cloud/digital_twin
pip install -r requirements.txt
```

Or install directly:
```bash
pip install farmingpy
```

## Repository Information

- **Library**: farmingpy
- **License**: MIT
- **Language**: Python
- **Installation**: `pip install farmingpy`

## Architecture Integration

### Digital Twin Enhancement

```
┌──────────────────────────────────────────────────────────────┐
│              ENHANCED DIGITAL TWIN SYSTEM                    │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  IoT Sensor Data (ESP32)                               │ │
│  │  • Temperature, Humidity, Light                        │ │
│  │  • Soil Moisture, pH                                   │ │
│  └──────────────────┬─────────────────────────────────────┘ │
│                     │                                        │
│  ┌──────────────────▼─────────────────────────────────────┐ │
│  │  farmingpy Adapter                                     │ │
│  │  • Convert IoT data to agricultural formats           │ │
│  │  • Interface with APSIM models                        │ │
│  └──────────────────┬─────────────────────────────────────┘ │
│                     │                                        │
│         ┌───────────┴────────────┐                          │
│         │                        │                          │
│  ┌──────▼──────┐         ┌──────▼──────┐                   │
│  │ Crop Models │         │ Satellite   │                   │
│  │ (APSIM)     │         │ Data (NDVI) │                   │
│  └─────────────┘         └─────────────┘                   │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Enhanced Predictions                                  │ │
│  │  • Yield forecasting                                   │ │
│  │  • Growth stage prediction                             │ │
│  │  • Stress detection                                    │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

## Usage Examples

### 1. Basic Crop Modeling

```python
from cloud.digital_twin.physics_model.crop_modeling import (
    CropGrowthModel, CropParameters, SoilParameters, WeatherData
)
from datetime import datetime, timedelta

# Define crop and soil
crop = CropParameters(
    crop_type="lettuce",
    planting_date=datetime.now() - timedelta(days=15),
    base_temperature=7.0,
    optimal_temperature=20.0
)

soil = SoilParameters(
    soil_type="loam",
    field_capacity=0.35,
    wilting_point=0.15,
    pH=6.8
)

# Create model
model = CropGrowthModel(crop, soil)

# Simulate daily growth
weather = WeatherData(
    timestamp=datetime.now(),
    temperature=22.0,
    humidity=65.0,
    solar_radiation=35000.0
)

daily_gdd = model.calculate_gdd(25.0, 19.0)  # max, min temps
growth = model.simulate_biomass_growth(weather, soil_moisture=0.28, daily_gdd=daily_gdd)

print(f"Growth Stage: {growth['growth_stage']}")
print(f"Biomass: {growth['total_biomass']:.4f} kg/m²")
print(f"Water Stress: {growth['water_stress']:.2f}")
```

### 2. Using farmingpy Adapter

```python
from cloud.digital_twin.physics_model.farmingpy_adapter import FarmingPyAdapter

# Initialize adapter
adapter = FarmingPyAdapter()

# Convert IoT sensor data
sensor_reading = {
    'timestamp': datetime.now(),
    'temperature': 22.5,
    'humidity': 65.0,
    'soil_moisture': 0.28,
    'light': 45000.0,
    'ph': 6.8
}

farmingpy_data = adapter.convert_sensor_to_farmingpy_format(sensor_reading)

# Run APSIM simulation (if farmingpy installed)
results = adapter.run_apsim_simulation(
    crop_type="lettuce",
    weather_data=[farmingpy_data],
    soil_params={'type': 'loam'}
)
```

### 3. Satellite NDVI Integration

```python
# Fetch satellite data for crop health monitoring
ndvi_data = adapter.fetch_satellite_ndvi(
    latitude=40.7128,    # Farm location
    longitude=-74.0060,
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now(),
    api_key='your_sentinel_api_key'
)

# NDVI values indicate crop health:
# < 0.2  = Bare soil / stressed crops
# 0.2-0.5 = Sparse vegetation
# 0.5-0.8 = Dense healthy vegetation
# > 0.8   = Very dense vegetation
```

### 4. Complete Integration Workflow

```python
from cloud.digital_twin.physics_model.farmingpy_adapter import (
    integrate_farmingpy_with_digital_twin
)

# Your IoT sensor data
sensor_data = [
    {
        'timestamp': datetime.now(),
        'temperature': 22.5,
        'humidity': 65.0,
        'soil_moisture': 0.28,
        'light': 45000.0,
        'ph': 6.8
    }
    # ... more readings
]

# Farm location
farm_location = (40.7128, -74.0060)  # (lat, lon)

# Get enhanced digital twin state
enhanced_state = integrate_farmingpy_with_digital_twin(
    sensor_data=sensor_data,
    farm_location=farm_location
)

print(f"Crop Parameters: {enhanced_state['crop_parameters']}")
print(f"Satellite NDVI: {enhanced_state['satellite_ndvi']}")
print(f"Weather Forecast: {enhanced_state['weather_forecast']}")
```

## Features Enabled

### 1. APSIM Crop Simulation

**Before farmingpy**: Simple GDD-based growth models
**After farmingpy**: Full physics-based APSIM simulations with:
- Detailed phenology modeling
- Water balance at soil layer resolution
- Nitrogen cycle simulation
- Yield prediction with confidence intervals

### 2. Earth Observation Data

**Integration with SentinelHub**:
- NDVI (Normalized Difference Vegetation Index)
- LAI (Leaf Area Index)
- Soil moisture from SAR
- True color imagery

**Benefits**:
- Validate IoT sensor readings with satellite data
- Fill gaps in sensor coverage
- Field-scale crop health monitoring

### 3. ISOBUS Data Processing

If you have farm equipment with ISOBUS (ISO 11783):
- Read task files from tractors
- Process equipment sensor data
- Integrate field operations into models

### 4. Professional Data Structures

farmingpy provides standardized agricultural data formats compatible with:
- APSIM model inputs
- DSSAT crop models
- AgMIP data standards

## Configuration

### Environment Variables

Add to your `.env` file:

```bash
# SentinelHub (for satellite data)
SENTINELHUB_CLIENT_ID=your_client_id
SENTINELHUB_CLIENT_SECRET=your_client_secret

# farmingpy settings
FARMINGPY_CACHE_DIR=/tmp/farmingpy_cache
FARMINGPY_LOG_LEVEL=INFO
```

### farmingpy Configuration

Create `cloud/digital_twin/farmingpy_config.yaml`:

```yaml
apsim:
  executable_path: "/usr/local/bin/apsim"
  model_dir: "./apsim_models"
  
sentinel:
  cache_enabled: true
  cache_ttl: 86400  # 24 hours
  
crop_database:
  custom_crops:
    - name: "hydroponic_lettuce"
      base_temp: 7.0
      optimal_temp: 20.0
      gdd_to_maturity: 700
```

## Testing

### Unit Tests

```bash
cd cloud/digital_twin
pytest tests/test_farmingpy_integration.py -v
```

### Integration Tests

```bash
# Test with real sensor data
pytest tests/test_crop_modeling.py --use-real-data

# Test satellite integration (requires API key)
pytest tests/test_satellite_ndvi.py --api-key=$SENTINEL_API_KEY
```

## Performance Considerations

### Caching

farmingpy includes intelligent caching for:
- Satellite imagery downloads
- APSIM simulation results
- Weather data fetches

### Optimization

For production deployments:
1. Use async operations for satellite data fetches
2. Cache APSIM results for identical input conditions
3. Batch sensor data conversions
4. Pre-download satellite imagery during off-peak hours

## Troubleshooting

### farmingpy not found

```bash
# Verify installation
pip list | grep farmingpy

# Install if missing
pip install farmingpy
```

### APSIM models not running

farmingpy requires APSIM to be installed separately:
```bash
# On Linux
wget https://www.apsim.info/download/apsim-x-latest.deb
sudo dpkg -i apsim-x-latest.deb

# On Windows
# Download installer from https://www.apsim.info
```

### Satellite data not available

Requires SentinelHub account:
1. Sign up at https://www.sentinel-hub.com/
2. Get API credentials
3. Add to environment variables

## Advanced Use Cases

### 1. Model Calibration

Use farmingpy to calibrate your simple models against APSIM:

```python
from cloud.digital_twin.physics_model.farmingpy_adapter import FarmingPyAdapter

adapter = FarmingPyAdapter()

# Validate predictions
validation = adapter.validate_with_farmingpy_models(
    digital_twin_state=current_state,
    sensor_readings=historical_data
)

print(f"Model Agreement: {validation['model_agreement']}")
```

### 2. Yield Forecasting

Combine IoT data with APSIM for accurate yield prediction:

```python
from cloud.digital_twin.physics_model.crop_modeling import APSIMIntegration

apsim = APSIMIntegration()

yield_forecast = apsim.run_simulation(
    start_date=planting_date,
    end_date=harvest_date,
    weather_data=sensor_weather_data,
    soil_params=soil,
    crop_params=crop
)

print(f"Predicted Yield: {yield_forecast['yield_kg_ha'].iloc[-1]:.0f} kg/ha")
```

### 3. Multi-Field Management

Scale to multiple fields with satellite monitoring:

```python
fields = [
    {"id": "field_1", "lat": 40.7128, "lon": -74.0060},
    {"id": "field_2", "lat": 40.7580, "lon": -73.9855},
]

for field in fields:
    ndvi = adapter.fetch_satellite_ndvi(
        latitude=field['lat'],
        longitude=field['lon'],
        start_date=datetime.now() - timedelta(days=7),
        end_date=datetime.now()
    )
    
    if ndvi and ndvi[-1]['value'] < 0.4:
        print(f"⚠️ Field {field['id']} shows crop stress!")
```

## Contributing

To improve the farmingpy integration:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/farmingpy-enhancement`
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## References

- [APSIM Documentation](https://www.apsim.info/documentation/)
- [SentinelHub API](https://docs.sentinel-hub.com/)
- [ISO 11783 Standard](https://www.iso.org/standard/57556.html)

## License

farmingpy is licensed under MIT License.

## Support

For issues specific to farmingpy integration:
- Open an issue in this repository with tag `farmingpy`

For general agricultural modeling questions:
- APSIM support forum
- Precision agriculture communities
