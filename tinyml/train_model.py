"""
Train LSTM Model for Soil Moisture Prediction

Lightweight model optimized for ESP32 deployment.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import os
import json


# Model configuration
LOOKBACK = 4  # Use last 4 readings (1 hour at 15-min intervals)
FORECAST_HORIZON = 1  # Predict next reading
FEATURES = ['temperature', 'humidity', 'light_level', 'hour']
TARGET = 'soil_moisture'


def load_data(filepath='data/training_data.csv'):
    """Load training data"""
    print(f"Loading data from {filepath}...")
    df = pd.read_csv(filepath)
    print(f"✓ Loaded {len(df)} samples")
    return df


def create_sequences(df, lookback=LOOKBACK, forecast_horizon=FORECAST_HORIZON):
    """
    Create sequences for LSTM training
    
    Input shape: (samples, lookback, features)
    Output shape: (samples,)
    """
    X, y = [], []
    
    for i in range(lookback, len(df) - forecast_horizon + 1):
        # Input: past lookback timesteps
        X.append(df[FEATURES].iloc[i-lookback:i].values)
        # Output: future soil moisture
        y.append(df[TARGET].iloc[i + forecast_horizon - 1])
    
    return np.array(X), np.array(y)


def normalize_data(X_train, X_test):
    """
    Normalize features to [0, 1] range
    
    This is crucial for TinyML deployment
    """
    # Calculate normalization parameters from training data
    feature_mins = X_train.reshape(-1, X_train.shape[-1]).min(axis=0)
    feature_maxs = X_train.reshape(-1, X_train.shape[-1]).max(axis=0)
    feature_ranges = feature_maxs - feature_mins
    
    # Normalize
    X_train_norm = (X_train - feature_mins) / feature_ranges
    X_test_norm = (X_test - feature_mins) / feature_ranges
    
    # Save normalization parameters
    norm_params = {
        'feature_names': FEATURES,
        'mins': feature_mins.tolist(),
        'maxs': feature_maxs.tolist(),
        'ranges': feature_ranges.tolist()
    }
    
    os.makedirs('models', exist_ok=True)
    with open('models/normalization_params.json', 'w') as f:
        json.dump(norm_params, f, indent=2)
    
    print("✓ Normalization parameters saved")
    
    return X_train_norm, X_test_norm, norm_params


def build_model(input_shape):
    """
    Build lightweight LSTM model for ESP32
    
    Architecture optimized for:
    - Small size (<20KB)
    - Fast inference (<10ms)
    - Good accuracy (>95%)
    """
    model = keras.Sequential([
        # Input layer
        layers.Input(shape=input_shape),
        
        # LSTM layer (32 units for balance of size/performance)
        layers.LSTM(32, return_sequences=False),
        
        # Dense layers
        layers.Dense(16, activation='relu'),
        layers.Dropout(0.2),
        
        # Output layer
        layers.Dense(1, activation='linear')
    ])
    
    # Compile with Adam optimizer
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss='mse',
        metrics=['mae']
    )
    
    return model


def train_model(model, X_train, y_train, X_val, y_val, epochs=50):
    """Train the model with early stopping"""
    
    # Callbacks
    early_stop = keras.callbacks.EarlyStopping(
        monitor='val_loss',
        patience=10,
        restore_best_weights=True
    )
    
    reduce_lr = keras.callbacks.ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=5,
        min_lr=0.00001
    )
    
    # Train
    print("\n=== Training Model ===")
    history = model.fit(
        X_train, y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=32,
        callbacks=[early_stop, reduce_lr],
        verbose=1
    )
    
    return history


def evaluate_model(model, X_test, y_test):
    """Evaluate model performance"""
    print("\n=== Evaluating Model ===")
    
    # Predictions
    y_pred = model.predict(X_test, verbose=0).flatten()
    
    # Metrics
    mae = np.mean(np.abs(y_pred - y_test))
    rmse = np.sqrt(np.mean((y_pred - y_test) ** 2))
    
    # R² score
    ss_res = np.sum((y_test - y_pred) ** 2)
    ss_tot = np.sum((y_test - np.mean(y_test)) ** 2)
    r2 = 1 - (ss_res / ss_tot)
    
    print(f"MAE: {mae:.2f}%")
    print(f"RMSE: {rmse:.2f}%")
    print(f"R² Score: {r2:.4f}")
    
    return y_pred, {'mae': mae, 'rmse': rmse, 'r2': r2}


def plot_results(history, y_test, y_pred):
    """Plot training history and predictions"""
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Training loss
    axes[0, 0].plot(history.history['loss'], label='Training Loss')
    axes[0, 0].plot(history.history['val_loss'], label='Validation Loss')
    axes[0, 0].set_xlabel('Epoch')
    axes[0, 0].set_ylabel('Loss (MSE)')
    axes[0, 0].set_title('Training History')
    axes[0, 0].legend()
    axes[0, 0].grid(True)
    
    # MAE
    axes[0, 1].plot(history.history['mae'], label='Training MAE')
    axes[0, 1].plot(history.history['val_mae'], label='Validation MAE')
    axes[0, 1].set_xlabel('Epoch')
    axes[0, 1].set_ylabel('MAE')
    axes[0, 1].set_title('Mean Absolute Error')
    axes[0, 1].legend()
    axes[0, 1].grid(True)
    
    # Predictions vs Actual
    axes[1, 0].scatter(y_test, y_pred, alpha=0.5)
    axes[1, 0].plot([y_test.min(), y_test.max()], 
                    [y_test.min(), y_test.max()], 
                    'r--', lw=2)
    axes[1, 0].set_xlabel('Actual Soil Moisture (%)')
    axes[1, 0].set_ylabel('Predicted Soil Moisture (%)')
    axes[1, 0].set_title('Predictions vs Actual')
    axes[1, 0].grid(True)
    
    # Error distribution
    errors = y_pred - y_test
    axes[1, 1].hist(errors, bins=50, edgecolor='black')
    axes[1, 1].set_xlabel('Prediction Error (%)')
    axes[1, 1].set_ylabel('Frequency')
    axes[1, 1].set_title('Error Distribution')
    axes[1, 1].axvline(0, color='r', linestyle='--', lw=2)
    axes[1, 1].grid(True)
    
    plt.tight_layout()
    plt.savefig('models/training_results.png', dpi=150)
    print("✓ Plots saved to models/training_results.png")


def main():
    """Main training pipeline"""
    
    print("=" * 60)
    print("TinyML Model Training - Soil Moisture Prediction")
    print("=" * 60)
    
    # Load data
    df = load_data('data/training_data.csv')
    
    # Create sequences
    print("\n=== Creating Sequences ===")
    X, y = create_sequences(df, lookback=LOOKBACK, forecast_horizon=FORECAST_HORIZON)
    print(f"✓ Created {len(X)} sequences")
    print(f"  Input shape: {X.shape}")
    print(f"  Output shape: {y.shape}")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, shuffle=False
    )
    
    # Further split training into train/val
    X_train, X_val, y_train, y_val = train_test_split(
        X_train, y_train, test_size=0.2, random_state=42, shuffle=False
    )
    
    print(f"✓ Train: {len(X_train)} samples")
    print(f"✓ Val: {len(X_val)} samples")
    print(f"✓ Test: {len(X_test)} samples")
    
    # Normalize data
    print("\n=== Normalizing Data ===")
    X_train_norm, X_test_norm, norm_params = normalize_data(X_train, X_test)
    X_val_norm = (X_val - norm_params['mins']) / norm_params['ranges']
    
    # Build model
    print("\n=== Building Model ===")
    model = build_model(input_shape=(LOOKBACK, len(FEATURES)))
    model.summary()
    
    # Train model
    history = train_model(model, X_train_norm, y_train, X_val_norm, y_val, epochs=50)
    
    # Evaluate model
    y_pred, metrics = evaluate_model(model, X_test_norm, y_test)
    
    # Plot results
    plot_results(history, y_test, y_pred)
    
    # Save model
    print("\n=== Saving Model ===")
    model.save('models/soil_moisture_model.h5')
    print("✓ Model saved to models/soil_moisture_model.h5")
    
    # Save metrics
    with open('models/metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    print("✓ Metrics saved to models/metrics.json")
    
    # Model size
    model_size = os.path.getsize('models/soil_moisture_model.h5') / 1024
    print(f"\n✓ Model size: {model_size:.1f} KB")
    
    print("\n" + "=" * 60)
    print("Training Complete!")
    print("=" * 60)
    print(f"MAE: {metrics['mae']:.2f}%")
    print(f"RMSE: {metrics['rmse']:.2f}%")
    print(f"R² Score: {metrics['r2']:.4f}")
    print("\nNext step: python convert_to_tflite.py")


if __name__ == "__main__":
    main()
