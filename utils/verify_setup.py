"""
Verify AgriTwin setup and check readiness for data collection
"""

import os
import sys
from loguru import logger

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        logger.success(f"✓ Python version: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        logger.error(f"✗ Python version too old: {version.major}.{version.minor}.{version.micro}")
        logger.error("  Required: Python 3.8 or higher")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    required = ['paho.mqtt', 'numpy', 'pandas', 'loguru']
    missing = []
    
    for package in required:
        try:
            __import__(package.replace('.', '_'))
            logger.success(f"✓ {package} installed")
        except ImportError:
            logger.error(f"✗ {package} not installed")
            missing.append(package)
    
    if missing:
        logger.error("\nInstall missing packages:")
        logger.error("pip install -r requirements_data.txt")
        return False
    
    return True

def check_scripts():
    """Check if all required scripts exist"""
    scripts = [
        'collect_data.py',
        'generate_synthetic_data.py',
        'generate_yield_data.py',
        'generate_anomaly_data.py',
        'generate_disease_data.py',
        'combine_datasets.py',
        'run_all_generators.py'
    ]
    
    all_exist = True
    for script in scripts:
        if os.path.exists(script):
            logger.success(f"✓ {script}")
        else:
            logger.error(f"✗ {script} not found")
            all_exist = False
    
    return all_exist

def check_firmware():
    """Check if ESP32 firmware exists"""
    firmware_path = 'edge/src/main.cpp'
    if os.path.exists(firmware_path):
        logger.success(f"✓ ESP32 firmware: {firmware_path}")
        return True
    else:
        logger.error(f"✗ ESP32 firmware not found: {firmware_path}")
        return False

def check_mqtt_broker():
    """Check if MQTT broker is accessible"""
    try:
        import paho.mqtt.client as mqtt
        
        broker = "192.168.1.2"
        port = 1883
        
        logger.info(f"Testing MQTT connection to {broker}:{port}...")
        
        client = mqtt.Client()
        client.connect(broker, port, 60)
        client.disconnect()
        
        logger.success(f"✓ MQTT broker accessible at {broker}:{port}")
        return True
    
    except Exception as e:
        logger.warning(f"⚠ MQTT broker not accessible: {e}")
        logger.warning("  Make sure MQTT broker is running:")
        logger.warning("  - Docker: docker run -d -p 1883:1883 eclipse-mosquitto:2.0")
        logger.warning("  - Windows: net start mosquitto")
        logger.warning("  - Linux: sudo systemctl start mosquitto")
        return False

def check_disk_space():
    """Check available disk space"""
    try:
        import shutil
        stat = shutil.disk_usage('.')
        free_gb = stat.free / (1024 ** 3)
        
        if free_gb >= 1:
            logger.success(f"✓ Disk space: {free_gb:.2f} GB available")
            return True
        else:
            logger.warning(f"⚠ Low disk space: {free_gb:.2f} GB available")
            logger.warning("  Recommended: At least 1 GB free")
            return False
    except Exception as e:
        logger.warning(f"⚠ Could not check disk space: {e}")
        return True

def check_existing_data():
    """Check if any data files already exist"""
    data_files = [
        'sensor_data_real.csv',
        'sensor_data_synthetic_90days.csv',
        'sensor_data_combined.csv',
        'yield_data_synthetic.csv',
        'anomaly_data_synthetic.csv',
        'disease_data_synthetic.csv'
    ]
    
    existing = []
    for file in data_files:
        if os.path.exists(file):
            size_mb = os.path.getsize(file) / 1024 / 1024
            logger.info(f"  Found: {file} ({size_mb:.2f} MB)")
            existing.append(file)
    
    if existing:
        logger.info(f"\n✓ {len(existing)} data file(s) already exist")
    else:
        logger.info("\n  No existing data files (this is normal for first run)")
    
    return True

def main():
    """Run all verification checks"""
    logger.info("=" * 60)
    logger.info("AgriTwin Setup Verification")
    logger.info("=" * 60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Scripts", check_scripts),
        ("ESP32 Firmware", check_firmware),
        ("MQTT Broker", check_mqtt_broker),
        ("Disk Space", check_disk_space),
        ("Existing Data", check_existing_data)
    ]
    
    results = []
    
    for name, check_func in checks:
        logger.info(f"\n{name}:")
        result = check_func()
        results.append((name, result))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Verification Summary")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {name}")
    
    logger.info(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        logger.success("\n✓ All checks passed! Ready to start data collection.")
        logger.info("\nNext steps:")
        logger.info("1. Flash ESP32: cd edge && pio run --target upload")
        logger.info("2. Generate synthetic data: python run_all_generators.py")
        logger.info("3. Start data collection: python collect_data.py")
        logger.info("\nSee QUICK_START_GUIDE.md for detailed instructions.")
    elif passed >= total - 1:
        logger.warning("\n⚠ Most checks passed. Review warnings above.")
        logger.info("\nYou can proceed, but fix warnings for best results.")
    else:
        logger.error("\n✗ Some checks failed. Fix errors before proceeding.")
        logger.info("\nSee error messages above for troubleshooting.")

if __name__ == "__main__":
    main()
