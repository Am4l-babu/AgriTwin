# DATA COLLECTION SCRIPTS
## AgriTwin Dataset Enhancement Tools

**Purpose:** Scripts to download and generate datasets for enhancing AgriTwin features

---

## 📁 SCRIPTS OVERVIEW

| Script | Purpose | Output | Time |
|--------|---------|--------|------|
| `download_nasa_weather.py` | Download weather data | CSV | 1 min |
| `generate_sample_yield_data.py` | Generate yield data | CSV/JSON | Instant |
| `export_sensor_data.py` | Export sensor data | CSV | 1 min |

---

## 🚀 QUICK START

### 1. Install Requirements

```bash
pip install requests pandas numpy
```

### 2. Download Weather Data (Priority 1)

```bash
cd scripts
python download_nasa_weather.py
```

**Edit the script first:**
```python
# Line 145-146: Set your farm coordinates
FARM_LATITUDE = 37.7749   # Your latitude
FARM_LONGITUDE = -122.4194  # Your longitude
```

**Output:** `weather_2023.csv`

### 3. Generate Sample Yield Data (For Testing)

```bash
python generate_sample_yield_data.py
```

**Output:**
- `sample_yield_data.csv` - Simple sample
- `realistic_yield_data.csv` - Realistic farm data
- `api_test_yield_data.json` - API test format

### 4. Export Sensor Data (If Backend Running)

```bash
# Start backend first
cd ../cloud/backend
python main_working.py

# In another terminal
cd ../../scripts
python export_sensor_data.py
```

**Output:**
- `sensor_data.csv` - Historical readings
- `sensor_stats.json` - Statistics
- `sensor_optimization_data.csv` - For optimization

---

## 📊 SCRIPT DETAILS

### 1. download_nasa_weather.py

**What it does:**
- Downloads weather data from NASA POWER API
- No API key required
- Global coverage
- 40+ years of historical data

**Configuration:**
```python
# Edit these lines in the script:
FARM_LATITUDE = 37.7749    # Your farm latitude
FARM_LONGITUDE = -122.4194  # Your farm longitude

# Download single year
download_nasa_weather(
    latitude=FARM_LATITUDE,
    longitude=FARM_LONGITUDE,
    start_date="20230101",
    end_date="20231231",
    output_file="weather_2023.csv"
)

# Download multiple years (uncomment in script)
download_multi_year(
    latitude=FARM_LATITUDE,
    longitude=FARM_LONGITUDE,
    years=[2021, 2022, 2023, 2024]
)
```

**Output Format:**
```csv
date,temperature_avg_c,temperature_max_c,temperature_min_c,humidity_percent,rainfall_mm,solar_radiation_mj_m2,wind_speed_m_s
20230101,22.5,28.3,18.2,65,0,18.5,2.3
20230102,23.1,29.1,19.0,68,2.3,17.2,2.1
```

**Parameters:**
- `T2M` - Average temperature (°C)
- `T2M_MAX` - Maximum temperature (°C)
- `T2M_MIN` - Minimum temperature (°C)
- `RH2M` - Relative humidity (%)
- `PRECTOTCORR` - Precipitation (mm/day)
- `ALLSKY_SFC_SW_DWN` - Solar radiation (MJ/m²/day)
- `WS2M` - Wind speed (m/s)

**Use Cases:**
- Digital twin calibration
- Evapotranspiration calculation
- Climate pattern analysis
- Irrigation scheduling

---

### 2. generate_sample_yield_data.py

**What it does:**
- Generates realistic sample yield data
- Creates different stability patterns
- Outputs in multiple formats

**Usage:**

```python
# Simple sample (3 zones, 4 years)
zones = ["north_field", "south_field", "east_field"]
years = [2021, 2022, 2023, 2024]
df = generate_sample_yield_data(zones, years, output_format="csv")

# Realistic farm data (auto-generates zones)
df = generate_realistic_farm_data(farm_size_ha=10)

# API test format
api_data = create_api_test_data()
```

**Output Format (CSV):**
```csv
zone_id,year,yield_tons_per_hectare
north_field,2021,5.2
north_field,2022,5.4
north_field,2023,5.1
north_field,2024,5.3
```

**Output Format (JSON for API):**
```json
{
  "north_field": [5.2, 5.4, 5.1, 5.3],
  "south_field": [2.3, 2.1, 2.4, 2.2],
  "east_field": [3.5, 5.0, 2.8, 4.9]
}
```

**Stability Patterns:**
- **Stable High:** CV < 15%, yield > 4.0 t/ha
- **Stable Low:** CV < 15%, yield < 3.0 t/ha
- **Unstable:** CV > 15%, variable yield

**Use Cases:**
- Test yield stability analysis
- Validate zone classification
- Calculate N loss risk
- Generate management recommendations

---

### 3. export_sensor_data.py

**What it does:**
- Exports sensor data from AgriTwin database
- Formats for optimization analysis
- Generates statistics

**Prerequisites:**
```bash
# Backend must be running
cd cloud/backend
python main_working.py
```

**Usage:**

