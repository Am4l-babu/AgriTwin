# AI Model Template

This template helps you add a new machine learning model to the digital twin system.

## Model Structure

```
cloud/digital_twin/ai_models/
├── your_model_name/
│   ├── __init__.py
│   ├── model.py           # Model definition
│   ├── trainer.py         # Training script
│   ├── inference.py       # Inference engine
│   ├── preprocessing.py   # Data preprocessing
│   └── config.yaml        # Hyperparameters
```

## Step 1: Define Model (`model.py`)

```python
import torch
import torch.nn as nn
from typing import Dict, Any

class YourModel(nn.Module):
    """
    Description of what this model predicts.
    
    Input: (batch_size, sequence_length, num_features)
    Output: (batch_size, prediction_horizon, num_outputs)
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        self.input_dim = config['input_dim']
        self.hidden_dim = config['hidden_dim']
        self.output_dim = config['output_dim']
        
        # Define layers
        self.lstm = nn.LSTM(
            input_size=self.input_dim,
            hidden_size=self.hidden_dim,
            num_layers=2,
            batch_first=True,
            dropout=0.2
        )
        self.fc = nn.Linear(self.hidden_dim, self.output_dim)
        
    def forward(self, x):
        lstm_out, _ = self.lstm(x)
        predictions = self.fc(lstm_out[:, -1, :])
        return predictions
```

## Step 2: Create Trainer (`trainer.py`)

```python
import torch
from torch.utils.data import DataLoader, Dataset
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class YourModelTrainer:
    """Handles training, validation, and model persistence."""
    
    def __init__(self, model, config: Dict[str, Any]):
        self.model = model
        self.config = config
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model.to(self.device)
        
        self.optimizer = torch.optim.Adam(
            model.parameters(),
            lr=config['learning_rate']
        )
        self.criterion = nn.MSELoss()
        
    def train(self, train_loader: DataLoader, val_loader: DataLoader, epochs: int):
        """Train the model."""
        best_val_loss = float('inf')
        
        for epoch in range(epochs):
            # Training
            train_loss = self._train_epoch(train_loader)
            
            # Validation
            val_loss = self._validate(val_loader)
            
            logger.info(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
            
            # Save best model
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                self.save_model('best_model.pth')
        
        return best_val_loss
    
    def _train_epoch(self, data_loader: DataLoader) -> float:
        """Train one epoch."""
        self.model.train()
        total_loss = 0
        
        for batch_x, batch_y in data_loader:
            batch_x, batch_y = batch_x.to(self.device), batch_y.to(self.device)
            
            self.optimizer.zero_grad()
            predictions = self.model(batch_x)
            loss = self.criterion(predictions, batch_y)
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item()
        
        return total_loss / len(data_loader)
    
    def _validate(self, data_loader: DataLoader) -> float:
        """Validate the model."""
        self.model.eval()
        total_loss = 0
        
        with torch.no_grad():
            for batch_x, batch_y in data_loader:
                batch_x, batch_y = batch_x.to(self.device), batch_y.to(self.device)
                predictions = self.model(batch_x)
                loss = self.criterion(predictions, batch_y)
                total_loss += loss.item()
        
        return total_loss / len(data_loader)
    
    def save_model(self, path: str):
        """Save model checkpoint."""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'config': self.config
        }, path)
        logger.info(f"Model saved to {path}")
    
    @classmethod
    def load_model(cls, model_class, path: str):
        """Load model from checkpoint."""
        checkpoint = torch.load(path)
        model = model_class(checkpoint['config'])
        model.load_state_dict(checkpoint['model_state_dict'])
        return model
```

## Step 3: Create Inference Engine (`inference.py`)

