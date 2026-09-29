"""
Reinforcement Learning Agent for Optimal Irrigation Scheduling

Uses Deep Q-Network (DQN) to learn optimal irrigation policies
that maximize crop health while minimizing water usage
"""

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from collections import deque
import random
import joblib
from pathlib import Path
import json

class IrrigationEnvironment:
    """
    Simulated environment for irrigation decisions
    
    State: [soil_moisture, temperature, humidity, days_since_irrigation, crop_health]
    Actions: [no_irrigation, light_irrigation, medium_irrigation, heavy_irrigation]
    Reward: Based on crop health improvement and water conservation
    """
    
    def __init__(self, df):
        self.df = df.sort_values(['Plant_ID', 'Timestamp']).reset_index(drop=True)
        self.current_idx = 0
        self.plant_id = 1
        self.days_since_irrigation = 0
        self.total_water_used = 0
        self.episode_length = 30  # 30 days per episode
        self.step_count = 0
        
        # Action effects on soil moisture
        self.irrigation_amounts = {
            0: 0,    # No irrigation
            1: 5,    # Light: +5% moisture
            2: 10,   # Medium: +10% moisture
            3: 15    # Heavy: +15% moisture
        }
        
        # Water costs (liters)
        self.water_costs = {
            0: 0,
            1: 50,
            2: 100,
            3: 150
        }
    
    def reset(self):
        """Reset environment to start new episode"""
        self.plant_id = random.randint(1, 10)
        plant_data = self.df[self.df['Plant_ID'] == self.plant_id]
        self.current_idx = random.randint(0, len(plant_data) - self.episode_length - 1)
        self.days_since_irrigation = 0
        self.total_water_used = 0
        self.step_count = 0
        
        return self._get_state()
    
    def _get_state(self):
        """Get current state"""
        row = self.df.iloc[self.current_idx]
        
        # Normalize state values
        state = np.array([
            row['Soil_Moisture'] / 100.0,  # 0-1
            row['Ambient_Temperature'] / 50.0,  # 0-1
            row['Humidity'] / 100.0,  # 0-1
            min(self.days_since_irrigation / 7.0, 1.0),  # 0-1
            self._get_health_score(row) / 100.0  # 0-1
        ])
        
        return state
    
    def _get_health_score(self, row):
        """Calculate health score from row data"""
        # Simple health score based on soil moisture and nitrogen
        moisture_score = max(0, 100 - abs(row['Soil_Moisture'] - 35) * 3)
        nitrogen_score = max(0, 100 - abs(row['Nitrogen_Level'] - 35) * 2)
        return (moisture_score + nitrogen_score) / 2
    
    def step(self, action):
        """
        Take action and return next state, reward, done
        
        Args:
            action: 0=none, 1=light, 2=medium, 3=heavy
            
        Returns:
            next_state, reward, done, info
        """
        # Apply irrigation
        moisture_increase = self.irrigation_amounts[action]
        water_used = self.water_costs[action]
        
        # Update state
        if action > 0:
            self.days_since_irrigation = 0
        else:
            self.days_since_irrigation += 1
        
        self.total_water_used += water_used
        
        # Get current and next health
        current_health = self._get_health_score(self.df.iloc[self.current_idx])
        
        # Move to next timestep
        self.current_idx += 1
        self.step_count += 1
        
        # Simulate moisture increase from irrigation
        next_row = self.df.iloc[self.current_idx].copy()
        next_row['Soil_Moisture'] = min(100, next_row['Soil_Moisture'] + moisture_increase)
        
        next_health = self._get_health_score(next_row)
        
        # Calculate reward
        reward = self._calculate_reward(
            current_health, next_health, water_used, action
        )
        
        # Check if episode is done
        done = self.step_count >= self.episode_length
        
        next_state = self._get_state()
        
        info = {
            'health': next_health,
            'water_used': water_used,
            'total_water': self.total_water_used
        }
        
        return next_state, reward, done, info
    
    def _calculate_reward(self, current_health, next_health, water_used, action):
        """
        Calculate reward for action
        
        Reward components:
        1. Health improvement: +10 per point
        2. Maintaining high health: +5 if health > 80
        3. Water conservation: -0.1 per liter
        4. Penalty for over-irrigation: -20 if unnecessary
        """
        reward = 0
        
        # Health improvement
        health_delta = next_health - current_health
        reward += health_delta * 10
        
        # Bonus for maintaining high health
        if next_health > 80:
            reward += 5
        
        # Water cost
        reward -= water_used * 0.1
        
        # Penalty for over-irrigation (irrigating when moisture is already high)
        if action > 0 and current_health > 75:
            reward -= 20
        
        # Penalty for under-irrigation (not irrigating when health is low)
        if action == 0 and current_health < 50:
            reward -= 10
        
        return reward


