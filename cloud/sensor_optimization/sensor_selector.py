# Sensor selector - Helper for sensor selection

from typing import List, Dict, Any, Tuple
import numpy as np


class SensorSelector:
    """
    Helper class for sensor selection and placement
    """
    
    @staticmethod
    def generate_grid_locations(field_width: float, field_height: float,
                               grid_size: int = 3) -> List[Tuple[float, float]]:
        """
        Generate grid of candidate sensor locations
        
        Args:
            field_width: Field width in meters
            field_height: Field height in meters
            grid_size: Grid size (e.g., 3x3 = 9 locations)
        
        Returns:
            List of (x, y) coordinates
        """
        locations = []
        x_step = field_width / (grid_size + 1)
        y_step = field_height / (grid_size + 1)
        
        for i in range(1, grid_size + 1):
            for j in range(1, grid_size + 1):
                x = i * x_step
                y = j * y_step
                locations.append((x, y))
        
        return locations
    
    @staticmethod
    def calculate_coverage(selected_locations: List[Tuple[float, float]],
                          field_width: float, field_height: float,
                          sensor_range: float = 10.0) -> float:
        """
        Calculate field coverage percentage
        
        Args:
            selected_locations: Selected sensor locations
            field_width: Field width
            field_height: Field height
            sensor_range: Sensor coverage radius
        
        Returns:
            Coverage percentage (0-100)
        """
        # Create grid of points to check
        grid_resolution = 50
        x_points = np.linspace(0, field_width, grid_resolution)
        y_points = np.linspace(0, field_height, grid_resolution)
        
        covered_points = 0
        total_points = grid_resolution * grid_resolution
        
        for x in x_points:
            for y in y_points:
                # Check if point is within range of any sensor
                for sensor_x, sensor_y in selected_locations:
                    distance = np.sqrt((x - sensor_x)**2 + (y - sensor_y)**2)
                    if distance <= sensor_range:
                        covered_points += 1
                        break
        
        coverage = (covered_points / total_points) * 100
        return coverage
    
    @staticmethod
    def recommend_sensor_count(field_area: float, sensor_range: float = 10.0) -> int:
        """
        Recommend number of sensors based on field size
        
        Args:
            field_area: Field area in square meters
            sensor_range: Sensor coverage radius
        
        Returns:
            Recommended sensor count
        """
        # Coverage area per sensor
        coverage_per_sensor = np.pi * (sensor_range ** 2)
        
        # Minimum sensors needed for full coverage
        min_sensors = int(np.ceil(field_area / coverage_per_sensor))
        
        # Thompson Sampling can reduce by ~82%
        recommended = max(2, int(min_sensors * 0.18))
        
        return recommended
    
    @staticmethod
    def validate_placement(locations: List[Tuple[float, float]],
                          min_distance: float = 5.0) -> Dict[str, Any]:
        """
        Validate sensor placement (check minimum distance)
        
        Args:
            locations: Sensor locations
            min_distance: Minimum distance between sensors
        
        Returns:
            Validation result
        """
        issues = []
        
        for i, loc1 in enumerate(locations):
            for j, loc2 in enumerate(locations[i+1:], i+1):
                distance = np.sqrt(
                    (loc1[0] - loc2[0])**2 + 
                    (loc1[1] - loc2[1])**2
                )
                if distance < min_distance:
                    issues.append(
                        f"Sensors {i} and {j} too close: {distance:.1f}m "
                        f"(min: {min_distance}m)"
                    )
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "sensor_count": len(locations)
        }
