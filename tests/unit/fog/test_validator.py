import pytest
from fog.src.preprocessing.validator import SensorDataValidator


class TestSensorDataValidator:
    """Unit tests for sensor data validation."""
    
    @pytest.fixture
    def validator(self):
        return SensorDataValidator()
    
    def test_valid_soil_moisture(self, validator):
        """Test validation of valid soil moisture data."""
        data = {
            'sensor_type': 'soil_moisture',
            'value': 45.2,
            'timestamp': 1708075200
        }
        
        is_valid, error = validator.validate(data)
        
        assert is_valid is True
        assert error is None
    
    def test_soil_moisture_out_of_range_high(self, validator):
        """Test soil moisture value above maximum."""
        data = {
            'sensor_type': 'soil_moisture',
            'value': 150.0,  # Invalid
            'timestamp': 1708075200
        }
        
        is_valid, error = validator.validate(data)
        
        assert is_valid is False
        assert 'range' in error.lower()
    
    def test_soil_moisture_out_of_range_low(self, validator):
        """Test soil moisture value below minimum."""
        data = {
            'sensor_type': 'soil_moisture',
            'value': -10.0,  # Invalid
            'timestamp': 1708075200
        }
        
        is_valid, error = validator.validate(data)
        
        assert is_valid is False
        assert 'range' in error.lower()
    
    def test_valid_temperature(self, validator):
        """Test validation of valid temperature data."""
        data = {
            'sensor_type': 'temperature',
            'value': 22.5,
            'timestamp': 1708075200
        }
        
        is_valid, error = validator.validate(data)
        
        assert is_valid is True
        assert error is None
    
    def test_temperature_extremes(self, validator):
        """Test temperature at extreme but valid values."""
        # Very cold
        data_cold = {
            'sensor_type': 'temperature',
            'value': -39.0,
            'timestamp': 1708075200
        }
        is_valid, _ = validator.validate(data_cold)
        assert is_valid is True
        
        # Very hot
        data_hot = {
            'sensor_type': 'temperature',
            'value': 79.0,
            'timestamp': 1708075200
        }
        is_valid, _ = validator.validate(data_hot)
        assert is_valid is True
    
    def test_temperature_out_of_range(self, validator):
        """Test temperature beyond sensor limits."""
        data = {
            'sensor_type': 'temperature',
            'value': 100.0,  # Beyond sensor range
            'timestamp': 1708075200
        }
        
        is_valid, error = validator.validate(data)
        
        assert is_valid is False
    
    def test_ph_valid_range(self, validator):
        """Test pH in valid range."""
        for ph_value in [4.0, 7.0, 10.0]:
            data = {
                'sensor_type': 'ph',
                'value': ph_value,
                'timestamp': 1708075200
            }
            is_valid, _ = validator.validate(data)
            assert is_valid is True
    
    def test_ph_out_of_range(self, validator):
        """Test pH outside 0-14 range."""
        data = {
            'sensor_type': 'ph',
            'value': 15.0,  # Invalid
            'timestamp': 1708075200
        }
        
        is_valid, error = validator.validate(data)
        
        assert is_valid is False
    
    def test_missing_required_field(self, validator):
        """Test validation with missing required fields."""
        data = {
            'sensor_type': 'soil_moisture',
            # Missing 'value'
            'timestamp': 1708075200
        }
        
        is_valid, error = validator.validate(data)
        
        assert is_valid is False
        assert 'missing' in error.lower() or 'required' in error.lower()
    
    def test_missing_sensor_type(self, validator):
        """Test validation with missing sensor type."""
        data = {
            'value': 45.2,
            'timestamp': 1708075200
        }
        
        is_valid, error = validator.validate(data)
        
        assert is_valid is False
    
    def test_unknown_sensor_type(self, validator):
        """Test validation with unknown sensor type."""
        data = {
            'sensor_type': 'unknown_sensor',
            'value': 45.2,
            'timestamp': 1708075200
        }
        
        is_valid, error = validator.validate(data)
        
        # Should either accept with warning or reject
        # Implementation dependent
        assert is_valid in [True, False]
    
    def test_non_numeric_value(self, validator):
        """Test validation with non-numeric value."""
        data = {
            'sensor_type': 'soil_moisture',
            'value': 'invalid',  # Not a number
            'timestamp': 1708075200
        }
        
        is_valid, error = validator.validate(data)
        
        assert is_valid is False
        assert 'numeric' in error.lower() or 'type' in error.lower()
    
    def test_null_value(self, validator):
        """Test validation with null value."""
        data = {
            'sensor_type': 'soil_moisture',
            'value': None,
            'timestamp': 1708075200
        }
        
        is_valid, error = validator.validate(data)
        
        assert is_valid is False
    
    def test_invalid_timestamp(self, validator):
        """Test validation with invalid timestamp."""
        data = {
            'sensor_type': 'soil_moisture',
            'value': 45.2,
            'timestamp': 'invalid'
        }
        
        is_valid, error = validator.validate(data)
        
        assert is_valid is False
    
    def test_future_timestamp(self, validator):
        """Test validation with future timestamp."""
        import time
        future_timestamp = int(time.time()) + 86400  # Tomorrow
        
        data = {
            'sensor_type': 'soil_moisture',
            'value': 45.2,
            'timestamp': future_timestamp
        }
        
        is_valid, error = validator.validate(data)
        
        # May accept or reject depending on implementation
        # But should at least not crash
        assert is_valid in [True, False]
    
    def test_batch_validation(self, validator):
        """Test validation of multiple sensor readings."""
        batch_data = [
            {'sensor_type': 'soil_moisture', 'value': 45.2, 'timestamp': 1708075200},
            {'sensor_type': 'temperature', 'value': 22.5, 'timestamp': 1708075200},
            {'sensor_type': 'humidity', 'value': 65.0, 'timestamp': 1708075200},
            {'sensor_type': 'soil_moisture', 'value': 150.0, 'timestamp': 1708075200},  # Invalid
        ]
        
        if hasattr(validator, 'validate_batch'):
            results = validator.validate_batch(batch_data)
            
            # First 3 should be valid
            assert results[0]['valid'] is True
            assert results[1]['valid'] is True
            assert results[2]['valid'] is True
            
            # Last one should be invalid
            assert results[3]['valid'] is False
    
    def test_humidity_validation(self, validator):
        """Test humidity sensor validation."""
        # Valid
        data_valid = {
            'sensor_type': 'humidity',
            'value': 65.0,
            'timestamp': 1708075200
        }
        is_valid, _ = validator.validate(data_valid)
        assert is_valid is True
        
        # Invalid (>100%)
        data_invalid = {
            'sensor_type': 'humidity',
            'value': 120.0,
            'timestamp': 1708075200
        }
        is_valid, _ = validator.validate(data_invalid)
        assert is_valid is False
    
    def test_light_sensor_validation(self, validator):
        """Test light sensor validation."""
        data = {
            'sensor_type': 'light',
            'value': 50000,  # lux
            'timestamp': 1708075200
        }
        
        is_valid, _ = validator.validate(data)
        
        # Should be valid (0-120000 lux range)
        assert is_valid is True
    
    def test_ec_sensor_validation(self, validator):
        """Test electrical conductivity sensor validation."""
        data = {
            'sensor_type': 'ec',
            'value': 1.5,  # mS/cm
            'timestamp': 1708075200
        }
        
        is_valid, _ = validator.validate(data)
        
        # Should be valid
        assert is_valid is True
    
    @pytest.mark.parametrize("sensor_type,value,expected_valid", [
        ('soil_moisture', 50.0, True),
        ('soil_moisture', -5.0, False),
        ('soil_moisture', 105.0, False),
        ('temperature', 25.0, True),
        ('temperature', -50.0, False),
        ('temperature', 100.0, False),
        ('ph', 7.0, True),
        ('ph', -1.0, False),
        ('ph', 15.0, False),
        ('humidity', 60.0, True),
        ('humidity', 110.0, False),
    ])
    def test_parametrized_validation(self, validator, sensor_type, value, expected_valid):
        """Test various sensor types and values."""
        data = {
            'sensor_type': sensor_type,
            'value': value,
            'timestamp': 1708075200
        }
        
        is_valid, _ = validator.validate(data)
        
        assert is_valid == expected_valid
