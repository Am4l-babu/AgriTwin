"""
NASA POWER Weather Data Downloader
Downloads historical weather data for your farm location
"""

import requests
import pandas as pd
import json
from datetime import datetime

def download_nasa_weather(latitude, longitude, start_date, end_date, output_file="weather_data.csv"):
    """
    Download weather data from NASA POWER API
    
    Args:
        latitude: Farm latitude (e.g., 37.7749)
        longitude: Farm longitude (e.g., -122.4194)
        start_date: Start date (YYYYMMDD format, e.g., "20230101")
        end_date: End date (YYYYMMDD format, e.g., "20231231")
        output_file: Output CSV filename
    
    Returns:
        DataFrame with weather data
    """
    
    print(f"📡 Downloading weather data from NASA POWER...")
    print(f"   Location: ({latitude}, {longitude})")
    print(f"   Period: {start_date} to {end_date}")
    
    # NASA POWER API endpoint
    url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    
    # Parameters for agricultural applications
    params = {
        "parameters": "T2M,T2M_MAX,T2M_MIN,RH2M,PRECTOTCORR,ALLSKY_SFC_SW_DWN,WS2M",
        "community": "AG",
        "longitude": longitude,
        "latitude": latitude,
        "start": start_date,
        "end": end_date,
        "format": "JSON"
    }
    
    try:
        # Make API request
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract parameter data
        parameters = data['properties']['parameter']
        
        # Convert to DataFrame
        df = pd.DataFrame(parameters)
        
        # Rename columns for clarity
        df = df.rename(columns={
            'T2M': 'temperature_avg_c',
            'T2M_MAX': 'temperature_max_c',
            'T2M_MIN': 'temperature_min_c',
            'RH2M': 'humidity_percent',
            'PRECTOTCORR': 'rainfall_mm',
            'ALLSKY_SFC_SW_DWN': 'solar_radiation_mj_m2',
            'WS2M': 'wind_speed_m_s'
        })
        
        # Reset index to get dates as column
        df = df.reset_index()
        df = df.rename(columns={'index': 'date'})
        
        # Save to CSV
        df.to_csv(output_file, index=False)
        
        print(f"✅ Downloaded {len(df)} days of weather data")
        print(f"✅ Saved to: {output_file}")
        
        # Show summary statistics
        print("\n📊 Data Summary:")
        print(f"   Temperature: {df['temperature_avg_c'].mean():.1f}°C (avg)")
        print(f"   Humidity: {df['humidity_percent'].mean():.1f}% (avg)")
        print(f"   Total Rainfall: {df['rainfall_mm'].sum():.1f} mm")
        print(f"   Avg Solar Radiation: {df['solar_radiation_mj_m2'].mean():.1f} MJ/m²")
        
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error downloading data: {e}")
        return None
    except Exception as e:
        print(f"❌ Error processing data: {e}")
        return None


def download_multi_year(latitude, longitude, years, output_dir="weather_data"):
    """
    Download multiple years of data
    
    Args:
        latitude: Farm latitude
        longitude: Farm longitude
        years: List of years (e.g., [2021, 2022, 2023])
        output_dir: Output directory
    """
    import os
    
    os.makedirs(output_dir, exist_ok=True)
    
    all_data = []
    
    for year in years:
        start_date = f"{year}0101"
        end_date = f"{year}1231"
        output_file = os.path.join(output_dir, f"weather_{year}.csv")
        
        print(f"\n📅 Downloading year {year}...")
        df = download_nasa_weather(latitude, longitude, start_date, end_date, output_file)
        
        if df is not None:
            all_data.append(df)
    
    # Combine all years
    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        combined_file = os.path.join(output_dir, "weather_all_years.csv")
        combined.to_csv(combined_file, index=False)
        print(f"\n✅ Combined data saved to: {combined_file}")
        print(f"   Total days: {len(combined)}")
        
        return combined
    
    return None


if __name__ == "__main__":
    # CONFIGURE YOUR FARM LOCATION HERE
    # Find your coordinates: https://www.latlong.net/
    
    FARM_LATITUDE = 37.7749   # Replace with your farm latitude
    FARM_LONGITUDE = -122.4194  # Replace with your farm longitude
    
    # Download options:
    
    # Option 1: Single year
    print("=" * 60)
    print("NASA POWER Weather Data Downloader")
    print("=" * 60)
    
    df = download_nasa_weather(
        latitude=FARM_LATITUDE,
        longitude=FARM_LONGITUDE,
        start_date="20230101",  # January 1, 2023
        end_date="20231231",    # December 31, 2023
        output_file="weather_2023.csv"
    )
    
    # Option 2: Multiple years (uncomment to use)
    # print("\n" + "=" * 60)
    # print("Downloading Multiple Years")
    # print("=" * 60)
    # 
    # df_multi = download_multi_year(
    #     latitude=FARM_LATITUDE,
    #     longitude=FARM_LONGITUDE,
    #     years=[2021, 2022, 2023, 2024]
    # )
    
    print("\n" + "=" * 60)
    print("✅ Download Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Check the CSV file(s) created")
    print("2. Use this data for digital twin calibration")
    print("3. Integrate with your AgriTwin system")
