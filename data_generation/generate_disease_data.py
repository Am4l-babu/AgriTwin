"""
Generate synthetic disease classification data for Random Forest
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger

def generate_disease_data(n_samples=800):
    """
    Generate disease classification data
    
    Args:
        n_samples: Total number of samples (divided equally among classes)
    
    Returns:
        DataFrame with synthetic disease data
    """
    logger.info(f"Generating {n_samples} disease samples...")
    np.random.seed(42)
    
    classes = ['Healthy', 'Powdery_Mildew', 'Blight', 'Nutrient_Deficiency']
    samples_per_class = n_samples // 4
    
    data = []
    
    for class_name in classes:
        logger.info(f"Generating {samples_per_class} samples for class: {class_name}")
        
        for i in range(samples_per_class):
            date = datetime(2024, 1, 1) + timedelta(days=np.random.randint(0, 90))
            days_since_planting = np.random.randint(20, 80)
            
            if class_name == 'Healthy':
                # Optimal conditions
                temp = np.random.normal(26, 3)
                humidity = np.random.normal(60, 8)
                leaf_wetness = np.random.normal(4, 2)
                ndvi = np.random.normal(0.75, 0.08)
            
            elif class_name == 'Powdery_Mildew':
                # High humidity, moderate temperature
                temp = np.random.normal(28, 2)
                humidity = np.random.normal(75, 5)
                leaf_wetness = np.random.normal(10, 3)
                ndvi = np.random.normal(0.60, 0.08)
            
            elif class_name == 'Blight':
                # Very high humidity, cooler temperature
                temp = np.random.normal(24, 2)
                humidity = np.random.normal(85, 5)
                leaf_wetness = np.random.normal(14, 3)
                ndvi = np.random.normal(0.50, 0.08)
            
            else:  # Nutrient_Deficiency
                # Normal conditions but low NDVI
                temp = np.random.normal(26, 3)
                humidity = np.random.normal(60, 8)
                leaf_wetness = np.random.normal(4, 2)
                ndvi = np.random.normal(0.45, 0.08)
            
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'temperature': round(temp, 1),
                'humidity': round(humidity, 1),
                'leaf_wetness_duration': round(max(0, leaf_wetness), 1),
                'ndvi': round(np.clip(ndvi, 0, 1), 2),
                'days_since_planting': days_since_planting,
                'disease_class': class_name
            })
    
    # Create DataFrame and shuffle
    df = pd.DataFrame(data)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    df.to_csv('disease_data_synthetic.csv', index=False)
    
    logger.success(f"✓ Generated {len(df):,} disease samples")
    logger.success(f"✓ Saved to: disease_data_synthetic.csv")
    
    return df

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("AgriTwin Synthetic Disease Data Generator")
    logger.info("=" * 60)
    
    # Generate data
    df = generate_disease_data(n_samples=800)
    
    # Display statistics
    logger.info("\n" + "=" * 60)
    logger.info("Dataset Statistics")
    logger.info("=" * 60)
    logger.info(f"\nFirst 5 rows:")
    print(df.head())
    
    logger.info(f"\nClass distribution:")
    print(df['disease_class'].value_counts())
    
    logger.info(f"\nFeature statistics by class:")
    print(df.groupby('disease_class')[['temperature', 'humidity', 'leaf_wetness_duration', 'ndvi']].mean())
    
    logger.success("\n✓ Synthetic disease data generation complete!")
