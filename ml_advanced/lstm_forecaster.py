"""
LSTM Time Series Forecasting for Plant Health Prediction

Predicts future soil moisture and plant health based on historical patterns
"""

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
import joblib
from pathlib import Path
import json

class PlantHealthLSTM:
    def __init__(self, sequence_length=24, features=11):
        """
        LSTM model for time-series prediction
        
        Args:
            sequence_length: Number of past timesteps to use (24 = 24 hours)
            features: Number of input features
        """
        self.sequence_length = sequence_length
        self.features = features
        self.model = None
        self.scaler = MinMaxScaler()
        self.history = None
        
    def build_model(self, output_dim=3):
        """Build LSTM architecture"""
        model = keras.Sequential([
            # First LSTM layer with return sequences
            layers.LSTM(128, return_sequences=True, 
                       input_shape=(self.sequence_length, self.features)),
            layers.Dropout(0.2),
            
            # Second LSTM layer
            layers.LSTM(64, return_sequences=True),
            layers.Dropout(0.2),
            
            # Third LSTM layer
            layers.LSTM(32),
            layers.Dropout(0.2),
            
            # Dense layers
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(32, activation='relu'),
            
            # Output layer
            layers.Dense(output_dim, activation='softmax')
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss='categorical_crossentropy',
            metrics=['accuracy']
        )
        
        self.model = model
        return model
    
    def prepare_sequences(self, data, target):
        """
        Create sequences for LSTM training
        
        Args:
            data: Feature dataframe
            target: Target labels
            
        Returns:
            X: Sequences of shape (samples, sequence_length, features)
            y: Target labels
        """
        X, y = [], []
        
        for i in range(len(data) - self.sequence_length):
            X.append(data[i:i + self.sequence_length])
            y.append(target[i + self.sequence_length])
        
        return np.array(X), np.array(y)
    
    def train(self, df, epochs=50, batch_size=32, validation_split=0.2):
        """Train the LSTM model"""
        print("Preparing data...")
        
        # Features
        feature_cols = [
            'Soil_Moisture', 'Ambient_Temperature', 'Soil_Temperature',
            'Humidity', 'Light_Intensity', 'Soil_pH',
            'Nitrogen_Level', 'Phosphorus_Level', 'Potassium_Level',
            'Chlorophyll_Content', 'Electrochemical_Signal'
        ]
        
        # Sort by timestamp and plant
        df = df.sort_values(['Plant_ID', 'Timestamp'])
        
        # Encode target
        target_map = {'Healthy': 0, 'Moderate Stress': 1, 'High Stress': 2}
        df['target'] = df['Plant_Health_Status'].map(target_map)
        
        # Scale features
        scaled_features = self.scaler.fit_transform(df[feature_cols])
        
        # Create sequences for each plant
        all_X, all_y = [], []
        
        for plant_id in df['Plant_ID'].unique():
            plant_data = scaled_features[df['Plant_ID'] == plant_id]
            plant_target = df[df['Plant_ID'] == plant_id]['target'].values
            
            if len(plant_data) > self.sequence_length:
                X, y = self.prepare_sequences(plant_data, plant_target)
                all_X.append(X)
                all_y.append(y)
        
        # Combine all sequences
        X = np.vstack(all_X)
        y = np.hstack(all_y)
        
        # One-hot encode targets
        y_onehot = keras.utils.to_categorical(y, num_classes=3)
        
        print(f"Training data shape: {X.shape}")
        print(f"Target shape: {y_onehot.shape}")
        
        # Build model
        self.build_model(output_dim=3)
        
        # Train
        print("\nTraining LSTM model...")
        self.history = self.model.fit(
            X, y_onehot,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            verbose=1,
            callbacks=[
                keras.callbacks.EarlyStopping(
                    monitor='val_loss',
                    patience=10,
                    restore_best_weights=True
                ),
                keras.callbacks.ReduceLROnPlateau(
                    monitor='val_loss',
                    factor=0.5,
                    patience=5,
                    min_lr=0.00001
                )
            ]
        )
        
        return self.history
    
    def predict(self, sequence):
        """
        Predict plant health from sequence
        
        Args:
            sequence: Array of shape (sequence_length, features)
            
        Returns:
            prediction: Class probabilities
        """
        # Scale input
        scaled = self.scaler.transform(sequence)
        
        # Reshape for LSTM
        X = scaled.reshape(1, self.sequence_length, self.features)
        
        # Predict
        prediction = self.model.predict(X, verbose=0)
        
        return prediction[0]
    
    def predict_future(self, initial_sequence, steps=24):
        """
        Predict multiple steps into the future
        
        Args:
            initial_sequence: Starting sequence
            steps: Number of future steps to predict
            
        Returns:
            predictions: List of predictions
        """
        predictions = []
        current_sequence = initial_sequence.copy()
        
        for _ in range(steps):
            # Predict next step
            pred = self.predict(current_sequence)
            predictions.append(pred)
            
            # Update sequence (simplified - in reality would need actual sensor values)
            # This is a placeholder for demonstration
            current_sequence = np.roll(current_sequence, -1, axis=0)
        
        return predictions
    
    def save(self, path='models/lstm_forecaster'):
        """Save model and scaler"""
        Path(path).mkdir(parents=True, exist_ok=True)
        
        # Save model
        self.model.save(f'{path}/model.h5')
        
        # Save scaler
        joblib.dump(self.scaler, f'{path}/scaler.pkl')
        
        # Save metadata
        metadata = {
            'sequence_length': self.sequence_length,
            'features': self.features,
            'classes': ['Healthy', 'Moderate Stress', 'High Stress']
        }
        with open(f'{path}/metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Model saved to {path}")
    
    def load(self, path='models/lstm_forecaster'):
        """Load model and scaler"""
        self.model = keras.models.load_model(f'{path}/model.h5')
        self.scaler = joblib.load(f'{path}/scaler.pkl')
        
        with open(f'{path}/metadata.json', 'r') as f:
            metadata = json.load(f)
            self.sequence_length = metadata['sequence_length']
            self.features = metadata['features']
        
        print(f"Model loaded from {path}")


def train_lstm_model():
    """Train and save LSTM model"""
    print("=" * 70)
    print("TRAINING LSTM TIME-SERIES FORECASTER")
    print("=" * 70)
    
    # Load data
    print("\nLoading data...")
    df = pd.read_csv('data/plant_health_data.csv')
    print(f"Total records: {len(df)}")
    
    # Initialize model
    lstm = PlantHealthLSTM(sequence_length=24, features=11)
    
    # Train
    history = lstm.train(df, epochs=50, batch_size=32)
    
    # Evaluate
    print("\n" + "=" * 70)
    print("TRAINING COMPLETE")
    print("=" * 70)
    
    final_acc = history.history['accuracy'][-1]
    final_val_acc = history.history['val_accuracy'][-1]
    
    print(f"\nFinal Training Accuracy: {final_acc * 100:.2f}%")
    print(f"Final Validation Accuracy: {final_val_acc * 100:.2f}%")
    
    # Save model
    lstm.save()
    
    # Test prediction
    print("\nTesting prediction...")
    test_sequence = df.iloc[:24][[
        'Soil_Moisture', 'Ambient_Temperature', 'Soil_Temperature',
        'Humidity', 'Light_Intensity', 'Soil_pH',
        'Nitrogen_Level', 'Phosphorus_Level', 'Potassium_Level',
        'Chlorophyll_Content', 'Electrochemical_Signal'
    ]].values
    
    prediction = lstm.predict(test_sequence)
    classes = ['Healthy', 'Moderate Stress', 'High Stress']
    
    print("\nPrediction probabilities:")
    for cls, prob in zip(classes, prediction):
        print(f"  {cls}: {prob * 100:.1f}%")
    
    print("\nPredicted class:", classes[np.argmax(prediction)])
    print("Actual class:", df.iloc[24]['Plant_Health_Status'])
    
    return lstm


if __name__ == '__main__':
    train_lstm_model()