```python
import torch
import numpy as np
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class YourModelInference:
    """Handles model inference in production."""
    
    def __init__(self, model_path: str):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = self._load_model(model_path)
        self.model.eval()
        
    def _load_model(self, path: str):
        """Load trained model."""
        checkpoint = torch.load(path, map_location=self.device)
        # Recreate model from config
        from .model import YourModel
        model = YourModel(checkpoint['config'])
        model.load_state_dict(checkpoint['model_state_dict'])
        model.to(self.device)
        return model
    
    def predict(self, input_data: np.ndarray) -> Dict[str, Any]:
        """
        Make prediction.
        
        Args:
            input_data: Numpy array of shape (sequence_length, num_features)
        
        Returns:
            Dictionary with predictions and confidence
        """
        # Preprocess
        input_tensor = torch.FloatTensor(input_data).unsqueeze(0).to(self.device)
        
        # Inference
        with torch.no_grad():
            predictions = self.model(input_tensor)
        
        # Postprocess
        predictions_np = predictions.cpu().numpy()[0]
        
        # Calculate confidence (example: inverse of prediction variance)
        confidence = self._calculate_confidence(predictions_np)
        
        return {
            'predictions': predictions_np.tolist(),
            'confidence': confidence,
            'model_version': '1.0.0'
        }
    
    def _calculate_confidence(self, predictions: np.ndarray) -> float:
        """Calculate confidence score."""
        # Implement your confidence calculation logic
        return 0.85  # Placeholder
    
    def batch_predict(self, batch_data: List[np.ndarray]) -> List[Dict[str, Any]]:
        """Batch prediction for efficiency."""
        results = []
        for data in batch_data:
            results.append(self.predict(data))
        return results
```

## Step 4: Create Configuration (`config.yaml`)

```yaml
model:
  name: "your_model_name"
  version: "1.0.0"
  description: "Description of what this model does"

architecture:
  input_dim: 10
  hidden_dim: 128
  output_dim: 1
  num_layers: 2
  dropout: 0.2

training:
  learning_rate: 0.001
  batch_size: 32
  epochs: 100
  validation_split: 0.2
  early_stopping_patience: 10

data:
  sequence_length: 30  # 30 days of history
  prediction_horizon: 7  # Predict 7 days ahead
  features:
    - soil_moisture
    - temperature
    - humidity
    - precipitation
    - radiation
  target: yield

preprocessing:
  normalization: "standard"  # standard, minmax, robust
  handle_missing: "interpolate"  # interpolate, forward_fill, drop
  outlier_removal: true
  outlier_threshold: 3.0  # Standard deviations

inference:
  model_path: "models/your_model_name/best_model.pth"
  batch_size: 64
  confidence_threshold: 0.7
```

## Step 5: Integration with Digital Twin

### Register Model (`cloud/digital_twin/model_registry.py`)

```python
from .ai_models.your_model_name.inference import YourModelInference

class ModelRegistry:
    def __init__(self):
        self.models = {
            'yield_prediction': YieldPredictionModel(),
            'your_model_name': YourModelInference('path/to/model.pth')  # Add here
        }
```

### Add API Endpoint (`cloud/backend/api/v1/predictions.py`)

```python
@router.post("/your-prediction")
async def predict_your_model(
    farm_id: str,
    input_data: YourInputSchema,
    db: AsyncSession = Depends(get_db)
):
    """Your model prediction endpoint."""
    # Get model from registry
    model = model_registry.get_model('your_model_name')
    
    # Prepare input
    sensor_data = await fetch_sensor_history(farm_id, days=30)
    
    # Predict
    result = model.predict(sensor_data)
    
    # Store prediction
    await store_prediction(db, farm_id, 'your_model_name', result)
    
    return result
```

## Step 6: Testing

```python
# tests/ai_models/test_your_model.py
import pytest
import torch
from cloud.digital_twin.ai_models.your_model_name.model import YourModel
from cloud.digital_twin.ai_models.your_model_name.inference import YourModelInference

def test_model_forward_pass():
    config = {'input_dim': 10, 'hidden_dim': 128, 'output_dim': 1}
    model = YourModel(config)
    
    # Create dummy input
    x = torch.randn(8, 30, 10)  # batch_size=8, seq_len=30, features=10
    output = model(x)
    
    assert output.shape == (8, 1)

def test_inference():
    model_path = 'path/to/test_model.pth'
    inference = YourModelInference(model_path)
    
    # Create dummy data
    data = np.random.randn(30, 10)
    result = inference.predict(data)
    
    assert 'predictions' in result
    assert 'confidence' in result
```

## Training Script Example

```bash
python cloud/digital_twin/ai_models/your_model_name/trainer.py \
    --config cloud/digital_twin/ai_models/your_model_name/config.yaml \
    --data-path data/training_data.csv \
    --output-dir models/your_model_name
```

## Model Versioning

- Store models in `backend/models/your_model_name/v{version}/`
- Use MLflow or similar for experiment tracking
- Tag production models in model registry
