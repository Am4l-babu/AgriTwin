"""
Train all advanced ML models

1. LSTM Time-Series Forecaster
2. RL Irrigation Agent
"""

import sys
import subprocess

print("=" * 70)
print("TRAINING ADVANCED ML MODELS")
print("=" * 70)

print("\n1. Installing required packages...")
packages = [
    'tensorflow>=2.13.0',
    'keras>=2.13.0'
]

for package in packages:
    print(f"   Installing {package}...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package, '-q'])

print("\n2. Training LSTM Time-Series Forecaster...")
print("-" * 70)
from ml_advanced.lstm_forecaster import train_lstm_model
lstm_model = train_lstm_model()

print("\n3. Training RL Irrigation Agent...")
print("-" * 70)
from ml_advanced.rl_irrigation_agent import train_rl_agent
rl_agent, rewards, water = train_rl_agent(episodes=100)

print("\n" + "=" * 70)
print("ALL MODELS TRAINED SUCCESSFULLY!")
print("=" * 70)

print("\nModels saved:")
print("  - LSTM Forecaster: models/lstm_forecaster/")
print("  - RL Agent: models/rl_irrigation_agent/")

print("\nNext steps:")
print("  1. Integrate LSTM into MAS for predictions")
print("  2. Use RL agent for irrigation decisions")
print("  3. Compare RL vs rule-based performance")
