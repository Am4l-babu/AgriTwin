"""
Analyze plant_health_data.csv for AgriTwin System
"""
import pandas as pd
import numpy as np
from datetime import datetime

# Load data
df = pd.read_csv('data/plant_health_data.csv')

print("=" * 70)
print("PLANT HEALTH DATA ANALYSIS")
print("=" * 70)

# Basic info
print(f"\n📊 Dataset Overview:")
print(f"  Total Records: {len(df):,}")
print(f"  Plants: {df['Plant_ID'].nunique()}")
print(f"  Date Range: {df['Timestamp'].min()} to {df['Timestamp'].max()}")
print(f"  Features: {len(df.columns)}")

# Health status distribution
print(f"\n🌱 Health Status Distribution:")
health_dist = df['Plant_Health_Status'].value_counts()
for status, count in health_dist.items():
    pct = (count / len(df)) * 100
    print(f"  {status}: {count} ({pct:.1f}%)")

# Sensor statistics by health status
print(f"\n📈 Sensor Averages by Health Status:")
print("-" * 70)

for status in ['Healthy', 'Moderate Stress', 'High Stress']:
    subset = df[df['Plant_Health_Status'] == status]
    if len(subset) > 0:
        print(f"\n{status}:")
        print(f"  Soil Moisture: {subset['Soil_Moisture'].mean():.1f}%")
        print(f"  Temperature: {subset['Ambient_Temperature'].mean():.1f}°C")
        print(f"  Humidity: {subset['Humidity'].mean():.1f}%")
        print(f"  Light: {subset['Light_Intensity'].mean():.0f} lux")
        print(f"  Nitrogen: {subset['Nitrogen_Level'].mean():.1f}")
        print(f"  Phosphorus: {subset['Phosphorus_Level'].mean():.1f}")
        print(f"  Potassium: {subset['Potassium_Level'].mean():.1f}")
        print(f"  Chlorophyll: {subset['Chlorophyll_Content'].mean():.1f}")

# Identify optimal thresholds
print(f"\n🎯 Recommended Thresholds for MAS:")
print("-" * 70)

healthy = df[df['Plant_Health_Status'] == 'Healthy']
stressed = df[df['Plant_Health_Status'] == 'High Stress']

print(f"\nSoil Moisture:")
print(f"  Healthy Range: {healthy['Soil_Moisture'].min():.1f}% - {healthy['Soil_Moisture'].max():.1f}%")
print(f"  Optimal: {healthy['Soil_Moisture'].mean():.1f}%")
print(f"  ⚠️ Irrigation Trigger: < {healthy['Soil_Moisture'].quantile(0.25):.1f}%")

print(f"\nTemperature:")
print(f"  Healthy Range: {healthy['Ambient_Temperature'].min():.1f}°C - {healthy['Ambient_Temperature'].max():.1f}°C")
print(f"  Optimal: {healthy['Ambient_Temperature'].mean():.1f}°C")
print(f"  ⚠️ Anomaly Trigger: > {healthy['Ambient_Temperature'].quantile(0.95):.1f}°C")

print(f"\nNitrogen Level:")
print(f"  Healthy Range: {healthy['Nitrogen_Level'].min():.1f} - {healthy['Nitrogen_Level'].max():.1f}")
print(f"  Optimal: {healthy['Nitrogen_Level'].mean():.1f}")
print(f"  ⚠️ Fertilization Trigger: < {healthy['Nitrogen_Level'].quantile(0.25):.1f}")

# Correlation analysis
print(f"\n🔗 Top Correlations with Health Status:")
print("-" * 70)

# Convert health status to numeric
health_map = {'Healthy': 2, 'Moderate Stress': 1, 'High Stress': 0}
df['Health_Numeric'] = df['Plant_Health_Status'].map(health_map)

# Select only numeric columns for correlation
numeric_cols = ['Soil_Moisture', 'Ambient_Temperature', 'Soil_Temperature', 'Humidity', 
                'Light_Intensity', 'Soil_pH', 'Nitrogen_Level', 'Phosphorus_Level', 
                'Potassium_Level', 'Chlorophyll_Content', 'Electrochemical_Signal', 'Health_Numeric']
df_numeric = df[numeric_cols]

correlations = df_numeric.corr()['Health_Numeric'].sort_values(ascending=False)
print("\nPositive Correlations (Higher = Healthier):")
for col, corr in correlations.head(6).items():
    if col != 'Health_Numeric':
        print(f"  {col}: {corr:.3f}")

print("\nNegative Correlations (Higher = More Stressed):")
for col, corr in correlations.tail(5).items():
    if col != 'Health_Numeric':
        print(f"  {col}: {corr:.3f}")

# Use cases
print(f"\n💡 Recommended Use Cases:")
print("-" * 70)
print("1. Train ML model to predict plant health")
print("2. Calibrate MAS decision thresholds")
print("3. Validate autonomous agent decisions")
print("4. Populate dashboard with historical data")
print("5. Test anomaly detection algorithms")
print("6. Benchmark digital twin accuracy")

print(f"\n✅ Dataset is HIGHLY USEFUL for AgriTwin system!")
print("=" * 70)
