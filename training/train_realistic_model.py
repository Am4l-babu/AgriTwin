"""
Train Realistic ML Model for Plant Health Prediction

Includes proper validation, cross-validation, and realistic expectations
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.preprocessing import StandardScaler
import joblib
from pathlib import Path

print("=" * 70)
print("TRAINING REALISTIC PLANT HEALTH PREDICTION MODEL")
print("=" * 70)

# Load data
print("\n📊 Loading dataset...")
df = pd.read_csv('data/plant_health_data.csv')
print(f"  Total records: {len(df):,}")
print(f"  Plants: {df['Plant_ID'].nunique()}")

# Check for data leakage
print("\n🔍 Checking for data issues...")
print(f"  Unique records: {len(df)}")
print(f"  Duplicate rows: {df.duplicated().sum()}")

# Analyze class overlap
print("\n📈 Class Overlap Analysis:")
for status in ['Healthy', 'Moderate Stress', 'High Stress']:
    subset = df[df['Plant_Health_Status'] == status]
    print(f"  {status}:")
    print(f"    Soil Moisture: {subset['Soil_Moisture'].min():.1f} - {subset['Soil_Moisture'].max():.1f}")
    print(f"    Nitrogen: {subset['Nitrogen_Level'].min():.1f} - {subset['Nitrogen_Level'].max():.1f}")

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

# Split data - use stratified split
print("\n✂️  Splitting data (80/20 train/test)...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"  Training set: {len(X_train):,} samples")
print(f"  Test set: {len(X_test):,} samples")

# Scale features for some models
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train multiple models
print("\n🤖 Training multiple models...")

models = {
    'Random Forest': RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=10,  # Increased to reduce overfitting
        min_samples_leaf=5,    # Increased to reduce overfitting
        random_state=42,
        n_jobs=-1
    ),
    'Gradient Boosting': GradientBoostingClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        random_state=42
    ),
    'Logistic Regression': LogisticRegression(
        max_iter=1000,
        random_state=42
    )
}

results = {}

for name, model in models.items():
    print(f"\n  Training {name}...")
    
    # Use scaled data for Logistic Regression
    if name == 'Logistic Regression':
        model.fit(X_train_scaled, y_train)
        y_pred = model.predict(X_test_scaled)
        
        # Cross-validation
        cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5)
    else:
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        
        # Cross-validation
        cv_scores = cross_val_score(model, X_train, y_train, cv=5)
    
    # Evaluate
    test_accuracy = accuracy_score(y_test, y_pred)
    cv_mean = cv_scores.mean()
    cv_std = cv_scores.std()
    
    results[name] = {
        'model': model,
        'test_accuracy': test_accuracy,
        'cv_mean': cv_mean,
        'cv_std': cv_std,
        'predictions': y_pred
    }
    
    print(f"    Test Accuracy: {test_accuracy * 100:.2f}%")
    print(f"    CV Accuracy: {cv_mean * 100:.2f}% (+/- {cv_std * 100:.2f}%)")
    
    # Check for overfitting
    if test_accuracy > cv_mean + 0.05:
        print(f"    ⚠️  Possible overfitting detected!")
    elif test_accuracy < cv_mean - 0.05:
        print(f"    ⚠️  Model may not generalize well")
    else:
        print(f"    ✓ Good generalization")

# Select best model based on CV score
best_model_name = max(results.keys(), key=lambda k: results[k]['cv_mean'])
best_model = results[best_model_name]['model']
best_predictions = results[best_model_name]['predictions']

print(f"\n🏆 Best Model: {best_model_name}")
print(f"  Test Accuracy: {results[best_model_name]['test_accuracy'] * 100:.2f}%")
print(f"  CV Accuracy: {results[best_model_name]['cv_mean'] * 100:.2f}% (+/- {results[best_model_name]['cv_std'] * 100:.2f}%)")

# Detailed evaluation of best model
print("\n📊 Detailed Classification Report:")
print(classification_report(y_test, best_predictions))

print("\n📉 Confusion Matrix:")
cm = confusion_matrix(y_test, best_predictions)
print(cm)

# Calculate per-class accuracy
print("\n📈 Per-Class Performance:")
for i, status in enumerate(['Healthy', 'High Stress', 'Moderate Stress']):
    if i < len(cm):
        correct = cm[i][i]
        total = cm[i].sum()
        accuracy = (correct / total * 100) if total > 0 else 0
        print(f"  {status}: {accuracy:.1f}% ({correct}/{total})")

# Feature importance (for tree-based models)
if best_model_name in ['Random Forest', 'Gradient Boosting']:
    print("\n🎯 Feature Importance (Top 5):")
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': best_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    for idx, row in feature_importance.head(5).iterrows():
        print(f"  {row['feature']}: {row['importance']:.4f}")

# Save best model
print("\n💾 Saving best model...")
model_dir = Path("models")
model_dir.mkdir(exist_ok=True)

model_path = model_dir / "plant_health_predictor_realistic.pkl"
joblib.dump(best_model, model_path)
print(f"  ✓ Model saved to: {model_path}")

# Save scaler if needed
if best_model_name == 'Logistic Regression':
    scaler_path = model_dir / "scaler.pkl"
    joblib.dump(scaler, scaler_path)
    print(f"  ✓ Scaler saved to: {scaler_path}")

# Save metadata
metadata = {
    'model_type': best_model_name,
    'test_accuracy': results[best_model_name]['test_accuracy'],
    'cv_accuracy': results[best_model_name]['cv_mean'],
    'cv_std': results[best_model_name]['cv_std'],
    'features': feature_cols,
    'classes': list(best_model.classes_),
    'needs_scaling': best_model_name == 'Logistic Regression'
}

import json
metadata_path = model_dir / "model_metadata.json"
with open(metadata_path, 'w') as f:
    json.dump(metadata, f, indent=2)
print(f"  ✓ Metadata saved to: {metadata_path}")

# Test prediction
print("\n🧪 Testing prediction...")
sample = X_test.iloc[0:1]
if best_model_name == 'Logistic Regression':
    sample_scaled = scaler.transform(sample)
    prediction = best_model.predict(sample_scaled)[0]
    probabilities = best_model.predict_proba(sample_scaled)[0]
else:
    prediction = best_model.predict(sample)[0]
    probabilities = best_model.predict_proba(sample)[0]

print(f"  Sample data:")
for col in feature_cols[:5]:
    print(f"    {col}: {sample[col].values[0]:.2f}")
print(f"  ...")
print(f"\n  Predicted: {prediction}")
print(f"  Actual: {y_test.iloc[0]}")
print(f"  Probabilities:")
for cls, prob in zip(best_model.classes_, probabilities):
    print(f"    {cls}: {prob * 100:.1f}%")

# Reality check
print("\n" + "=" * 70)
print("✅ REALISTIC MODEL TRAINING COMPLETE!")
print("=" * 70)

print("\n📌 Key Insights:")
print(f"  • Best model: {best_model_name}")
print(f"  • Test accuracy: {results[best_model_name]['test_accuracy'] * 100:.1f}%")
print(f"  • Cross-validation: {results[best_model_name]['cv_mean'] * 100:.1f}% (+/- {results[best_model_name]['cv_std'] * 100:.1f}%)")

if results[best_model_name]['test_accuracy'] >= 0.95:
    print("\n⚠️  WARNING: Very high accuracy may indicate:")
    print("  • Synthetic or overly clean data")
    print("  • Data leakage")
    print("  • Classes are perfectly separable")
    print("  • Consider collecting more diverse real-world data")
elif results[best_model_name]['test_accuracy'] >= 0.85:
    print("\n✓ Good accuracy - model should work well in practice")
elif results[best_model_name]['test_accuracy'] >= 0.70:
    print("\n✓ Reasonable accuracy - typical for real-world agricultural data")
else:
    print("\n⚠️  Low accuracy - may need:")
    print("  • More features")
    print("  • More training data")
    print("  • Feature engineering")

print("\nNext steps:")
print("1. Validate with real sensor data")
print("2. Monitor performance in production")
print("3. Retrain periodically with new data")
print("4. Consider ensemble methods if accuracy is insufficient")
