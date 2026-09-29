"""
Generate synthetic anomaly data for Autoencoder training
"""

import numpy as np
import pandas as pd
from loguru import logger

def generate_anomaly_data(n_normal=10000, n_anomaly=500):
    """
    Generate normal + anomaly data for autoencoder
    
    Args:
        n_normal: Number of normal samples
        n_anomaly: Number of anomaly samples
    
    Returns:
        DataFrame with synthetic anomaly data
    """
    logger.info(f"Generating {n_normal} normal + {n_anomaly} anomaly samples...")
    np.random.seed(42)
    
    data = []
    
    # Generate normal data
    logger.info("Generating normal samples...")
    for i in range(n_normal):
        temp = np.random.normal(27, 4)
        humidity = np.random.normal(65, 10)
        light = np.random.normal(60, 15)
        soil = np.random.normal(45, 8)
        
        data.append({
            'temperature': round(temp, 1),
            'humidity': round(humidity, 1),
            'light': round(light, 1),
            'soil_moisture': round(soil, 1),
            'is_anomaly': 0,
            'anomaly_type': None
        })
        
        if (i + 1) % 2000 == 0:
            logger.info(f"Generated {i + 1}/{n_normal} normal samples")
    
    # Generate anomalies
    logger.info("Generating anomaly samples...")
    anomaly_types = ['sensor_failure', 'extreme_weather', 'irrigation_malfunction']
    
    for i in range(n_anomaly):
        anomaly_type = np.random.choice(anomaly_types)
        
        if anomaly_type == 'sensor_failure':
            # Sensor reading errors
            temp = np.random.choice([0, 99, -10, 150])
            humidity = np.random.choice([0, 100, 150])
            light = np.random.choice([0, 100])
            soil = np.random.choice([0, 100])
        
        elif anomaly_type == 'extreme_weather':
            # Heat wave / drought
            temp = np.random.normal(42, 3)
            humidity = np.random.normal(15, 5)
            light = np.random.normal(95, 3)
            soil = np.random.normal(15, 5)
        
        else:  # irrigation_malfunction
            # Irrigation system failure
            temp = np.random.normal(27, 4)
            humidity = np.random.normal(65, 10)
            light = np.random.normal(60, 15)
            soil = np.random.normal(10, 3)
        
        data.append({
            'temperature': round(temp, 1),
            'humidity': round(humidity, 1),
            'light': round(light, 1),
            'soil_moisture': round(soil, 1),
            'is_anomaly': 1,
            'anomaly_type': anomaly_type
        })
        
        if (i + 1) % 100 == 0:
            logger.info(f"Generated {i + 1}/{n_anomaly} anomaly samples")
    
    # Create DataFrame and shuffle
    df = pd.DataFrame(data)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    df.to_csv('anomaly_data_synthetic.csv', index=False)
    
    logger.success(f"✓ Generated {n_normal:,} normal + {n_anomaly:,} anomaly samples")
    logger.success(f"✓ Saved to: anomaly_data_synthetic.csv")
    
    return df

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("AgriTwin Synthetic Anomaly Data Generator")
    logger.info("=" * 60)
    
    # Generate data
    df = generate_anomaly_data(n_normal=10000, n_anomaly=500)
    
    # Display statistics
    logger.info("\n" + "=" * 60)
    logger.info("Dataset Statistics")
    logger.info("=" * 60)
    logger.info(f"\nFirst 5 rows:")
    print(df.head())
    
    logger.info(f"\nClass distribution:")
    print(df['is_anomaly'].value_counts())
    print(f"\nPercentage: {df['is_anomaly'].value_counts(normalize=True) * 100}")
    
    logger.info(f"\nAnomaly types:")
    print(df[df['is_anomaly']==1]['anomaly_type'].value_counts())
    
    logger.info(f"\nNormal data statistics:")
    print(df[df['is_anomaly']==0].describe())
    
    logger.success("\n✓ Synthetic anomaly data generation complete!")
