# Testing Structure

This directory contains all automated tests for the smart farming system.

## Test Organization

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── edge/               # Edge firmware tests
│   ├── fog/                # Fog gateway tests
│   ├── backend/            # Backend API tests
│   └── digital_twin/       # Digital twin module tests
├── integration/            # Integration tests across layers
├── e2e/                    # End-to-end functional tests
└── performance/            # Load and performance tests
```

## Running Tests

### All Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov --cov-report=html
```

### Specific Test Suites

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# End-to-end tests
pytest tests/e2e/ -v

# Performance tests
pytest tests/performance/ -v -s
```

### By Component

```bash
# Backend tests
pytest tests/unit/backend/ -v

# Digital twin tests
pytest tests/unit/digital_twin/ -v
```

## Test Requirements

```bash
pip install pytest pytest-asyncio pytest-cov pytest-mock httpx faker
```

## Code Coverage Goals

- **Overall**: > 80%
- **Critical modules**: > 90%
  - Authentication
  - Sensor calibration
  - Digital twin state sync
  - Emergency control
- **Nice to have**: > 70%
  - API endpoints
  - Data validation

## Continuous Integration

Tests run automatically on:
- Every push to `main` or `develop`
- Every pull request
- Nightly builds

See `.github/workflows/ci-cd.yml` for CI configuration.

## Writing Tests

### Unit Test Example

```python
# tests/unit/digital_twin/test_evapotranspiration.py
import pytest
from cloud.digital_twin.physics_model.evapotranspiration import EvapotranspirationModel

def test_calculate_et0():
    model = EvapotranspirationModel()
    et0 = model.calculate_et0(
        temp_min=15.0,
        temp_max=25.0,
        humidity=60.0,
        wind_speed=2.0,
        solar_radiation=20.0,
        latitude=40.0,
        day_of_year=180
    )
    # ET0 should be positive and reasonable for a normal day
    assert 0 < et0 < 15.0
```

### Integration Test Example

```python
# tests/integration/test_mqtt_flow.py
import pytest
from fog.src.ingestion.mqtt_client import MQTTClient
from fog.src.buffer_manager.buffer import BufferManager

@pytest.mark.asyncio
async def test_sensor_data_flow():
    """Test complete data flow from MQTT to buffer."""
    buffer = BufferManager()
    mqtt_client = MQTTClient(buffer)
    
    # Publish test message
    test_payload = {
        "farm_id": "farm_001",
        "sensor_type": "soil_moisture",
        "value": 45.2
    }
    
    await mqtt_client.publish("farms/farm_001/sensors/soil_moisture/data", test_payload)
    
    # Verify it reached the buffer
    data = await buffer.get_recent("farm_001", hours=1)
    assert len(data) > 0
    assert data[0]["value"] == 45.2
```

### End-to-End Test Example

```python
# tests/e2e/test_irrigation_command.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_full_irrigation_flow(client: AsyncClient, auth_token):
    """Test irrigation command from API to edge device."""
    # Send irrigation command via API
    response = await client.post(
        "/api/v1/commands/farm_001/irrigation",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={
            "action": "activate",
            "duration_seconds": 30
        }
    )
    assert response.status_code == 200
    
    # Verify command reached MQTT
    # (This would check MQTT broker or edge device response)
```

## Test Fixtures

Common fixtures are defined in `conftest.py` files:

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient
from cloud.backend.main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def auth_token(client):
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": "test_user", "password": "test_pass"}
    )
    return response.json()["access_token"]
```

## Mocking

Use `pytest-mock` for mocking external dependencies:

```python
def test_sensor_reading_with_mock(mocker):
    # Mock the hardware read
    mock_adc = mocker.patch('analogRead')
    mock_adc.return_value = 2500
    
    sensor = SoilMoistureSensor(pin=34)
    value = sensor.readRaw()
    
    assert value == 2500
    mock_adc.assert_called_once_with(34)
```

## Performance Testing

