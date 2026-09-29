"""
Sample Yield Data Generator
Creates realistic sample yield data for testing yield stability analysis
"""

import pandas as pd
import numpy as np
import json

def generate_sample_yield_data(zones, years, output_format="csv"):
    """
    Generate sample yield data with different stability patterns
    
    Args:
        zones: List of zone names
        years: List of years
        output_format: "csv", "json", or "dict"
    
    Returns:
        Sample yield data
    """
    
    np.random.seed(42)  # For reproducibility
    
    data = []
    zone_patterns = {}
    
    for zone in zones:
        # Randomly assign stability pattern
        pattern_type = np.random.choice(['stable_high', 'stable_low', 'unstable'])
        
        if pattern_type == 'stable_high':
            # Stable high yield (CV < 15%)
            base_yield = np.random.uniform(4.5, 5.5)
            yields = [base_yield + np.random.normal(0, 0.2) for _ in years]
            zone_patterns[zone] = "Stable High Yield"
            
        elif pattern_type == 'stable_low':
            # Stable low yield (CV < 15%)
            base_yield = np.random.uniform(2.0, 3.0)
            yields = [base_yield + np.random.normal(0, 0.15) for _ in years]
            zone_patterns[zone] = "Stable Low Yield"
            
        else:  # unstable
            # Unstable yield (CV > 15%)
            base_yield = np.random.uniform(3.0, 4.5)
            yields = [base_yield + np.random.normal(0, 0.8) for _ in years]
            zone_patterns[zone] = "Unstable Yield"
        
        # Add to data
        for year, yield_val in zip(years, yields):
            data.append({
                'zone_id': zone,
                'year': year,
                'yield_tons_per_hectare': round(max(0.5, yield_val), 2)  # Ensure positive
            })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Output in requested format
    if output_format == "csv":
        df.to_csv("sample_yield_data.csv", index=False)
        print(f"✅ Saved to: sample_yield_data.csv")
        return df
    
    elif output_format == "json":
        # Group by zone for API format
        result = {}
        for zone in zones:
            zone_data = df[df['zone_id'] == zone]['yield_tons_per_hectare'].tolist()
            result[zone] = zone_data
        
        with open("sample_yield_data.json", "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"✅ Saved to: sample_yield_data.json")
        return result
    
    else:  # dict
        result = {}
        for zone in zones:
            zone_data = df[df['zone_id'] == zone]['yield_tons_per_hectare'].tolist()
            result[zone] = zone_data
        return result


def generate_realistic_farm_data(farm_size_ha=10, output_file="realistic_yield_data.csv"):
    """
    Generate realistic yield data for a farm
    
    Args:
        farm_size_ha: Farm size in hectares
        output_file: Output CSV filename
    """
    
    print(f"🌾 Generating realistic yield data for {farm_size_ha} ha farm...")
    
    # Divide farm into zones (roughly 1-2 ha per zone)
    num_zones = max(3, int(farm_size_ha / 1.5))
    zones = [f"zone_{i+1}" for i in range(num_zones)]
    
    # Generate 4 years of data
    years = [2021, 2022, 2023, 2024]
    
    # Generate data
    df = generate_sample_yield_data(zones, years, output_format="csv")
    
    # Rename file
    import os
    os.rename("sample_yield_data.csv", output_file)
    
    print(f"\n📊 Generated Data Summary:")
    print(f"   Farm Size: {farm_size_ha} ha")
    print(f"   Zones: {num_zones}")
    print(f"   Years: {len(years)}")
    print(f"   Total Records: {len(df)}")
    
    # Show zone statistics
    print(f"\n📈 Zone Statistics:")
    for zone in zones:
        zone_data = df[df['zone_id'] == zone]['yield_tons_per_hectare']
        mean_yield = zone_data.mean()
        cv = (zone_data.std() / mean_yield) * 100
        
        if cv < 15:
            if mean_yield > 4.0:
                classification = "Stable High"
            else:
                classification = "Stable Low"
        else:
            classification = "Unstable"
        
        print(f"   {zone}: {mean_yield:.2f} t/ha (CV: {cv:.1f}%) - {classification}")
    
    return df


def create_api_test_data():
    """
    Create data in format ready for API testing
    """
    
    print("🔧 Creating API test data...")
    
    zones = ["north_field", "south_field", "east_field", "west_field"]
    years = [2021, 2022, 2023, 2024]
    
    data = generate_sample_yield_data(zones, years, output_format="dict")
    
    # Save as JSON for API testing
    with open("api_test_yield_data.json", "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Saved to: api_test_yield_data.json")
    
    # Print API test command
    print("\n🚀 Test with API:")
    print("curl -X POST http://localhost:8000/api/v1/yield/analyze \\")
    print("  -H 'Content-Type: application/json' \\")
    print(f"  -d '{json.dumps(data)}'")
    
    return data


if __name__ == "__main__":
    print("=" * 60)
    print("Sample Yield Data Generator")
    print("=" * 60)
    
    # Option 1: Simple sample data
    print("\n1️⃣ Generating simple sample data...")
    zones = ["north_field", "south_field", "east_field"]
    years = [2021, 2022, 2023, 2024]
    df = generate_sample_yield_data(zones, years, output_format="csv")
    
    # Option 2: Realistic farm data
    print("\n2️⃣ Generating realistic farm data...")
    df_realistic = generate_realistic_farm_data(farm_size_ha=10)
    
    # Option 3: API test data
    print("\n3️⃣ Creating API test data...")
    api_data = create_api_test_data()
    
    print("\n" + "=" * 60)
    print("✅ All Sample Data Generated!")
    print("=" * 60)
    print("\nFiles created:")
    print("  - sample_yield_data.csv")
    print("  - realistic_yield_data.csv")
    print("  - api_test_yield_data.json")
    print("\nNext steps:")
    print("  1. Review the CSV files")
    print("  2. Test with your AgriTwin API")
    print("  3. Replace with your own real data when available")
