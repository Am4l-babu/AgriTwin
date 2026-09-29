"""
Unit Tests for Digital Twin Physics Model

Tests water balance, ET calculations, and crop growth model.
"""

import unittest
from cloud.digital_twin.physics_model.comprehensive_physics import (
    WaterBalanceModel,
    SoilProperties,
    WeatherData,
    CropGrowthModel,
    DigitalTwinPhysics
)


class TestWaterBalanceModel(unittest.TestCase):
    """Test water balance calculations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.soil = SoilProperties()
        self.model = WaterBalanceModel(self.soil)
    
    def test_et_calculation(self):
        """Test evapotranspiration calculation"""
        weather = WeatherData(
            temperature=25.0,
            humidity=60.0,
            solar_radiation=20.0,
            wind_speed=2.0,
            precipitation=0.0
        )
        
        et = self.model.calculate_evapotranspiration(weather)
        
        # ET should be positive
        self.assertGreater(et, 0)
        # ET should be reasonable (0-10 mm/day)
        self.assertLess(et, 10)
    
    def test_water_balance_no_irrigation(self):
        """Test water balance without irrigation"""
        weather = WeatherData(
            temperature=25.0,
            humidity=60.0,
            solar_radiation=20.0,
            wind_speed=2.0,
            precipitation=0.0
        )
        
        initial_moisture = self.model.current_moisture
        state = self.model.update(weather, irrigation=0.0)
        
        # Moisture should decrease without rain or irrigation
        self.assertLess(self.model.current_moisture, initial_moisture)
        self.assertIn('moisture', state)
        self.assertIn('evapotranspiration', state)
    
    def test_water_balance_with_irrigation(self):
        """Test water balance with irrigation"""
        weather = WeatherData(
            temperature=25.0,
            humidity=60.0,
            solar_radiation=20.0,
            wind_speed=2.0,
            precipitation=0.0
        )
        
        # Deplete moisture first
        for _ in range(5):
            self.model.update(weather, irrigation=0.0)
        
        initial_moisture = self.model.current_moisture
        state = self.model.update(weather, irrigation=10.0)
        
        # Moisture should increase with irrigation
        self.assertGreater(self.model.current_moisture, initial_moisture)
    
    def test_irrigation_needed(self):
        """Test irrigation need detection"""
        # Set low moisture
        self.model.current_moisture = self.soil.wilting_point + 0.05
        
        # Should need irrigation
        self.assertTrue(self.model.is_irrigation_needed(threshold=0.6))
        
        # Set high moisture
        self.model.current_moisture = self.soil.field_capacity
        
        # Should not need irrigation
        self.assertFalse(self.model.is_irrigation_needed(threshold=0.6))


class TestCropGrowthModel(unittest.TestCase):
    """Test crop growth calculations"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.model = CropGrowthModel(
            crop_name="Tomato",
            base_temp=10.0,
            max_temp=30.0,
            gdd_to_maturity=1500.0
        )
    
    def test_gdd_calculation(self):
        """Test growing degree days calculation"""
        # Below base temp
        gdd = self.model.calculate_gdd(5.0)
        self.assertEqual(gdd, 0.0)
        
        # Above base temp
        gdd = self.model.calculate_gdd(20.0)
        self.assertEqual(gdd, 10.0)
        
        # Above max temp
        gdd = self.model.calculate_gdd(35.0)
        self.assertEqual(gdd, 20.0)
    
    def test_growth_stages(self):
        """Test growth stage progression"""
        # Start in vegetative
        state = self.model.update(20.0)
        self.assertEqual(state['growth_stage'], 'vegetative')
        
        # Accumulate GDD to flowering
        self.model.accumulated_gdd = 400
        state = self.model.update(20.0)
        self.assertEqual(state['growth_stage'], 'flowering')
        
        # Accumulate to maturity
        self.model.accumulated_gdd = 1500
        state = self.model.update(20.0)
        self.assertEqual(state['growth_stage'], 'mature')


class TestDigitalTwinPhysics(unittest.TestCase):
    """Test complete digital twin simulation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.twin = DigitalTwinPhysics()
    
    def test_simulate_step(self):
        """Test single simulation step"""
        sensor_data = {
            'soil': 50.0,
            'temp': 25.0,
            'humidity': 60.0,
            'light': 600
        }
        
        state = self.twin.simulate_step(sensor_data)
        
        # Check state structure
        self.assertIn('water', state)
        self.assertIn('crop', state)
        self.assertIn('weather', state)
        self.assertIn('recommendations', state)
    
    def test_recommendations_generation(self):
        """Test recommendation generation"""
        # Simulate dry conditions
        self.twin.water_balance.current_moisture = self.twin.soil.wilting_point + 0.05
        
        sensor_data = {
            'soil': 20.0,
            'temp': 30.0,
            'humidity': 40.0,
            'light': 800
        }
        
        state = self.twin.simulate_step(sensor_data)
        
        # Should have irrigation recommendation
        recommendations = state['recommendations']
        self.assertGreater(len(recommendations), 0)
        
        # Check for irrigation recommendation
        has_irrigation_rec = any(r['type'] == 'irrigation' for r in recommendations)
        self.assertTrue(has_irrigation_rec)


if __name__ == '__main__':
    unittest.main()
