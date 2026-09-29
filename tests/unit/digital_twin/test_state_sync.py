import pytest
from cloud.digital_twin.twin_state_manager.state_sync import TwinStateManager
import numpy as np
from datetime import datetime


class TestTwinStateManager:
    """Unit tests for Digital Twin state synchronization."""
    
    @pytest.fixture
    def twin_manager(self):
        return TwinStateManager()
    
    def test_initialization(self, twin_manager):
        """Test TwinStateManager initialization."""
        assert twin_manager.physical_state == {}
        assert twin_manager.virtual_state == {}
        assert len(twin_manager.divergence_history) == 0
    
    def test_update_physical_state(self, twin_manager):
        """Test updating physical state from sensors."""
        sensor_data = {
            'soil_moisture': 45.2,
            'temperature': 22.5,
            'humidity': 65.0
        }
        
        twin_manager.update_physical_state(sensor_data)
        
        assert twin_manager.physical_state == sensor_data
    
    def test_update_virtual_state(self, twin_manager):
        """Test updating virtual state from simulation."""
        simulated_data = {
            'soil_moisture': 44.8,
            'temperature': 22.3,
            'humidity': 66.1
        }
        
        twin_manager.update_virtual_state(simulated_data)
        
        assert twin_manager.virtual_state == simulated_data
    
    def test_calculate_divergence_identical_states(self, twin_manager):
        """Test divergence calculation when states are identical."""
        state = {
            'soil_moisture': 45.0,
            'temperature': 22.0,
            'humidity': 65.0
        }
        
        twin_manager.update_physical_state(state)
        twin_manager.update_virtual_state(state)
        
        divergence = twin_manager.calculate_divergence()
        
        assert divergence == 0.0
    
    def test_calculate_divergence_different_states(self, twin_manager):
        """Test divergence calculation with different states."""
        physical = {
            'soil_moisture': 45.0,
            'temperature': 22.0,
            'humidity': 65.0
        }
        virtual = {
            'soil_moisture': 40.0,  # 5% difference
            'temperature': 23.0,    # 1°C difference
            'humidity': 70.0        # 5% difference
        }
        
        twin_manager.update_physical_state(physical)
        twin_manager.update_virtual_state(virtual)
        
        divergence = twin_manager.calculate_divergence()
        
        # Divergence should be positive
        assert divergence > 0
        assert divergence < 1.0  # Normalized RMSE should be < 1
    
    def test_divergence_threshold_detection(self, twin_manager):
        """Test detection of high divergence."""
        physical = {
            'soil_moisture': 50.0,
            'temperature': 25.0
        }
        virtual = {
            'soil_moisture': 30.0,  # 20% difference (high)
            'temperature': 15.0     # 10°C difference (high)
        }
        
        twin_manager.update_physical_state(physical)
        twin_manager.update_virtual_state(virtual)
        
        divergence = twin_manager.calculate_divergence()
        
        # Should exceed typical threshold (0.15)
        assert divergence > 0.15
    
    def test_divergence_history_tracking(self, twin_manager):
        """Test that divergence history is tracked."""
        for i in range(5):
            physical = {'soil_moisture': 50.0 + i}
            virtual = {'soil_moisture': 49.0 + i}
            
            twin_manager.update_physical_state(physical)
            twin_manager.update_virtual_state(virtual)
            twin_manager.calculate_divergence()
        
        assert len(twin_manager.divergence_history) == 5
    
    def test_divergence_history_limit(self, twin_manager):
        """Test that divergence history is limited to max size."""
        # Add more than max_history entries
        for i in range(1200):
            physical = {'soil_moisture': 50.0}
            virtual = {'soil_moisture': 49.0}
            
            twin_manager.update_physical_state(physical)
            twin_manager.update_virtual_state(virtual)
            twin_manager.calculate_divergence()
        
        # Should be limited to 1000
        assert len(twin_manager.divergence_history) <= 1000
    
    def test_get_state_snapshot(self, twin_manager):
        """Test getting complete state snapshot."""
        physical = {'soil_moisture': 45.0, 'temperature': 22.0}
        virtual = {'soil_moisture': 44.0, 'temperature': 22.5}
        
        twin_manager.update_physical_state(physical)
        twin_manager.update_virtual_state(virtual)
        divergence = twin_manager.calculate_divergence()
        
        snapshot = twin_manager.get_state_snapshot()
        
        assert 'physical_state' in snapshot
        assert 'virtual_state' in snapshot
        assert 'divergence_score' in snapshot
        assert 'timestamp' in snapshot
        assert snapshot['divergence_score'] == divergence
    
    def test_needs_recalibration(self, twin_manager):
        """Test recalibration detection."""
        # Low divergence - no recalibration needed
        physical = {'soil_moisture': 50.0}
        virtual = {'soil_moisture': 49.0}
        twin_manager.update_physical_state(physical)
        twin_manager.update_virtual_state(virtual)
        twin_manager.calculate_divergence()
        
        assert not twin_manager.needs_recalibration()
        
        # High divergence - recalibration needed
        physical = {'soil_moisture': 50.0}
        virtual = {'soil_moisture': 30.0}  # 20% difference
        twin_manager.update_physical_state(physical)
        twin_manager.update_virtual_state(virtual)
        twin_manager.calculate_divergence()
        
        assert twin_manager.needs_recalibration()
    
    def test_recalibrate_virtual_state(self, twin_manager):
        """Test virtual state recalibration to match physical."""
        physical = {'soil_moisture': 50.0, 'temperature': 25.0}
        virtual = {'soil_moisture': 30.0, 'temperature': 20.0}
        
        twin_manager.update_physical_state(physical)
        twin_manager.update_virtual_state(virtual)
        
        twin_manager.recalibrate()
        
        # Virtual should now match physical
        assert twin_manager.virtual_state == twin_manager.physical_state
        
        # Divergence should be zero after recalibration
        divergence = twin_manager.calculate_divergence()
        assert divergence == 0.0
    
    def test_partial_state_updates(self, twin_manager):
        """Test handling partial state updates."""
        # Initial full state
        twin_manager.update_physical_state({
            'soil_moisture': 50.0,
            'temperature': 25.0,
            'humidity': 65.0
        })
        
        # Partial update
        twin_manager.update_physical_state({
            'soil_moisture': 48.0
        })
        
        # Should merge, not replace
        assert twin_manager.physical_state['soil_moisture'] == 48.0
        assert twin_manager.physical_state['temperature'] == 25.0
        assert twin_manager.physical_state['humidity'] == 65.0
    
    def test_missing_sensors_in_divergence(self, twin_manager):
        """Test divergence calculation with mismatched sensors."""
        physical = {
            'soil_moisture': 50.0,
            'temperature': 25.0
        }
        virtual = {
            'soil_moisture': 49.0,
            'temperature': 24.0,
            'humidity': 65.0  # Extra sensor in virtual
        }
        
        twin_manager.update_physical_state(physical)
        twin_manager.update_virtual_state(virtual)
        
        # Should only compare common sensors
        divergence = twin_manager.calculate_divergence()
        assert divergence >= 0
    
    def test_empty_states_divergence(self, twin_manager):
        """Test divergence calculation with empty states."""
        divergence = twin_manager.calculate_divergence()
        
        # Should handle gracefully (return 0 or raise)
        assert divergence == 0.0 or divergence is None
    
    def test_normalization_ranges(self, twin_manager):
        """Test sensor range normalization for divergence."""
        # Soil moisture: 0-100%, temperature: -40 to 80°C
        # 10% difference in soil moisture vs 10°C in temperature
        # should be weighted differently
        
        physical = {
            'soil_moisture': 50.0,
            'temperature': 25.0
        }
        virtual = {
            'soil_moisture': 60.0,  # 10% diff (10% of 100 range)
            'temperature': 35.0     # 10°C diff (8.3% of 120 range)
        }
        
        twin_manager.update_physical_state(physical)
        twin_manager.update_virtual_state(virtual)
        
        divergence = twin_manager.calculate_divergence()
        
        # Check normalization is applied
        assert 0 < divergence < 0.5
    
    def test_state_prediction(self, twin_manager):
        """Test state prediction capability."""
        # Set current state
        twin_manager.update_physical_state({
            'soil_moisture': 50.0,
            'temperature': 25.0
        })
        
        # Predict future state (if method exists)
        if hasattr(twin_manager, 'predict_future_state'):
            future_state = twin_manager.predict_future_state(hours=24)
            
            assert 'soil_moisture' in future_state
            # Soil moisture should decrease over time (evaporation)
            assert future_state['soil_moisture'] < 50.0
    
    @pytest.mark.parametrize("physical,virtual,expected_high_divergence", [
        ({'sm': 50}, {'sm': 49}, False),    # Small diff
        ({'sm': 50}, {'sm': 30}, True),     # Large diff
        ({'t': 25}, {'t': 24}, False),      # Small diff
        ({'t': 25}, {'t': 40}, True),       # Large diff
    ])
    def test_divergence_scenarios(self, twin_manager, physical, virtual, expected_high_divergence):
        """Test various divergence scenarios."""
        twin_manager.update_physical_state(physical)
        twin_manager.update_virtual_state(virtual)
        divergence = twin_manager.calculate_divergence()
        
        is_high = divergence > 0.15
        assert is_high == expected_high_divergence
