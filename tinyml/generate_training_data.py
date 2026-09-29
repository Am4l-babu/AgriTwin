"""
Generate Synthetic Training Data for Soil Moisture Prediction

Creates realistic sensor data with:
- Day/night temperature cycles
- Humidity patterns
- Light level variations
- Soil moisture dynamics (evaporation, irrigation)
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os


def generate_day_night_cycle(hours, base_temp=25, amplitude=8):
    """Generate realistic temperature with day/night cycle"""
    # Sine wave with peak at 2pm (14:00)
    time_radians = (hours - 14) * 2 * np.pi / 24
    temp = base_temp + amplitude * np.cos(time_radians)
    # Add some noise
    temp += np.random.normal(0, 1, len(hours))
    return temp


def generate_humidity(temperature, base_humidity=60):
    """Generate humidity inversely correlated with temperature"""
    # Higher temp = lower humidity (generally)
    humidity = base_humidity + (25 - temperature) * 1.5
    humidity += np.random.normal(0, 3, len(temperature))
    humidity = np.clip(humidity, 20, 95)
    return humidity


def generate_light_level(hours):
    """Generate light level based on time of day"""
    light = np.zeros(len(hours))
    for i, hour in enumerate(hours):
        if 6 <= hour <= 18:  # Daylight hours
            # Peak at noon
            peak_hour = 12
            distance_from_peak = abs(hour - peak_hour)
            light[i] = 100 * (1 - distance_from_peak / 6) ** 2
        else:
            light[i] = 0  # Night
        
        # Add clouds/weather variation
        light[i] *= np.random.uniform(0.7, 1.0)
        light[i] += np.random.normal(0, 5)
    
    light = np.clip(light, 0, 100)
    return light


def simulate_soil_moisture(
    n_samples,
    initial_moisture=60,
    evaporation_rate=0.5,
    irrigation_threshold=30,
    irrigation_amount=40
):
    """
    Simulate soil moisture dynamics
    
    - Evaporation reduces moisture over time
    - Irrigation events when moisture drops below threshold
    - Temperature and light affect evaporation rate
    """
    moisture = np.zeros(n_samples)
    moisture[0] = initial_moisture
    
    for i in range(1, n_samples):
        # Previous moisture
        prev_moisture = moisture[i-1]
        
        # Evaporation (higher in day, lower at night)
        hour = i % 24
        if 8 <= hour <= 18:
            evap = evaporation_rate * np.random.uniform(0.8, 1.2)
        else:
            evap = evaporation_rate * 0.3 * np.random.uniform(0.8, 1.2)
        
        # Update moisture
        new_moisture = prev_moisture - evap
        
        # Irrigation event
        if new_moisture < irrigation_threshold:
            new_moisture += irrigation_amount
        
        # Add noise
        new_moisture += np.random.normal(0, 0.5)
        
        # Clip to valid range
        moisture[i] = np.clip(new_moisture, 10, 100)
    
    return moisture


def generate_dataset(n_days=30, samples_per_hour=4):
    """
    Generate complete training dataset
    
    Args:
        n_days: Number of days to simulate
        samples_per_hour: Samples per hour (4 = every 15 minutes)
    
    Returns:
        DataFrame with sensor readings
    """
    n_samples = n_days * 24 * samples_per_hour
    
    print(f"Generating {n_samples} samples ({n_days} days)...")
    
    # Time array
    start_time = datetime(2024, 1, 1, 0, 0, 0)
    timestamps = [start_time + timedelta(minutes=15*i) for i in range(n_samples)]
    hours = np.array([t.hour + t.minute/60 for t in timestamps])
    
    # Generate sensor data
    print("Generating temperature...")
    temperature = generate_day_night_cycle(hours)
    
    print("Generating humidity...")
    humidity = generate_humidity(temperature)
    
    print("Generating light level...")
    light_level = generate_light_level(hours)
    
    print("Simulating soil moisture...")
    soil_moisture = simulate_soil_moisture(n_samples)
    
    # Create DataFrame
    df = pd.DataFrame({
        'timestamp': timestamps,
        'hour': hours,
        'temperature': temperature,
        'humidity': humidity,
        'light_level': light_level,
        'soil_moisture': soil_moisture
    })
    
    # Add derived features
    df['temp_humidity_interaction'] = df['temperature'] * df['humidity'] / 100
    df['vpd'] = calculate_vpd(df['temperature'], df['humidity'])
    
    return df


def calculate_vpd(temperature, humidity):
    """Calculate Vapor Pressure Deficit"""
    # Saturation vapor pressure (kPa)
    svp = 0.6108 * np.exp(17.27 * temperature / (temperature + 237.3))
    # Actual vapor pressure
    avp = svp * humidity / 100
    # VPD
    vpd = svp - avp
    return vpd


def create_sequences(df, lookback=4, forecast_horizon=1):
    """
    Create sequences for time-series prediction
    
    Args:
        df: DataFrame with sensor data
        lookback: Number of past timesteps to use
        forecast_horizon: Steps ahead to predict
    
    Returns:
        X, y arrays for training
    """
    features = ['temperature', 'humidity', 'light_level', 'hour']
    target = 'soil_moisture'
    
    X, y = [], []
    
    for i in range(lookback, len(df) - forecast_horizon):
        # Input: past lookback timesteps
        X.append(df[features].iloc[i-lookback:i].values)
        # Output: future soil moisture
        y.append(df[target].iloc[i + forecast_horizon - 1])
    
    return np.array(X), np.array(y)


def main():
    """Generate and save training data"""
    
    # Create data directory
    os.makedirs('data', exist_ok=True)
    
    # Generate training data (30 days)
    print("\n=== Generating Training Data ===")
    train_df = generate_dataset(n_days=30, samples_per_hour=4)
    train_df.to_csv('data/training_data.csv', index=False)
    print(f"✓ Saved training data: {len(train_df)} samples")
    
    # Generate test data (7 days)
    print("\n=== Generating Test Data ===")
    test_df = generate_dataset(n_days=7, samples_per_hour=4)
    test_df.to_csv('data/test_data.csv', index=False)
    print(f"✓ Saved test data: {len(test_df)} samples")
    
    # Statistics
    print("\n=== Dataset Statistics ===")
    print(train_df.describe())
    
    print("\n=== Sample Data ===")
    print(train_df.head(10))
    
    print("\n✓ Data generation complete!")
    print(f"  Training: data/training_data.csv ({len(train_df)} samples)")
    print(f"  Test: data/test_data.csv ({len(test_df)} samples)")


if __name__ == "__main__":
    main()