```python
# tests/performance/test_api_load.py
import pytest
from locust import HttpUser, task, between

class FarmAPIUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def get_farms(self):
        self.client.get("/api/v1/farms")
    
    @task(3)
    def get_sensor_data(self):
        self.client.get("/api/v1/sensors/farm_001/soil_moisture?hours=24")
```

Run load tests:
```bash
locust -f tests/performance/test_api_load.py --host=http://localhost:8000
```

## Database Testing

Use test databases to avoid polluting production data:

```python
# tests/conftest.py
@pytest.fixture
async def test_db():
    # Create test database
    engine = create_async_engine("sqlite+aiosqlite:///test.db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
```

## Edge Firmware Testing

PlatformIO native testing:

```cpp
// test/test_sensor_calibration.cpp
#include <unity.h>
#include <SensorBase.h>

void test_calibration_linear() {
    SoilMoistureSensor sensor(34);
    sensor.calibrate(2950, 1350);  // air, water
    
    // Test conversion
    float value = sensor.convertRawToPercent(2100);
    TEST_ASSERT_FLOAT_WITHIN(5.0, 50.0, value);
}

void setup() {
    UNITY_BEGIN();
    RUN_TEST(test_calibration_linear);
    UNITY_END();
}

void loop() {}
```

Run edge tests:
```bash
cd edge
pio test
```

## Test Data

Use Faker for generating test data:

```python
from faker import Faker

fake = Faker()

def generate_farm_data():
    return {
        "farm_id": f"farm_{fake.uuid4()[:8]}",
        "name": f"{fake.word().title()} Farm",
        "location": {
            "latitude": float(fake.latitude()),
            "longitude": float(fake.longitude())
        },
        "area_sqm": fake.random_int(min=1000, max=10000)
    }
```

## Assertions

Use descriptive assertions:

```python
# Good
assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

# Better
from hamcrest import assert_that, equal_to, has_entries

assert_that(response.status_code, equal_to(200))
assert_that(response.json(), has_entries({
    'farm_id': 'farm_001',
    'status': 'active'
}))
```

## Parameterized Tests

Test multiple scenarios efficiently:

```python
@pytest.mark.parametrize("sensor_type,expected_range", [
    ("soil_moisture", (0, 100)),
    ("temperature", (-40, 80)),
    ("ph", (0, 14)),
    ("light", (0, 100000))
])
def test_sensor_ranges(sensor_type, expected_range):
    min_val, max_val = expected_range
    # Test logic here
```

## Test Markers

Organize tests with markers:

```python
# Mark slow tests
@pytest.mark.slow
def test_long_simulation():
    pass

# Mark tests requiring hardware
@pytest.mark.hardware
def test_actual_sensor():
    pass

# Skip in CI
@pytest.mark.skipif(os.getenv('CI'), reason="Requires hardware")
def test_edge_device():
    pass
```

Run specific markers:
```bash
pytest -m "not slow"  # Skip slow tests
pytest -m hardware    # Run only hardware tests
```

## Best Practices

1. **Arrange-Act-Assert**: Structure tests clearly
2. **One assertion per test**: Keep tests focused
3. **Descriptive names**: `test_should_reject_invalid_sensor_value`
4. **Independent tests**: No shared state between tests
5. **Fast tests**: Unit tests should run in milliseconds
6. **Realistic data**: Use production-like test data
7. **Clean up**: Always clean up resources (databases, files, connections)

## Test Documentation

Document complex test scenarios:

```python
def test_drought_simulation_accuracy():
    """
    Test digital twin drought simulation accuracy.
    
    Given:
        - Initial soil moisture: 50%
        - 7 days with no rain
        - Temperature: 30°C daily
    
    When:
        - Simulation runs for 7 days
    
    Then:
        - Final soil moisture should be 15-25%
        - Divergence score should be < 0.1
        - ET0 should average 6-8 mm/day
    """
    # Test implementation
```

## GitHub Actions Integration

Tests run automatically in CI:

```yaml
# .github/workflows/ci-cd.yml
- name: Run tests
  run: |
    pytest tests/ -v --cov --cov-report=xml
    
- name: Upload coverage
  uses: codecov/codecov-action@v3
```
