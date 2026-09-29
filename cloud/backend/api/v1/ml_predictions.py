"""
ML Predictions API

Provides endpoints for:
- LSTM health predictions
- RL irrigation recommendations
- Ensemble decision making
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import numpy as np
import logging
from pathlib import Path

router = APIRouter(prefix="/ml", tags=["ML Predictions"])
logger = logging.getLogger(__name__)

# Global model instances (lazy loaded)
lstm_model = None
rl_agent = None
models_loaded = False

class SensorData(BaseModel):
    soil_moisture: float
    temperature: float
    humidity: float
    light: float
    soil_ph: Optional[float] = 6.5
    nitrogen: Optional[float] = 35.0
    phosphorus: Optional[float] = 30.0
    potassium: Optional[float] = 30.0
    chlorophyll: Optional[float] = 35.0
    electrochemical: Optional[float] = 1.0

class SensorSequence(BaseModel):
    sequence: List[SensorData]

class PredictionResponse(BaseModel):
    prediction: str
    confidence: float
    probabilities: Dict[str, float]
    method: str

class IrrigationRecommendation(BaseModel):
    action: str
    action_id: int
    confidence: float
    water_amount: int
    reason: str

def load_models():
    """Load ML models if available"""
    global lstm_model, rl_agent, models_loaded
    
    if models_loaded:
        return
    
    try:
        # Use absolute paths - go up from cloud/backend/api/v1/ to project root
        # __file__ is in cloud/backend/api/v1/ml_predictions.py
        # Need to go up 4 levels to get to cloud/, then up 1 more to project root
        api_dir = Path(__file__).parent  # cloud/backend/api/v1
        backend_dir = api_dir.parent  # cloud/backend/api
        cloud_dir = backend_dir.parent  # cloud/backend
        project_root = cloud_dir.parent.parent  # cloud -> project root
        
        lstm_path = project_root / "models" / "lstm_forecaster"
        rl_path = project_root / "models" / "rl_irrigation_agent"
        
        logger.info(f"Looking for models in: {project_root / 'models'}")
        
        if lstm_path.exists():
            from ml_advanced.lstm_forecaster import PlantHealthLSTM
            lstm_model = PlantHealthLSTM()
            lstm_model.load(str(lstm_path))
            logger.info("✓ LSTM model loaded")
        else:
            logger.warning(f"LSTM path not found: {lstm_path}")
        
        if rl_path.exists():
            from ml_advanced.rl_irrigation_agent import DQNAgent
            rl_agent = DQNAgent()
            rl_agent.load(str(rl_path))
            logger.info("✓ RL agent loaded")
        else:
            logger.warning(f"RL path not found: {rl_path}")
        
        models_loaded = True
        logger.info("ML models loading complete")
    
    except Exception as e:
        logger.error(f"Error loading ML models: {e}")
        import traceback
        logger.error(traceback.format_exc())

@router.on_event("startup")
async def startup():
    """Load models on startup"""
    load_models()

@router.get("/status", summary="Get ML Models Status")
async def get_ml_status():
    """Check if ML models are loaded and available"""
    load_models()
    
    return {
        "models_loaded": models_loaded,
        "lstm_available": lstm_model is not None,
        "rl_available": rl_agent is not None,
        "lstm_path": "models/lstm_forecaster",
        "rl_path": "models/rl_irrigation_agent"
    }

@router.post("/predict/health", response_model=PredictionResponse, 
             summary="Predict Plant Health (LSTM)")
async def predict_health(sequence: SensorSequence):
    """
    Predict plant health using LSTM time-series model
    
    Requires 24 past sensor readings to make prediction
    """
    load_models()
    
    if not lstm_model:
        raise HTTPException(
            status_code=503,
            detail="LSTM model not available. Train model first: python train_advanced_ml.py"
        )
    
    if len(sequence.sequence) < 24:
        raise HTTPException(
            status_code=400,
            detail=f"Need 24 sensor readings, got {len(sequence.sequence)}"
        )
    
    try:
        # Prepare sequence
        seq_array = []
        for data in sequence.sequence[-24:]:
            seq_array.append([
                data.soil_moisture,
                data.temperature,
                data.temperature,  # soil_temperature (using same for now)
                data.humidity,
                data.light,
                data.soil_ph,
                data.nitrogen,
                data.phosphorus,
                data.potassium,
                data.chlorophyll,
                data.electrochemical
            ])
        
        seq_array = np.array(seq_array)
        
        # Predict
        prediction = lstm_model.predict(seq_array)
        classes = ['Healthy', 'Moderate Stress', 'High Stress']
        
        predicted_class = classes[np.argmax(prediction)]
        confidence = float(np.max(prediction))
        
        return PredictionResponse(
            prediction=predicted_class,
            confidence=confidence,
            probabilities={
                cls: float(prob) for cls, prob in zip(classes, prediction)
            },
            method="LSTM"
        )
    
    except Exception as e:
        logger.error(f"Error in LSTM prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recommend/irrigation", response_model=IrrigationRecommendation,
             summary="Get Irrigation Recommendation (RL)")
async def recommend_irrigation(data: SensorData):
    """
    Get irrigation recommendation using RL agent
    
    Returns optimal irrigation action based on current conditions
    """
    load_models()
    
    if not rl_agent:
        raise HTTPException(
            status_code=503,
            detail="RL agent not available. Train model first: python train_advanced_ml.py"
        )
    
    try:
        # Prepare state
        state = np.array([
            data.soil_moisture / 100.0,
            data.temperature / 50.0,
            data.humidity / 100.0,
            0.5,  # days_since_irrigation (would need to track)
            0.8   # crop_health (would calculate)
        ])
        
        # Get action
        action = rl_agent.act(state, training=False)
        
        actions = ['none', 'light', 'medium', 'heavy']
        water_amounts = [0, 50, 100, 150]
        
        # Generate reason
        reasons = {
            0: "Soil moisture is adequate, no irrigation needed",
            1: "Light irrigation recommended to maintain optimal moisture",
            2: "Medium irrigation needed to prevent stress",
            3: "Heavy irrigation required - soil moisture critically low"
        }
        
        return IrrigationRecommendation(
            action=actions[action],
            action_id=action,
            confidence=0.85,  # RL agent confidence (would calculate from Q-values)
            water_amount=water_amounts[action],
            reason=reasons[action]
        )
    
    except Exception as e:
        logger.error(f"Error in RL recommendation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/predict/ensemble", summary="Ensemble Prediction")
async def ensemble_prediction(data: SensorData, sequence: Optional[SensorSequence] = None):
    """
    Get ensemble prediction combining rule-based + ML methods
    
    Uses both LSTM (if sequence provided) and RL agent
    """
    load_models()
    
    result = {
        "rule_based": None,
        "lstm": None,
        "rl": None,
        "ensemble": None
    }
    
    # Rule-based decision
    rule_decision = {
        "irrigate": data.soil_moisture < 32.2,
        "fertilize": data.nitrogen < 26.7 if data.nitrogen else False,
        "confidence": 0.8,
        "method": "rule"
    }
    result["rule_based"] = rule_decision
    
    # LSTM prediction (if sequence provided)
    if lstm_model and sequence and len(sequence.sequence) >= 24:
        try:
            seq_array = []
            for d in sequence.sequence[-24:]:
                seq_array.append([
                    d.soil_moisture, d.temperature, d.temperature,
                    d.humidity, d.light, d.soil_ph,
                    d.nitrogen, d.phosphorus, d.potassium,
                    d.chlorophyll, d.electrochemical
                ])
            
            prediction = lstm_model.predict(np.array(seq_array))
            classes = ['Healthy', 'Moderate Stress', 'High Stress']
            
            result["lstm"] = {
                "prediction": classes[np.argmax(prediction)],
                "confidence": float(np.max(prediction)),
                "probabilities": {cls: float(p) for cls, p in zip(classes, prediction)}
            }
        except Exception as e:
            logger.error(f"LSTM error: {e}")
    
    # RL recommendation
    if rl_agent:
        try:
            state = np.array([
                data.soil_moisture / 100.0,
                data.temperature / 50.0,
                data.humidity / 100.0,
                0.5, 0.8
            ])
            action = rl_agent.act(state, training=False)
            actions = ['none', 'light', 'medium', 'heavy']
            
            result["rl"] = {
                "action": actions[action],
                "action_id": action,
                "irrigate": action > 0
            }
        except Exception as e:
            logger.error(f"RL error: {e}")
    
    # Ensemble decision
    ensemble = {
        "irrigate": rule_decision["irrigate"],
        "fertilize": rule_decision["fertilize"],
        "method": "ensemble",
        "confidence": 0.8
    }
    
    # Adjust based on ML if available
    if result["lstm"] and result["lstm"]["confidence"] > 0.7:
        if result["lstm"]["prediction"] == "High Stress":
            ensemble["irrigate"] = True
            ensemble["confidence"] = result["lstm"]["confidence"]
    
    if result["rl"] and result["rl"]["irrigate"]:
        ensemble["irrigate"] = True
    
    result["ensemble"] = ensemble
    
    return result

@router.get("/models/info", summary="Get Model Information")
async def get_model_info():
    """Get detailed information about loaded models"""
    load_models()
    
    info = {
        "lstm": None,
        "rl": None
    }
    
    if lstm_model:
        info["lstm"] = {
            "type": "LSTM Time-Series Forecaster",
            "sequence_length": 24,
            "features": 11,
            "classes": ["Healthy", "Moderate Stress", "High Stress"],
            "description": "Predicts plant health 24 hours ahead based on sensor history"
        }
    
    if rl_agent:
        info["rl"] = {
            "type": "Deep Q-Network (DQN)",
            "state_size": 5,
            "action_size": 4,
            "actions": ["none", "light", "medium", "heavy"],
            "description": "Learns optimal irrigation policy to maximize health and minimize water"
        }
    
    return info
