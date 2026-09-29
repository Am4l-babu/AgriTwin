"""
Check status of data collection and datasets
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger

def check_file(filename, expected_rows=None):
    """Check if file exists and show statistics"""
    if not os.path.exists(filename):
        logger.warning(f"✗ {filename} - Not found")
        return False
    
    try:
        # Get file size
        size_mb = os.path.getsize(filename) / 1024 / 1024
        
        # Load and analyze
        df = pd.read_csv(filename)
        rows = len(df)
        
        # Status
        status = "✓"
        if expected_rows and rows < expected_rows:
            status = "⚠"
        
        logger.info(f"{status} {filename}")
        logger.info(f"  Rows: {rows:,}")
        logger.info(f"  Size: {size_mb:.2f} MB")
        
        # Check timestamps if available
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            start = df['timestamp'].min()
            end = df['timestamp'].max()
            duration = end - start
            
            logger.info(f"  Start: {start}")
            logger.info(f"  End: {end}")
            logger.info(f"  Duration: {duration}")
            
            # Calculate collection rate
            if duration.total_seconds() > 0:
                rate = rows / (duration.total_seconds() / 3600)
                logger.info(f"  Rate: {rate:.1f} readings/hour")
        
        # Check for missing values
        missing = df.isnull().sum().sum()
        if missing > 0:
            logger.warning(f"  Missing values: {missing}")
        
        return True
    
    except Exception as e:
        logger.error(f"✗ {filename} - Error: {e}")
        return False

def estimate_completion(filename):
    """Estimate when data collection will be complete"""
    if not os.path.exists(filename):
        return
    
    try:
        df = pd.read_csv(filename)
        if 'timestamp' in df.columns and len(df) > 0:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            start = df['timestamp'].min()
            end = df['timestamp'].max()
            duration = end - start
            
            # Target: 24 hours = 8,640 readings
            target_hours = 24
            target_readings = 8640
            
            current_hours = duration.total_seconds() / 3600
            current_readings = len(df)
            
            if current_hours > 0:
                rate = current_readings / current_hours
                remaining_readings = target_readings - current_readings
                
                if remaining_readings > 0:
                    remaining_hours = remaining_readings / rate
                    completion_time = datetime.now() + timedelta(hours=remaining_hours)
                    
                    logger.info(f"\n📊 Collection Progress:")
                    logger.info(f"  Current: {current_readings:,} / {target_readings:,} readings ({current_readings/target_readings*100:.1f}%)")
                    logger.info(f"  Elapsed: {current_hours:.1f} / {target_hours} hours")
                    logger.info(f"  Remaining: {remaining_hours:.1f} hours")
                    logger.info(f"  Estimated completion: {completion_time.strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    logger.success(f"\n✓ Target reached! Collected {current_readings:,} readings in {current_hours:.1f} hours")
    
    except Exception as e:
        logger.error(f"Error estimating completion: {e}")

def main():
    """Check status of all datasets"""
    logger.info("=" * 60)
    logger.info("AgriTwin Data Collection Status")
    logger.info("=" * 60)
    logger.info(f"Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Check real data
    logger.info("Real Data (from ESP32):")
    logger.info("-" * 60)
    real_exists = check_file('sensor_data_real.csv', expected_rows=8640)
    
    if real_exists:
        estimate_completion('sensor_data_real.csv')
    else:
        logger.warning("\n⚠ Real data collection not started yet")
        logger.info("Start with: python collect_data.py")
    
    # Check synthetic data
    logger.info("\n" + "=" * 60)
    logger.info("Synthetic Data:")
    logger.info("-" * 60)
    
    synthetic_files = [
        ('sensor_data_synthetic_90days.csv', 777600),
        ('yield_data_synthetic.csv', 1200),
        ('anomaly_data_synthetic.csv', 10500),
        ('disease_data_synthetic.csv', 800)
    ]
    
    synthetic_count = 0
    for filename, expected in synthetic_files:
        if check_file(filename, expected):
            synthetic_count += 1
        logger.info("")
    
    if synthetic_count == 0:
        logger.warning("⚠ No synthetic data generated yet")
        logger.info("Generate with: python run_all_generators.py")
    elif synthetic_count < len(synthetic_files):
        logger.warning(f"⚠ Only {synthetic_count}/{len(synthetic_files)} synthetic datasets generated")
        logger.info("Generate missing datasets with: python run_all_generators.py")
    else:
        logger.success(f"✓ All {len(synthetic_files)} synthetic datasets generated")
    
    # Check combined data
    logger.info("=" * 60)
    logger.info("Combined Data:")
    logger.info("-" * 60)
    
    if check_file('sensor_data_combined.csv'):
        logger.success("\n✓ Combined dataset ready for ML training")
    else:
        logger.info("\n⚠ Combined dataset not created yet")
        if real_exists and synthetic_count > 0:
            logger.info("Combine with: python combine_datasets.py")
        else:
            logger.info("First complete real data collection and generate synthetic data")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Summary")
    logger.info("=" * 60)
    
    if real_exists and synthetic_count == len(synthetic_files):
        logger.success("✓ All datasets ready!")
        logger.info("\nNext steps:")
        logger.info("1. If real data collection is complete (24+ hours), stop it")
        logger.info("2. Combine datasets: python combine_datasets.py")
        logger.info("3. Start ML model training")
    elif real_exists:
        logger.info("⚠ Real data collection in progress")
        logger.info("\nNext steps:")
        logger.info("1. Wait for 24-48 hours of data collection")
        logger.info("2. Generate synthetic data: python run_all_generators.py")
    elif synthetic_count > 0:
        logger.info("⚠ Synthetic data ready, but no real data yet")
        logger.info("\nNext steps:")
        logger.info("1. Start data collection: python collect_data.py")
        logger.info("2. Wait for 24-48 hours")
    else:
        logger.warning("⚠ No datasets found")
        logger.info("\nNext steps:")
        logger.info("1. Generate synthetic data: python run_all_generators.py")
        logger.info("2. Start data collection: python collect_data.py")

if __name__ == "__main__":
    main()
