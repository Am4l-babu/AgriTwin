"""
Train ML Model to Predict Plant Health Status

Uses plant_health_data.csv to train a Random Forest classifier
that predicts plant health status from sensor readings.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib
from pathlib import Path

print("=" * 70)
print("TRAINING PLANT HEALTH PREDICTION MODEL")
print("=" * 70)

# Load data
print("\n📊 Loading dataset...")
df = pd.read_csv('data/plant_health_data.csv')
print(f"  Total records: {len(df):,}")
print(f"  Plants: {df['Plant_ID'].nunique()}")

# Prepare features and target
print("\n🔧 Preparing features...")
feature_cols = [
    'Soil_Moisture', 'Ambient_Temperature', 'Soil_Temperature',
    'Humidity', 'Light_Intensity', 'Soil_pH',
    'Nitrogen_Level', 'Phosphorus_Level', 'Potassium_Level',
    'Chlorophyll_Content', 'Electrochemical_Signal'
]

X = df[feature_cols]
y = df['Plant_Health_Status']

print(f"  Features: {len(feature_cols)}")
print(f"  Target classes: {y.nunique()}")

# Split data
print("\n✂️  Splitting data...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"  Training set: {len(X_train):,} samples")
print(f"  Test set: {len(X_test):,} samples")

# Train model
print("\n🤖 Training Random Forest model...")
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train, y_train)
print("  ✓ Model trained!")

# Evaluate
print("\n📈 Evaluating model...")
y_pred = model.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f"\n  Accuracy: {accuracy * 100:.2f}%")

print("\n  Classification Report:")
print(classification_report(y_test, y_pred))

print("  Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# Feature importance
print("\n🎯 Feature Importance:")
feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

for idx, row in feature_importance.head(5).iterrows():
    print(f"  {row['feature']}: {row['importance']:.4f}")

# Save model
print("\n💾 Saving model...")
model_dir = Path("models")
model_dir.mkdir(exist_ok=True)

model_path = model_dir / "plant_health_predictor.pkl"
joblib.dump(model, model_path)
print(f"  ✓ Model saved to: {model_path}")

# Save feature names
feature_path = model_dir / "feature_names.txt"
with open(feature_path, 'w') as f:
    f.write('\n'.join(feature_cols))
print(f"  ✓ Features saved to: {feature_path}")

# Test prediction
print("\n🧪 Testing prediction...")
sample = X_test.iloc[0:1]
prediction = model.predict(sample)[0]
probabilities = model.predict_proba(sample)[0]

print(f"  Sample data:")
for col in feature_cols[:5]:  # Show first 5 features
    print(f"    {col}: {sample[col].values[0]:.2f}")
print(f"  ...")
print(f"\n  Predicted: {prediction}")
print(f"  Actual: {y_test.iloc[0]}")
print(f"  Probabilities:")
for cls, prob in zip(model.classes_, probabilities):
    print(f"    {cls}: {prob * 100:.1f}%")

print("\n" + "=" * 70)
print("✅ MODEL TRAINING COMPLETE!")
print("=" * 70)
print("\nNext steps:")
print("1. Integrate model into Multi-Agent System")
print("2. Use for real-time health predictions")
print("3. Compare predictions with actual sensor data")
print("4. Retrain periodically with new data")
