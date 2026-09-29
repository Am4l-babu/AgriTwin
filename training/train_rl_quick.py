"""
Quick RL Agent Training (Reduced Episodes for Testing)

Trains RL agent with fewer episodes for faster completion
"""

import sys
import subprocess

print("=" * 70)
print("QUICK RL AGENT TRAINING")
print("=" * 70)

print("\nInstalling TensorFlow if needed...")
try:
    import tensorflow
    print("  TensorFlow already installed")
except ImportError:
    print("  Installing TensorFlow...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'tensorflow>=2.13.0', '-q'])

print("\nTraining RL Agent (20 episodes for quick testing)...")
print("-" * 70)

from ml_advanced.rl_irrigation_agent import train_rl_agent

# Train with fewer episodes for quick completion
agent, rewards, water = train_rl_agent(episodes=20)

print("\n" + "=" * 70)
print("RL AGENT TRAINING COMPLETE!")
print("=" * 70)

print("\nModel saved to: models/rl_irrigation_agent/")
print("\nNote: This is a quick training run (20 episodes)")
print("For production, run full training: python train_advanced_ml.py")
print("\nNext: Restart backend to load the trained RL agent")
