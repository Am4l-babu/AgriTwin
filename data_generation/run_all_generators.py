"""
Run all synthetic data generators at once
"""

from loguru import logger
import subprocess
import sys

def run_script(script_name):
    """Run a Python script and capture output"""
    logger.info(f"\n{'=' * 60}")
    logger.info(f"Running: {script_name}")
    logger.info(f"{'=' * 60}\n")
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=False,
            text=True,
            check=True
        )
        logger.success(f"✓ {script_name} completed successfully\n")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ {script_name} failed with error code {e.returncode}\n")
        return False

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("AgriTwin - Generate All Synthetic Datasets")
    logger.info("=" * 60)
    logger.info("\nThis will generate 4 synthetic datasets:")
    logger.info("1. Sensor data (90 days, 777,600 rows)")
    logger.info("2. Yield data (1,200 samples)")
    logger.info("3. Anomaly data (10,500 samples)")
    logger.info("4. Disease data (800 samples)")
    logger.info("\nEstimated time: 2-3 minutes")
    logger.info("=" * 60)
    
    input("\nPress Enter to start generation...")
    
    scripts = [
        'generate_synthetic_data.py',
        'generate_yield_data.py',
        'generate_anomaly_data.py',
        'generate_disease_data.py'
    ]
    
    results = []
    for script in scripts:
        success = run_script(script)
        results.append((script, success))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Generation Summary")
    logger.info("=" * 60)
    
    for script, success in results:
        status = "✓ SUCCESS" if success else "✗ FAILED"
        logger.info(f"{status}: {script}")
    
    all_success = all(success for _, success in results)
    
    if all_success:
        logger.success("\n✓ All datasets generated successfully!")
        logger.info("\nGenerated files:")
        logger.info("- sensor_data_synthetic_90days.csv")
        logger.info("- yield_data_synthetic.csv")
        logger.info("- anomaly_data_synthetic.csv")
        logger.info("- disease_data_synthetic.csv")
        logger.info("\nNext steps:")
        logger.info("1. Start collecting real data: python collect_data.py")
        logger.info("2. After 24-48 hours, combine datasets: python combine_datasets.py")
        logger.info("3. Train ML models with combined data")
    else:
        logger.error("\n✗ Some datasets failed to generate")
        logger.info("Check the error messages above and try again")