class DQNAgent:
    """Deep Q-Network agent for irrigation decisions"""
    
    def __init__(self, state_size=5, action_size=4):
        self.state_size = state_size
        self.action_size = action_size
        
        # Hyperparameters
        self.gamma = 0.95  # Discount factor
        self.epsilon = 1.0  # Exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001
        self.batch_size = 32
        
        # Replay memory
        self.memory = deque(maxlen=2000)
        
        # Q-Networks
        self.model = self._build_model()
        self.target_model = self._build_model()
        self.update_target_model()
    
    def _build_model(self):
        """Build neural network for Q-learning"""
        model = keras.Sequential([
            layers.Dense(64, activation='relu', input_shape=(self.state_size,)),
            layers.Dropout(0.2),
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(32, activation='relu'),
            layers.Dense(self.action_size, activation='linear')
        ])
        
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=self.learning_rate),
            loss='mean_squared_error'  # Use full name for Keras 3.x compatibility
        )
        
        return model
    
    def update_target_model(self):
        """Copy weights from model to target_model"""
        self.target_model.set_weights(self.model.get_weights())
    
    def remember(self, state, action, reward, next_state, done):
        """Store experience in replay memory"""
        self.memory.append((state, action, reward, next_state, done))
    
    def act(self, state, training=True):
        """
        Choose action using epsilon-greedy policy
        
        Args:
            state: Current state
            training: If True, use epsilon-greedy; if False, use greedy
            
        Returns:
            action: Selected action
        """
        if training and np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        
        q_values = self.model.predict(state.reshape(1, -1), verbose=0)
        return np.argmax(q_values[0])
    
    def replay(self):
        """Train on batch from replay memory"""
        if len(self.memory) < self.batch_size:
            return
        
        # Sample batch
        batch = random.sample(self.memory, self.batch_size)
        
        states = np.array([exp[0] for exp in batch])
        actions = np.array([exp[1] for exp in batch])
        rewards = np.array([exp[2] for exp in batch])
        next_states = np.array([exp[3] for exp in batch])
        dones = np.array([exp[4] for exp in batch])
        
        # Predict Q-values
        current_q = self.model.predict(states, verbose=0)
        next_q = self.target_model.predict(next_states, verbose=0)
        
        # Update Q-values
        for i in range(self.batch_size):
            if dones[i]:
                current_q[i][actions[i]] = rewards[i]
            else:
                current_q[i][actions[i]] = rewards[i] + self.gamma * np.max(next_q[i])
        
        # Train
        self.model.fit(states, current_q, epochs=1, verbose=0)
        
        # Decay epsilon
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
    
    def save(self, path='models/rl_irrigation_agent'):
        """Save agent"""
        Path(path).mkdir(parents=True, exist_ok=True)
        
        # Save using Keras 3.x format
        self.model.save(f'{path}/model.keras')
        self.target_model.save(f'{path}/target_model.keras')
        
        metadata = {
            'state_size': self.state_size,
            'action_size': self.action_size,
            'epsilon': self.epsilon,
            'gamma': self.gamma
        }
        
        with open(f'{path}/metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Agent saved to {path}")
    
    def load(self, path='models/rl_irrigation_agent'):
        """Load agent"""
        # Try new format first (.keras), then fall back to old format (.h5)
        if Path(f'{path}/model.keras').exists():
            self.model = keras.models.load_model(f'{path}/model.keras')
            self.target_model = keras.models.load_model(f'{path}/target_model.keras')
        else:
            # Old format - rebuild and load weights only
            self.model = self._build_model()
            self.target_model = self._build_model()
            
            # Load weights only (avoids serialization issues)
            self.model.load_weights(f'{path}/model.h5')
            self.target_model.load_weights(f'{path}/target_model.h5')
        
        with open(f'{path}/metadata.json', 'r') as f:
            metadata = json.load(f)
            self.epsilon = metadata['epsilon']
        
        print(f"Agent loaded from {path}")


def train_rl_agent(episodes=100):
    """Train RL agent"""
    print("=" * 70)
    print("TRAINING REINFORCEMENT LEARNING IRRIGATION AGENT")
    print("=" * 70)
    
    # Load data
    print("\nLoading data...")
    df = pd.read_csv('data/plant_health_data.csv')
    
    # Initialize environment and agent
    env = IrrigationEnvironment(df)
    agent = DQNAgent(state_size=5, action_size=4)
    
    # Training loop
    print(f"\nTraining for {episodes} episodes...")
    
    rewards_history = []
    water_history = []
    
    for episode in range(episodes):
        state = env.reset()
        total_reward = 0
        
        for step in range(env.episode_length):
            # Choose action
            action = agent.act(state)
            
            # Take action
            next_state, reward, done, info = env.step(action)
            
            # Remember
            agent.remember(state, action, reward, next_state, done)
            
            # Learn
            agent.replay()
            
            total_reward += reward
            state = next_state
            
            if done:
                break
        
        # Update target network
        if episode % 10 == 0:
            agent.update_target_model()
        
        rewards_history.append(total_reward)
        water_history.append(env.total_water_used)
        
        # Print progress
        if (episode + 1) % 10 == 0:
            avg_reward = np.mean(rewards_history[-10:])
            avg_water = np.mean(water_history[-10:])
            print(f"Episode {episode + 1}/{episodes} | "
                  f"Avg Reward: {avg_reward:.2f} | "
                  f"Avg Water: {avg_water:.0f}L | "
                  f"Epsilon: {agent.epsilon:.3f}")
    
    # Save agent
    agent.save()
    
    print("\n" + "=" * 70)
    print("TRAINING COMPLETE")
    print("=" * 70)
    
    print(f"\nFinal average reward (last 10): {np.mean(rewards_history[-10:]):.2f}")
    print(f"Final average water usage (last 10): {np.mean(water_history[-10:]):.0f}L")
    print(f"Final epsilon: {agent.epsilon:.3f}")
    
    return agent, rewards_history, water_history


if __name__ == '__main__':
    train_rl_agent(episodes=100)