```python
# Export 1 week of data
df = export_sensor_history(
    farm_id="farm_001",
    hours=168,
    output_file="sensor_data.csv"
)

# Export for optimization
df = export_for_optimization(
    farm_id="farm_001",
    hours=168
)

# Export statistics
stats = export_statistics(
    farm_id="farm_001",
    hours=24
)

# Generate sample data (if backend not running)
df = generate_sample_sensor_data(
    num_sensors=6,
    num_readings=100
)
```

**Output Format:**
```csv
sensor_id,location_x,location_y,timestamp,datetime,temperature,humidity,soil_moisture,light_level
sensor_1,0,0,1704096000,2024-01-01T10:00:00,25.3,68,45,520
sensor_2,10,0,1704096000,2024-01-01T10:00:00,25.1,69,47,515
```

**Use Cases:**
- Thompson Sampling optimization
- Sensor placement validation
- Coverage analysis
- Performance tracking

---

## 🎯 USAGE WORKFLOWS

### Workflow 1: Test Yield Analysis (5 minutes)

```bash
# 1. Generate sample data
python generate_sample_yield_data.py

# 2. Test API (backend must be running)
curl -X POST http://localhost:8000/api/v1/yield/analyze \
  -H 'Content-Type: application/json' \
  -d @api_test_yield_data.json

# 3. Review results
# Check stability classification, N loss risk, recommendations
```

### Workflow 2: Download Real Weather Data (5 minutes)

```bash
# 1. Edit script with your coordinates
nano download_nasa_weather.py
# Set FARM_LATITUDE and FARM_LONGITUDE

# 2. Download data
python download_nasa_weather.py

# 3. Review output
cat weather_2023.csv
```

### Workflow 3: Optimize Sensor Placement (10 minutes)

```bash
# 1. Export sensor data (or generate sample)
python export_sensor_data.py

# 2. Test optimization API
curl -X POST http://localhost:8000/api/v1/sensors/optimize \
  -H 'Content-Type: application/json' \
  -d '{
    "candidate_locations": [[0,0], [10,0], [0,10], [10,10], [20,0], [20,10]],
    "target_count": 2
  }'

# 3. Review recommendations
# Check selected sensors, savings, rankings
```

---

## 📈 EXPECTED OUTPUTS

### Weather Data:
- **Size:** ~365 rows per year
- **Columns:** 8 (date + 7 parameters)
- **Use:** Digital twin calibration

### Yield Data:
- **Size:** zones × years rows
- **Columns:** 3 (zone, year, yield)
- **Use:** Yield stability analysis

### Sensor Data:
- **Size:** sensors × readings rows
- **Columns:** 9 (id, location, time, 4 sensors)
- **Use:** Sensor optimization

---

## 🔧 CUSTOMIZATION

### Change Weather Parameters:

```python
# In download_nasa_weather.py, line 30
params = {
    "parameters": "T2M,RH2M,PRECTOTCORR,ALLSKY_SFC_SW_DWN,WS2M,PS",
    # Add more parameters as needed
}
```

**Available Parameters:**
- `T2M` - Temperature
- `RH2M` - Humidity
- `PRECTOTCORR` - Rainfall
- `ALLSKY_SFC_SW_DWN` - Solar radiation
- `WS2M` - Wind speed
- `PS` - Surface pressure
- `T2MDEW` - Dew point
- `EVPTRNS` - Evapotranspiration

### Change Yield Patterns:

```python
# In generate_sample_yield_data.py
# Adjust stability patterns:
if pattern_type == 'stable_high':
    base_yield = np.random.uniform(5.0, 6.0)  # Higher yields
    yields = [base_yield + np.random.normal(0, 0.1)]  # Less variation
```

### Change Sensor Grid:

```python
# In export_sensor_data.py
# Adjust grid size and spacing:
grid_size = 4  # 4x4 grid
spacing = 15   # 15 meters between sensors
```

---

## ⚠️ TROUBLESHOOTING

### NASA API Not Responding:
```
Error: Connection timeout
Solution: Check internet connection, try again later
```

### Backend Not Running:
```
Error: Cannot connect to AgriTwin backend
Solution: Start backend with: python cloud/backend/main_working.py
```

### No Sensor Data:
```
Error: No sensor data found
Solution: 
1. Check farm_id is correct
2. Ensure sensors are sending data
3. Use generate_sample_sensor_data() for testing
```

### Invalid Coordinates:
```
Error: Invalid latitude/longitude
Solution: Use valid coordinates (-90 to 90 for lat, -180 to 180 for lon)
```

---

## 📚 ADDITIONAL RESOURCES

### Find Your Coordinates:
- https://www.latlong.net/
- Google Maps (right-click → coordinates)

### NASA POWER Documentation:
- https://power.larc.nasa.gov/docs/

### Data Format Standards:
- ISO 8601 for dates
- WGS84 for coordinates
- Metric units (°C, mm, m/s)

---

## 🎓 NEXT STEPS

After running these scripts:

1. **Review the data** - Check CSV files for quality
2. **Test APIs** - Use data with AgriTwin endpoints
3. **Analyze results** - Review recommendations
4. **Collect real data** - Replace samples with actual measurements
5. **Iterate** - Refine based on results

---

**All scripts are ready to use! Start with weather data download for immediate value.** 🌱📊
