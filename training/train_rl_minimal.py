"""
Minimal RL Agent Training (5 episodes for immediate testing)
"""

import sys
import subprocess

print("=" * 70)
print("MINIMAL RL AGENT TRAINING (5 EPISODES)")
print("=" * 70)

print("\nChecking TensorFlow...")
try:
    import tensorflow
    print("  TensorFlow ready")
except ImportError:
    print("  Installing TensorFlow...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'tensorflow>=2.13.0', '-q'])

print("\nTraining RL Agent (5 episodes - minimal for testing)...")
print("-" * 70)

from ml_advanced.rl_irrigation_agent import train_rl_agent

# Train with minimal episodes
agent, rewards, water = train_rl_agent(episodes=5)

print("\n" + "=" * 70)
print("MINIMAL TRAINING COMPLETE!")
print("=" * 70)

print("\nModel saved to: models/rl_irrigation_agent/")
print("\nNote: This is minimal training (5 episodes) for testing only")
print("The agent will work but won't be well-optimized")
print("\nFor better performance, run: python train_rl_quick.py (20 episodes)")
print("For production, run: python train_advanced_ml.py (100 episodes)")
