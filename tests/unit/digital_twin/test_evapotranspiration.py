import pytest
from cloud.digital_twin.physics_model.evapotranspiration import EvapotranspirationModel
import numpy as np


class TestEvapotranspirationModel:
    """Unit tests for FAO-56 Penman-Monteith ET0 model."""
    
    @pytest.fixture
    def model(self):
        return EvapotranspirationModel()
    
    def test_calculate_et0_typical_day(self, model):
        """Test ET0 calculation for typical summer day."""
        et0 = model.calculate_et0(
            temp_min=15.0,
            temp_max=25.0,
            humidity=60.0,
            wind_speed=2.0,
            solar_radiation=20.0,
            latitude=40.0,
            day_of_year=180  # Mid-summer
        )
        
        # ET0 should be positive and within reasonable range
        assert 0 < et0 < 15.0, f"ET0 {et0} outside reasonable range"
        assert 3.0 < et0 < 8.0, f"ET0 {et0} unusual for typical summer day"
    
    def test_calculate_et0_hot_dry_day(self, model):
        """Test ET0 for hot, dry conditions (high ET0 expected)."""
        et0 = model.calculate_et0(
            temp_min=25.0,
            temp_max=40.0,
            humidity=20.0,
            wind_speed=4.0,
            solar_radiation=25.0,
            latitude=35.0,
            day_of_year=210
        )
        
        # High ET0 expected
        assert et0 > 8.0, f"ET0 {et0} too low for hot, dry day"
        assert et0 < 20.0, f"ET0 {et0} unrealistically high"
    
    def test_calculate_et0_cool_humid_day(self, model):
        """Test ET0 for cool, humid conditions (low ET0 expected)."""
        et0 = model.calculate_et0(
            temp_min=5.0,
            temp_max=15.0,
            humidity=90.0,
            wind_speed=1.0,
            solar_radiation=10.0,
            latitude=45.0,
            day_of_year=90  # Early spring
        )
        
        # Low ET0 expected
        assert et0 > 0, f"ET0 {et0} cannot be negative"
        assert et0 < 3.0, f"ET0 {et0} too high for cool, humid day"
    
    def test_saturation_vapor_pressure(self, model):
        """Test saturation vapor pressure calculation."""
        es_0 = model._saturation_vapor_pressure(0.0)
        es_20 = model._saturation_vapor_pressure(20.0)
        es_40 = model._saturation_vapor_pressure(40.0)
        
        # Should increase with temperature
        assert es_0 < es_20 < es_40
        
        # Check approximate values (FAO-56 Table 3)
        assert 0.6 < es_0 < 0.7
        assert 2.3 < es_20 < 2.4
        assert 7.3 < es_40 < 7.5
    
    def test_slope_vapor_pressure_curve(self, model):
        """Test slope of saturation vapor pressure curve."""
        delta_20 = model._slope_vapor_pressure_curve(20.0)
        
        # Should be positive
        assert delta_20 > 0
        
        # Approximate value at 20°C (FAO-56 Table 3)
        assert 0.12 < delta_20 < 0.16
    
    def test_psychrometric_constant(self, model):
        """Test psychrometric constant calculation."""
        # At sea level
        gamma_0 = model._psychrometric_constant(0)
        
        # At 1000m elevation
        gamma_1000 = model._psychrometric_constant(1000)
        
        # Should decrease with elevation
        assert gamma_1000 < gamma_0
        
        # Sea level value should be around 0.067 kPa/°C
        assert 0.065 < gamma_0 < 0.070
    
    def test_net_radiation(self, model):
        """Test net radiation calculation."""
        rn = model._net_radiation(
            solar_radiation=20.0,
            temp_min=15.0,
            temp_max=25.0,
            humidity=60.0,
            latitude=40.0,
            day_of_year=180
        )
        
        # Net radiation should be positive during day
        assert rn > 0
        assert rn < 30.0  # Upper bound
    
    def test_extraterrestrial_radiation(self, model):
        """Test extraterrestrial radiation calculation."""
        ra_summer = model._extraterrestrial_radiation(40.0, 180)  # Summer
        ra_winter = model._extraterrestrial_radiation(40.0, 365)  # Winter
        
        # Summer should have more radiation in northern hemisphere
        assert ra_summer > ra_winter
        
        # Should be within reasonable range
        assert 0 < ra_summer < 50.0
        assert 0 < ra_winter < 50.0
    
    def test_crop_coefficient_application(self, model):
        """Test crop coefficient (Kc) application."""
        # Reference ET0
        et0 = model.calculate_et0(
            temp_min=15.0,
            temp_max=25.0,
            humidity=60.0,
            wind_speed=2.0,
            solar_radiation=20.0,
            latitude=40.0,
            day_of_year=180
        )
        
        # Crop-specific ET (Kc = 1.15 for mature tomato)
        etc = et0 * 1.15
        
        assert etc > et0
        assert etc < et0 * 1.5
    
    def test_different_latitudes(self, model):
        """Test ET0 calculation at different latitudes."""
        et0_equator = model.calculate_et0(
            temp_min=20.0, temp_max=30.0, humidity=70.0,
            wind_speed=2.0, solar_radiation=22.0,
            latitude=0.0, day_of_year=180
        )
        
        et0_mid = model.calculate_et0(
            temp_min=20.0, temp_max=30.0, humidity=70.0,
            wind_speed=2.0, solar_radiation=22.0,
            latitude=45.0, day_of_year=180
        )
        
        et0_polar = model.calculate_et0(
            temp_min=20.0, temp_max=30.0, humidity=70.0,
            wind_speed=2.0, solar_radiation=22.0,
            latitude=70.0, day_of_year=180
        )
        
        # All should be positive
        assert et0_equator > 0 and et0_mid > 0 and et0_polar > 0
    
    def test_seasonal_variation(self, model):
        """Test seasonal ET0 variation."""
        et0_values = []
        for day in [1, 91, 181, 271]:  # Winter, Spring, Summer, Fall
            et0 = model.calculate_et0(
                temp_min=10.0, temp_max=20.0, humidity=60.0,
                wind_speed=2.0, solar_radiation=15.0,
                latitude=40.0, day_of_year=day
            )
            et0_values.append(et0)
        
        # ET0 should vary by season
        assert len(set(np.round(et0_values, 2))) > 1
    
    def test_zero_wind_speed(self, model):
        """Test ET0 with zero wind speed."""
        et0 = model.calculate_et0(
            temp_min=15.0, temp_max=25.0, humidity=60.0,
            wind_speed=0.0,  # Still conditions
            solar_radiation=20.0,
            latitude=40.0, day_of_year=180
        )
        
        # Should still calculate (use minimum wind speed)
        assert et0 > 0
    
    def test_extreme_humidity(self, model):
        """Test ET0 with extreme humidity values."""
        # Very dry
        et0_dry = model.calculate_et0(
            temp_min=15.0, temp_max=25.0, humidity=10.0,
            wind_speed=2.0, solar_radiation=20.0,
            latitude=40.0, day_of_year=180
        )
        
        # Very humid
        et0_humid = model.calculate_et0(
            temp_min=15.0, temp_max=25.0, humidity=95.0,
            wind_speed=2.0, solar_radiation=20.0,
            latitude=40.0, day_of_year=180
        )
        
        # Dry conditions should have higher ET0
        assert et0_dry > et0_humid
    
    def test_invalid_inputs(self, model):
        """Test handling of invalid inputs."""
        # These should either handle gracefully or raise ValueError
        with pytest.raises((ValueError, AssertionError)):
            model.calculate_et0(
                temp_min=25.0,
                temp_max=15.0,  # Max < Min (invalid)
                humidity=60.0,
                wind_speed=2.0,
                solar_radiation=20.0,
                latitude=40.0,
                day_of_year=180
            )
