"""
ML-Enhanced Decision Agent

Combines rule-based decisions with ML predictions:
- LSTM for time-series forecasting
- RL agent for optimal irrigation
- Ensemble decision making
"""

import numpy as np
from typing import Dict, Any, Optional
import logging
from pathlib import Path
from datetime import datetime

from .base_agent import BaseAgent, AgentMessage, MessagePriority

logger = logging.getLogger(__name__)

class MLDecisionAgent(BaseAgent):
    """
    Decision Agent enhanced with ML models
    
    Capabilities:
    - LSTM predictions for future plant health
    - RL-based irrigation optimization
    - Ensemble decisions (ML + rules)
    - Confidence scoring
    """
    
    def __init__(self, agent_id: str = "ml_decision_agent_001", farm_id: str = "farm_001"):
        super().__init__(agent_id, "MLDecisionAgent")
        self.farm_id = farm_id
        
        # Decision thresholds (calibrated from data)
        self.irrigation_threshold = 32.2
        self.fertilization_threshold = 26.7
        
        # ML models (lazy loaded)
        self.lstm_model = None
        self.rl_agent = None
        self.models_loaded = False
        
        # Decision history
        self.decision_history = []
        self.max_history = 1000
        
        # Sensor history for LSTM
        self.sensor_history = []
        self.sequence_length = 24
        
        # Performance tracking
        self.ml_decisions = 0
        self.rule_decisions = 0
        self.ensemble_decisions = 0
        
        # Initialize beliefs
        self.add_belief("ml_enabled", False)
        self.add_belief("lstm_available", False)
        self.add_belief("rl_available", False)
        self.add_belief("last_prediction", None)
        
        # Try to load models
        self._load_models()
        
        logger.info(f"MLDecisionAgent initialized (ML enabled: {self.models_loaded})")
    
    def _load_models(self):
        """Load ML models if available"""
        try:
            # Check if models exist
            lstm_path = Path("models/lstm_forecaster")
            rl_path = Path("models/rl_irrigation_agent")
            
            if lstm_path.exists():
                logger.info("Loading LSTM model...")
                from ml_advanced.lstm_forecaster import PlantHealthLSTM
                self.lstm_model = PlantHealthLSTM()
                self.lstm_model.load(str(lstm_path))
                self.update_belief("lstm_available", True)
                logger.info("✓ LSTM model loaded")
            
            if rl_path.exists():
                try:
                    logger.info("Loading RL agent...")
                    from ml_advanced.rl_irrigation_agent import DQNAgent
                    self.rl_agent = DQNAgent()
                    self.rl_agent.load(str(rl_path))
                    self.update_belief("rl_available", True)
                    logger.info("✓ RL agent loaded")
                except Exception as e:
                    logger.warning(f"RL agent exists but couldn't load: {e}")
                    logger.info("Using LSTM + rule-based decisions only")
            
            if self.lstm_model or self.rl_agent:
                self.models_loaded = True
                self.update_belief("ml_enabled", True)
                logger.info("✓ ML models ready")
            else:
                logger.warning("No ML models found - using rule-based decisions only")
        
        except Exception as e:
            logger.error(f"Error loading ML models: {e}")
            self.models_loaded = False
    
    async def process_sensor_data(self, data: Dict[str, Any]):
        """Process sensor data and make decisions"""
        # Store in history for LSTM
        self.sensor_history.append(data)
        if len(self.sensor_history) > self.sequence_length:
            self.sensor_history.pop(0)
        
        # Get decisions from different methods
        rule_decision = self._rule_based_decision(data)
        ml_decision = self._ml_based_decision(data) if self.models_loaded else None
        
        # Ensemble decision
        final_decision = self._ensemble_decision(rule_decision, ml_decision, data)
        
        # Log decision
        self.decision_history.append({
            'timestamp': datetime.now().isoformat(),
            'data': data,
            'rule_decision': rule_decision,
            'ml_decision': ml_decision,
            'final_decision': final_decision,
            'method': final_decision.get('method', 'rule')
        })
        
        if len(self.decision_history) > self.max_history:
            self.decision_history.pop(0)
        
        return final_decision
    
    def _rule_based_decision(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Traditional rule-based decision"""
        decision = {
            'method': 'rule',
            'irrigate': False,
            'fertilize': False,
            'confidence': 0.8,
            'reason': []
        }
        
        # Irrigation decision
        soil_moisture = data.get('soil_moisture', 50)
        if soil_moisture < self.irrigation_threshold:
            decision['irrigate'] = True
            decision['reason'].append(f"Soil moisture {soil_moisture:.1f}% < {self.irrigation_threshold}%")
        
        # Fertilization decision
        nitrogen = data.get('nitrogen', 35)
        if nitrogen and nitrogen < self.fertilization_threshold:
            decision['fertilize'] = True
            decision['reason'].append(f"Nitrogen {nitrogen:.1f} < {self.fertilization_threshold}")
        
        self.rule_decisions += 1
        return decision
    
    def _ml_based_decision(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """ML-based decision using LSTM and RL"""
        if not self.models_loaded:
            return None
        
        decision = {
            'method': 'ml',
            'irrigate': False,
            'fertilize': False,
            'confidence': 0.0,
            'reason': [],
            'predictions': {}
        }
        
        try:
            # LSTM prediction (if enough history)
            if self.lstm_model and len(self.sensor_history) >= self.sequence_length:
                sequence = self._prepare_lstm_sequence()
                prediction = self.lstm_model.predict(sequence)
                
                classes = ['Healthy', 'Moderate Stress', 'High Stress']
                predicted_class = classes[np.argmax(prediction)]
                confidence = float(np.max(prediction))
                
                decision['predictions']['health'] = {
                    'class': predicted_class,
                    'confidence': confidence,
                    'probabilities': {cls: float(prob) for cls, prob in zip(classes, prediction)}
                }
                
                # Decision based on prediction
                if predicted_class == 'High Stress' and confidence > 0.7:
                    decision['irrigate'] = True
                    decision['reason'].append(f"LSTM predicts {predicted_class} (conf: {confidence:.2f})")
                
                decision['confidence'] = confidence
            
            # RL agent decision (if available)
            if self.rl_agent:
                state = self._prepare_rl_state(data)
                action = self.rl_agent.act(state, training=False)
                
                actions = ['none', 'light', 'medium', 'heavy']
                decision['predictions']['irrigation'] = {
                    'action': actions[action],
                    'action_id': int(action)
                }
                
                if action > 0:
                    decision['irrigate'] = True
                    decision['reason'].append(f"RL agent recommends {actions[action]} irrigation")
            
            self.ml_decisions += 1
            return decision
        
        except Exception as e:
            logger.error(f"Error in ML decision: {e}")
            return None
    
    def _ensemble_decision(self, rule_decision: Dict, ml_decision: Optional[Dict], 
                          data: Dict) -> Dict[str, Any]:
        """Combine rule-based and ML decisions"""
        if not ml_decision:
            return rule_decision
        
        # Ensemble strategy: Use ML if high confidence, otherwise use rules
        ml_confidence = ml_decision.get('confidence', 0)
        
        if ml_confidence > 0.8:
            # High confidence ML - use ML decision
            self.ensemble_decisions += 1
            return {
                **ml_decision,
                'method': 'ensemble_ml',
                'rule_agreement': rule_decision['irrigate'] == ml_decision['irrigate']
            }
        elif ml_confidence > 0.6:
            # Medium confidence - combine both
            self.ensemble_decisions += 1
            return {
                'method': 'ensemble_combined',
                'irrigate': rule_decision['irrigate'] or ml_decision['irrigate'],
                'fertilize': rule_decision['fertilize'] or ml_decision['fertilize'],
                'confidence': (ml_confidence + rule_decision['confidence']) / 2,
                'reason': rule_decision['reason'] + ml_decision['reason'],
                'predictions': ml_decision.get('predictions', {})
            }
        else:
            # Low confidence ML - use rules
            return {
                **rule_decision,
                'method': 'ensemble_rule',
                'ml_confidence_low': ml_confidence
            }
    
    def _prepare_lstm_sequence(self) -> np.ndarray:
        """Prepare sequence for LSTM prediction"""
        sequence = []
        for data in self.sensor_history[-self.sequence_length:]:
            sequence.append([
                data.get('soil_moisture', 0),
                data.get('temperature', 0),
                data.get('soil_temperature', 0),
                data.get('humidity', 0),
                data.get('light', 0),
                data.get('soil_ph', 6.5),
                data.get('nitrogen', 0),
                data.get('phosphorus', 0),
                data.get('potassium', 0),
                data.get('chlorophyll', 0),
                data.get('electrochemical', 0)
            ])
        return np.array(sequence)
    
    def _prepare_rl_state(self, data: Dict) -> np.ndarray:
        """Prepare state for RL agent"""
        # Simplified state for RL
        state = np.array([
            data.get('soil_moisture', 0) / 100.0,
            data.get('temperature', 0) / 50.0,
            data.get('humidity', 0) / 100.0,
            0.5,  # days_since_irrigation (would need to track)
            0.8   # crop_health (would calculate)
        ])
        return state
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        total = self.rule_decisions + self.ml_decisions + self.ensemble_decisions
        
        return {
            'total_decisions': total,
            'rule_decisions': self.rule_decisions,
            'ml_decisions': self.ml_decisions,
            'ensemble_decisions': self.ensemble_decisions,
            'ml_enabled': self.models_loaded,
            'lstm_available': self.get_belief("lstm_available").value if self.get_belief("lstm_available") else False,
            'rl_available': self.get_belief("rl_available").value if self.get_belief("rl_available") else False
        }
    
    # Implement abstract methods from BaseAgent
    async def perceive(self):
        """Perceive environment - check for new sensor data"""
        # Check inbox for messages
        if not self.inbox.empty():
            message = await self.inbox.get()
            await self.handle_message(message)
    
    async def deliberate(self):
        """Deliberate on current state and update desires"""
        # Update desires based on beliefs
        if self.get_belief("ml_enabled"):
            self.add_desire("use_ml_predictions", priority=10)
        else:
            self.add_desire("use_rule_based", priority=9)
    
    async def act(self):
        """Execute actions based on intentions"""
        # Process any pending sensor data
        pass
    
    async def handle_message(self, message: AgentMessage):
        """Handle incoming messages"""
        if message.message_type == "sensor_data":
            decision = await self.process_sensor_data(message.content)
            
            # Send decision to task agent if action needed
            if decision.get('irrigate') or decision.get('fertilize'):
                await self.send_message(
                    receiver="task_agent_001",
                    message_type="execute_decision",
                    content=decision,
                    priority=MessagePriority.HIGH
                )
