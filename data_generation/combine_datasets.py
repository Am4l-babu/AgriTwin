"""
Combine real and synthetic sensor data
"""

import pandas as pd
from loguru import logger
import os

def combine_datasets():
    """
    Combine real ESP32 data with synthetic data
    """
    logger.info("=" * 60)
    logger.info("Combining Real + Synthetic Datasets")
    logger.info("=" * 60)
    
    # Check if real data exists
    if not os.path.exists('sensor_data_real.csv'):
        logger.warning("Real data file not found: sensor_data_real.csv")
        logger.warning("Make sure you've collected data from ESP32 for 24-48 hours")
        logger.info("Using only synthetic data for now...")
        
        # Load synthetic data only
        df_synthetic = pd.read_csv('sensor_data_synthetic_90days.csv')
        logger.info(f"Synthetic data: {len(df_synthetic):,} rows")
        
        df_combined = df_synthetic
    else:
        # Load real data
        df_real = pd.read_csv('sensor_data_real.csv')
        logger.success(f"✓ Real data loaded: {len(df_real):,} rows")
        
        # Load synthetic data
        df_synthetic = pd.read_csv('sensor_data_synthetic_90days.csv')
        logger.success(f"✓ Synthetic data loaded: {len(df_synthetic):,} rows")
        
        # Combine
        df_combined = pd.concat([df_real, df_synthetic], ignore_index=True)
        
        # Sort by timestamp
        df_combined['timestamp'] = pd.to_datetime(df_combined['timestamp'])
        df_combined = df_combined.sort_values('timestamp').reset_index(drop=True)
    
    # Save combined dataset
    df_combined.to_csv('sensor_data_combined.csv', index=False)
    
    logger.success(f"\n✓ Combined dataset: {len(df_combined):,} rows")
    logger.success(f"✓ Saved to: sensor_data_combined.csv")
    
    # Display statistics
    logger.info("\n" + "=" * 60)
    logger.info("Combined Dataset Statistics")
    logger.info("=" * 60)
    logger.info(f"\nFirst 5 rows:")
    print(df_combined.head())
    
    logger.info(f"\nLast 5 rows:")
    print(df_combined.tail())
    
    logger.info(f"\nStatistical Summary:")
    print(df_combined.describe())
    
    logger.info(f"\nMissing values:")
    print(df_combined.isnull().sum())
    
    logger.info(f"\nData types:")
    print(df_combined.dtypes)
    
    # File size
    file_size_mb = os.path.getsize('sensor_data_combined.csv') / 1024 / 1024
    logger.info(f"\nFile size: {file_size_mb:.2f} MB")
    
    logger.success("\n✓ Dataset combination complete!")
    logger.info("\nNext steps:")
    logger.info("1. Use this combined dataset for ML model training")
    logger.info("2. Train LSTM model with yield_data_synthetic.csv")
    logger.info("3. Train Autoencoder with anomaly_data_synthetic.csv")
    logger.info("4. Train Random Forest with disease_data_synthetic.csv")

if __name__ == "__main__":
    combine_datasets()
