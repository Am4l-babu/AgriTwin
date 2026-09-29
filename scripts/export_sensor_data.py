"""
Sensor Data Exporter
Exports sensor data from AgriTwin database for analysis
"""

import requests
import pandas as pd
import json
from datetime import datetime

def export_sensor_history(farm_id="farm_001", hours=168, output_file="sensor_data.csv"):
    """
    Export sensor history from AgriTwin API
    
    Args:
        farm_id: Farm identifier
        hours: Hours of history to export (default: 168 = 1 week)
        output_file: Output CSV filename
    
    Returns:
        DataFrame with sensor data
    """
    
    print(f"📡 Exporting sensor data from AgriTwin...")
    print(f"   Farm ID: {farm_id}")
    print(f"   Period: Last {hours} hours")
    
    try:
        # Call API
        url = "http://localhost:8000/api/v1/sensors/history"
        params = {
            "farm_id": farm_id,
            "hours": hours,
            "limit": 5000
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        readings = data.get('readings', [])
        
        if not readings:
            print("❌ No sensor data found")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(readings)
        
        # Add timestamp as datetime
        if 'timestamp' in df.columns:
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        
        # Save to CSV
        df.to_csv(output_file, index=False)
        
        print(f"✅ Exported {len(df)} readings")
        print(f"✅ Saved to: {output_file}")
        
        # Show summary
        print("\n📊 Data Summary:")
        if 'temperature' in df.columns:
            print(f"   Temperature: {df['temperature'].mean():.1f}°C (avg)")
        if 'humidity' in df.columns:
            print(f"   Humidity: {df['humidity'].mean():.1f}% (avg)")
        if 'light_level' in df.columns:
            print(f"   Light: {df['light_level'].mean():.0f} lux (avg)")
        if 'soil_moisture' in df.columns:
            print(f"   Soil Moisture: {df['soil_moisture'].mean():.1f}% (avg)")
        
        return df
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to AgriTwin backend")
        print("   Make sure the backend is running: python cloud/backend/main_working.py")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def export_for_optimization(farm_id="farm_001", hours=168, output_file="sensor_optimization_data.csv"):
    """
    Export sensor data in format for Thompson Sampling optimization
    
    Includes sensor locations and readings
    """
    
    print(f"🎯 Exporting data for sensor optimization...")
    
    df = export_sensor_history(farm_id, hours, output_file)
    
    if df is not None:
        # Add location columns if not present
        if 'location_x' not in df.columns:
            print("\n⚠️ Warning: No location data found")
            print("   Add sensor locations to use optimization")
            print("   Format: sensor_id, location_x, location_y")
        
        print("\n🚀 Ready for optimization!")
        print("   Use this data with: /api/v1/sensors/optimize")
    
    return df


def export_statistics(farm_id="farm_001", hours=24):
    """
    Export sensor statistics
    """
    
    print(f"📊 Exporting sensor statistics...")
    
    try:
        url = "http://localhost:8000/api/v1/sensors/stats"
        params = {
            "farm_id": farm_id,
            "hours": hours
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        stats = response.json()
        
        # Save as JSON
        with open("sensor_stats.json", "w") as f:
            json.dump(stats, f, indent=2)
        
        print(f"✅ Saved to: sensor_stats.json")
        
        # Print summary
        print("\n📈 Statistics Summary:")
        print(f"   Period: {stats['period_hours']} hours")
        print(f"   Total Readings: {stats['total_readings']}")
        print(f"   Avg Temperature: {stats['avg_temperature']:.1f}°C")
        print(f"   Avg Humidity: {stats['avg_humidity']:.1f}%")
        
        return stats
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def generate_sample_sensor_data(num_sensors=6, num_readings=100, output_file="sample_sensor_data.csv"):
    """
    Generate sample sensor data for testing
    """
    
    print(f"🔧 Generating sample sensor data...")
    print(f"   Sensors: {num_sensors}")
    print(f"   Readings per sensor: {num_readings}")
    
    import numpy as np
    
    np.random.seed(42)
    
    # Define sensor locations in a grid
    locations = []
    grid_size = int(np.sqrt(num_sensors)) + 1
    for i in range(num_sensors):
        x = (i % grid_size) * 10
        y = (i // grid_size) * 10
        locations.append((x, y))
    
    # Generate readings
    data = []
    base_time = datetime.now().timestamp()
    
    for reading_idx in range(num_readings):
        timestamp = base_time - (num_readings - reading_idx) * 900  # 15 min intervals
        
        # Base values with temporal variation
        base_temp = 25 + 5 * np.sin(reading_idx / 10)  # Daily cycle
        base_humidity = 65 + 10 * np.cos(reading_idx / 10)
        
        for sensor_idx, (x, y) in enumerate(locations):
            # Add spatial variation
            temp = base_temp + (x + y) * 0.01 + np.random.normal(0, 0.5)
            humidity = base_humidity + np.random.normal(0, 3)
            soil = 45 + (x - y) * 0.02 + np.random.normal(0, 2)
            light = max(0, 500 + 300 * np.sin(reading_idx / 10) + np.random.normal(0, 50))
            
            data.append({
                'sensor_id': f'sensor_{sensor_idx + 1}',
                'location_x': x,
                'location_y': y,
                'timestamp': int(timestamp),
                'datetime': datetime.fromtimestamp(timestamp).isoformat(),
                'temperature': round(temp, 1),
                'humidity': round(humidity, 1),
                'soil_moisture': round(soil, 1),
                'light_level': round(light, 0)
            })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    df.to_csv(output_file, index=False)
    
    print(f"✅ Generated {len(df)} readings")
    print(f"✅ Saved to: {output_file}")
    
    # Show sensor locations
    print("\n📍 Sensor Locations:")
    for sensor_id, (x, y) in zip([f'sensor_{i+1}' for i in range(num_sensors)], locations):
        print(f"   {sensor_id}: ({x}, {y})")
    
    return df


if __name__ == "__main__":
    print("=" * 60)
    print("Sensor Data Exporter")
    print("=" * 60)
    
    # Check if backend is running
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        backend_running = response.status_code == 200
    except:
        backend_running = False
    
    if backend_running:
        print("\n✅ AgriTwin backend is running")
        
        # Option 1: Export real data
        print("\n1️⃣ Exporting real sensor data...")
        df = export_sensor_history(hours=168)  # 1 week
        
        # Option 2: Export statistics
        print("\n2️⃣ Exporting statistics...")
        stats = export_statistics(hours=24)
        
        # Option 3: Export for optimization
        print("\n3️⃣ Exporting for optimization...")
        df_opt = export_for_optimization(hours=168)
        
    else:
        print("\n⚠️ AgriTwin backend is not running")
        print("   Start it with: python cloud/backend/main_working.py")
        print("\n   Generating sample data instead...")
        
        # Generate sample data
        df_sample = generate_sample_sensor_data(num_sensors=6, num_readings=100)
    
    print("\n" + "=" * 60)
    print("✅ Export Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Review the exported CSV files")
    print("  2. Use for sensor optimization")
    print("  3. Analyze patterns and correlations")
