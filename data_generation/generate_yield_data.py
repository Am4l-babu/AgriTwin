"""
Generate synthetic yield data for LSTM training
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger

def generate_yield_data(n_samples=1200):
    """
    Generate yield data for LSTM training
    
    Args:
        n_samples: Number of yield samples to generate
    
    Returns:
        DataFrame with synthetic yield data
    """
    logger.info(f"Generating {n_samples} yield samples...")
    np.random.seed(42)
    
    data = []
    
    for i in range(n_samples):
        # Random harvest date (3 years of data)
        harvest_date = datetime(2021, 1, 1) + timedelta(days=np.random.randint(0, 1095))
        
        # Crop parameters
        crop_type = 'tomato'
        days_to_harvest = np.random.randint(80, 100)
        
        # Weather conditions (affect yield)
        avg_temp = np.random.normal(26, 3)
        avg_humidity = np.random.normal(65, 10)
        avg_light = np.random.normal(60, 15)
        avg_soil = np.random.normal(45, 8)
        
        # Irrigation
        total_irrigation = np.random.normal(400, 80)
        
        # Growing Degree Days
        accumulated_gdd = (avg_temp - 10) * days_to_harvest
        
        # Yield calculation (with realistic correlation)
        base_yield = 5000
        temp_factor = 1 - abs(avg_temp - 27) * 0.02
        water_factor = 1 - abs(avg_soil - 45) * 0.01
        light_factor = avg_light / 70
        
        yield_kg = base_yield * temp_factor * water_factor * light_factor
        yield_kg += np.random.normal(0, 300)  # Random variation
        yield_kg = np.clip(yield_kg, 3000, 7000)
        
        data.append({
            'harvest_date': harvest_date.strftime('%Y-%m-%d'),
            'farm_id': 'farm_001',
            'crop_type': crop_type,
            'yield_kg': round(yield_kg, 2),
            'days_to_harvest': days_to_harvest,
            'avg_temperature': round(avg_temp, 1),
            'avg_humidity': round(avg_humidity, 1),
            'avg_light': round(avg_light, 1),
            'avg_soil_moisture': round(avg_soil, 1),
            'total_irrigation': round(total_irrigation, 1),
            'accumulated_gdd': round(accumulated_gdd, 1),
            'growth_stage_at_harvest': 'mature'
        })
        
        # Progress indicator
        if (i + 1) % 200 == 0:
            logger.info(f"Generated {i + 1}/{n_samples} samples")
    
    df = pd.DataFrame(data)
    df.to_csv('yield_data_synthetic.csv', index=False)
    
    logger.success(f"✓ Generated {len(df):,} yield samples")
    logger.success(f"✓ Saved to: yield_data_synthetic.csv")
    
    return df

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("AgriTwin Synthetic Yield Data Generator")
    logger.info("=" * 60)
    
    # Generate data
    df = generate_yield_data(n_samples=1200)
    
    # Display statistics
    logger.info("\n" + "=" * 60)
    logger.info("Dataset Statistics")
    logger.info("=" * 60)
    logger.info(f"\nFirst 5 rows:")
    print(df.head())
    
    logger.info(f"\nYield statistics:")
    print(df['yield_kg'].describe())
    
    logger.info(f"\nCorrelation with yield:")
    correlations = df.corr()['yield_kg'].sort_values(ascending=False)
    print(correlations)
    
    logger.success("\n✓ Synthetic yield data generation complete!")
