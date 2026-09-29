"""
Generate realistic synthetic sensor data for 90 days
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger

def generate_sensor_data(days=90, start_date='2024-01-01'):
    """
    Generate realistic sensor data for specified number of days
    
    Args:
        days: Number of days to generate (default: 90)
        start_date: Start date for data generation
    
    Returns:
        DataFrame with synthetic sensor data
    """
    logger.info(f"Generating {days} days of synthetic sensor data...")
    np.random.seed(42)
    
    # Time range (every 10 seconds)
    start = pd.to_datetime(start_date)
    timestamps = [start + timedelta(seconds=10*i) for i in range(days * 8640)]
    
    data = []
    
    for i, ts in enumerate(timestamps):
        hour = ts.hour
        day = (ts - start).days
        
        # Diurnal temperature pattern (15-35°C)
        base_temp = 25 + 8 * np.sin((hour - 6) * np.pi / 12)
        temp = base_temp + np.random.normal(0, 1.5)
        temp = np.clip(temp, 15, 40)
        
        # Humidity inversely correlated with temperature
        base_humidity = 80 - (temp - 20) * 2
        humidity = base_humidity + np.random.normal(0, 5)
        humidity = np.clip(humidity, 30, 95)
        
        # Light follows sunrise/sunset (0-100%)
        if 6 <= hour <= 18:
            base_light = 50 + 40 * np.sin((hour - 6) * np.pi / 12)
        else:
            base_light = 5
        light = base_light + np.random.normal(0, 5)
        light = np.clip(light, 0, 100)
        
        # Soil moisture decays over time (irrigation every 2-3 days)
        days_since_irrigation = day % 3
        soil = 60 - days_since_irrigation * 8 + np.random.normal(0, 3)
        soil = np.clip(soil, 25, 70)
        
        # System metrics
        rssi = -40 + np.random.normal(0, 5)
        free_heap = 250000 + np.random.normal(0, 10000)
        uptime = i * 10
        
        data.append({
            'timestamp': ts,
            'device_id': 'esp32_001',
            'farm_id': 'farm_001',
            'temperature': round(temp, 1),
            'humidity': round(humidity, 1),
            'light_level': round(light, 1),
            'soil_moisture': round(soil, 1),
            'rssi': int(rssi),
            'free_heap': int(free_heap),
            'uptime': uptime
        })
        
        # Progress indicator
        if (i + 1) % 86400 == 0:
            logger.info(f"Generated day {(i + 1) // 8640}/{days}")
    
    df = pd.DataFrame(data)
    df.to_csv('sensor_data_synthetic_90days.csv', index=False)
    
    logger.success(f"✓ Generated {len(df):,} sensor readings ({days} days)")
    logger.success(f"✓ Saved to: sensor_data_synthetic_90days.csv")
    logger.info(f"✓ File size: {os.path.getsize('sensor_data_synthetic_90days.csv') / 1024 / 1024:.2f} MB")
    
    return df

if __name__ == "__main__":
    import os
    
    logger.info("=" * 60)
    logger.info("AgriTwin Synthetic Sensor Data Generator")
    logger.info("=" * 60)
    
    # Generate data
    df = generate_sensor_data(days=90)
    
    # Display statistics
    logger.info("\n" + "=" * 60)
    logger.info("Dataset Statistics")
    logger.info("=" * 60)
    logger.info(f"\nFirst 5 rows:")
    print(df.head())
    
    logger.info(f"\nLast 5 rows:")
    print(df.tail())
    
    logger.info(f"\nStatistical Summary:")
    print(df.describe())
    
    logger.info(f"\nData Types:")
    print(df.dtypes)
    
    logger.success("\n✓ Synthetic sensor data generation complete!")
