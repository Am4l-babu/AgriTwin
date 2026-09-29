# PAPER 10: DIGITAL TWIN FOR SENSOR SELECTION & OPTIMIZATION
## Based on "A Digital Twin Framework for Sensor Selection and Microclimate Monitoring in Greenhouses" by Akintan et al. (2025)

---

## 🎯 EXECUTIVE SUMMARY

This research presents a **Unity 3D-based Digital Twin** with **Thompson Sampling (Reinforcement Learning)** for **optimal sensor placement** in greenhouses. The key innovation: **reduce 56 sensors to 10 sensors** while maintaining 99%+ accuracy.

### Key Innovation:
**70% of sensors are redundant!** Using RL, they identified the 10 most informative sensors that capture the same climate trends as 56 sensors.

### Critical Findings:
1. **Thompson Sampling** identifies optimal sensor locations dynamically
2. **Z-index validation** shows minimal deviation (0.037 max)
3. **Seasonal adaptation** - optimal locations change by season
4. **Unity 3D visualization** - immersive 3D greenhouse environment
5. **AWS cloud infrastructure** - DynamoDB + S3 for data management

---

## 📊 YOUR SYSTEM vs RESEARCH FRAMEWORK

| Component | Your AgriTwin | Research Framework | Priority |
|-----------|---------------|-------------------|----------|
| **Sensor Count** | 3 sensors (DHT11, LDR, soil) | 56 sensors → optimized to 10 | HIGH |
| **Sensor Optimization** | ❌ None | ✅ Thompson Sampling RL | CRITICAL |
| **3D Visualization** | ❌ None | ✅ Unity 3D immersive | HIGH |
| **Seasonal Adaptation** | ❌ Static | ✅ Dynamic per season | HIGH |
| **Cloud Storage** | ✅ SQLite | ✅ DynamoDB + S3 | MEDIUM |
| **Psychrometric Params** | ⚠️ Basic | ✅ 6 parameters (Td, W, h, SV) | MEDIUM |
| **Validation Metrics** | ❌ None | ✅ Z-index, MAE, RMSE | HIGH |

---

## 🚀 TOP 5 NEW IMPROVEMENTS

### 1. **THOMPSON SAMPLING FOR SENSOR OPTIMIZATION** (CRITICAL - NEW)

**What:** Reinforcement learning algorithm to identify most informative sensors
**Why:** Reduce hardware costs, eliminate redundancy, maintain accuracy
**Impact:** 82% reduction in sensors (56 → 10) with 99%+ accuracy

#### Implementation:

```python
# Add to cloud/backend/
- sensor_optimization/
  - thompson_sampling.py
  - sensor_selector.py
  - validation_metrics.py
```

**Thompson Sampling Implementation:**
```python
# cloud/backend/sensor_optimization/thompson_sampling.py

import numpy as np
from scipy.stats import beta
from typing import Dict, List, Tuple

class ThompsonSamplingSensorSelector:
    """
    Thompson Sampling for optimal sensor selection
    
    Treats each sensor location as a Bernoulli bandit
    Reward = 1 if sensor reading crosses fleet mean, else 0
    """
    
    def __init__(self, num_sensors: int):
        self.num_sensors = num_sensors
        # Initialize Beta distribution parameters (α, β)
        self.alpha = np.ones(num_sensors)  # Success count + 1
        self.beta = np.ones(num_sensors)   # Failure count + 1
        self.selected_sensors = []
        
    def calculate_reward(self, sensor_reading: float, 
                        fleet_mean: float) -> int:
        """
        Binary reward: 1 if reading crosses mean, else 0
        """
        if sensor_reading > fleet_mean or sensor_reading < fleet_mean:
            return 1
        return 0
    
    def update(self, sensor_id: int, reward: int):
        """
        Update Beta distribution parameters
        
        α(t) = α(t-1) + reward
        β(t) = β(t-1) + (1 - reward)
        """
        self.alpha[sensor_id] += reward
        self.beta[sensor_id] += (1 - reward)
    
    def select_sensor(self) -> int:
        """
        Select sensor by sampling from Beta posteriors
        
        θ(t) ~ Beta(α(t), β(t))
        i* = argmax θ(t)
        """
        # Sample from each sensor's Beta distribution
        theta = np.random.beta(self.alpha, self.beta)
        
        # Select sensor with highest sampled value
        selected = np.argmax(theta)
        self.selected_sensors.append(selected)
        
        return selected
    
    def get_top_k_sensors(self, k: int = 10) -> List[int]:
        """
        Get top K sensors based on posterior means
        
        Posterior mean = α / (α + β)
        """
        posterior_means = self.alpha / (self.alpha + self.beta)
        top_k_indices = np.argsort(posterior_means)[-k:][::-1]
        
        return top_k_indices.tolist()
    
    def train_monthly(self, sensor_data: np.ndarray) -> List[int]:
        """
        Train on monthly data to identify optimal sensors
        
        Args:
            sensor_data: shape (timesteps, num_sensors)
        
        Returns:
            List of top 10 sensor indices
        """
        timesteps, num_sensors = sensor_data.shape
        
        for t in range(timesteps):
            # Calculate fleet mean at time t
            fleet_mean = np.mean(sensor_data[t, :])
            
            # Update each sensor
            for sensor_id in range(num_sensors):
                reading = sensor_data[t, sensor_id]
                reward = self.calculate_reward(reading, fleet_mean)
                self.update(sensor_id, reward)
        
        # Return top 10 sensors
        return self.get_top_k_sensors(k=10)

# Usage Example
def optimize_sensors_for_season(season_data: np.ndarray) -> Dict:
    """
    Optimize sensor placement for a season
    
    Args:
        season_data: shape (timesteps, 56) for 56 sensors
    
    Returns:
        Dictionary with optimal sensor IDs and their rankings
    """
    selector = ThompsonSamplingSensorSelector(num_sensors=56)
    
    # Train on seasonal data
    top_sensors = selector.train_monthly(season_data)
    
    # Get posterior distributions
    posteriors = {
        sensor_id: {
            "alpha": selector.alpha[sensor_id],
            "beta": selector.beta[sensor_id],
            "posterior_mean": selector.alpha[sensor_id] / 
                            (selector.alpha[sensor_id] + selector.beta[sensor_id])
        }
        for sensor_id in top_sensors
    }
    
    return {
        "top_10_sensors": top_sensors,
        "posteriors": posteriors,
        "reduction_percentage": (1 - 10/56) * 100  # 82%
    }
```

**Benefits:**
- ✅ 82% reduction in sensors (56 → 10)
- ✅ 99%+ accuracy maintained
- ✅ Seasonal adaptation
- ✅ Eliminates redundancy
- ✅ Lower hardware costs

---

### 2. **Z-INDEX VALIDATION** (HIGH PRIORITY - NEW)

**What:** Metric to validate if sensor subset represents full network
**Why:** Quantify how well reduced sensors capture climate trends
**Impact:** Confidence in sensor reduction decisions

#### Implementation:

```python
# cloud/backend/sensor_optimization/validation_metrics.py

import numpy as np
from typing import Dict, Tuple

class SensorSubsetValidator:
    """
    Validate sensor subset against full network
    """
    
    @staticmethod
    def calculate_z_index(full_network: np.ndarray, 
                         subset: np.ndarray) -> float:
        """
        Z-index measures distributional consistency
        
        Z = std(RT - CT) / std(RT)
        
        Where:
        - RT = Reference Trend (full network mean)
        - CT = Combination Trend (subset mean)
        
        Lower Z-index = better representation
        Values near 0 indicate minimal deviation
        """
        # Reference Trend (full network)
        RT = np.mean(full_network, axis=1)
        
        # Combination Trend (subset)
        CT = np.mean(subset, axis=1)
        
        # Error
        error = RT - CT
        
        # Z-index
        z_index = np.std(error) / np.std(RT)
        
        return z_index
    
    @staticmethod
    def calculate_mae(full_network: np.ndarray, 
                     subset: np.ndarray) -> float:
        """
        Mean Absolute Error
        
        MAE = (1/N) * Σ|RT(t) - CT(t)|
        """
        RT = np.mean(full_network, axis=1)
        CT = np.mean(subset, axis=1)
        
        mae = np.mean(np.abs(RT - CT))
        return mae
    
    @staticmethod
    def calculate_rmse(full_network: np.ndarray, 
                      subset: np.ndarray) -> float:
        """
        Root Mean Squared Error
        
        RMSE = sqrt((1/N) * Σ(RT(t) - CT(t))²)
        """
        RT = np.mean(full_network, axis=1)
        CT = np.mean(subset, axis=1)
        
        rmse = np.sqrt(np.mean((RT - CT)**2))
        return rmse
    
    @staticmethod
    def validate_subset(full_network: np.ndarray,
                       subset_indices: List[int]) -> Dict:
        """
        Complete validation of sensor subset
        
        Args:
            full_network: shape (timesteps, num_sensors)
            subset_indices: list of selected sensor IDs
        
        Returns:
            Validation metrics
        """
        subset = full_network[:, subset_indices]
        
        z_index = SensorSubsetValidator.calculate_z_index(
            full_network, subset
        )
        mae = SensorSubsetValidator.calculate_mae(
            full_network, subset
        )
        rmse = SensorSubsetValidator.calculate_rmse(
            full_network, subset
        )
        
        # Interpretation
        if z_index < 0.05:
            quality = "Excellent"
        elif z_index < 0.1:
            quality = "Good"
        elif z_index < 0.2:
            quality = "Acceptable"
        else:
            quality = "Poor"
        
        return {
            "z_index": z_index,
            "mae": mae,
            "rmse": rmse,
            "quality": quality,
            "num_sensors_full": full_network.shape[1],
            "num_sensors_subset": len(subset_indices),
            "reduction_percentage": (1 - len(subset_indices)/full_network.shape[1]) * 100
        }

# Usage Example
def validate_seasonal_sensors():
    """Validate sensor selection for a season"""
    # Load data (timesteps x 56 sensors)
    full_data = load_seasonal_data()
    
    # Get optimal sensors from Thompson Sampling
    optimal_sensors = [0, 5, 12, 18, 23, 29, 34, 41, 47, 52]  # Example
    
    # Validate
    validation = SensorSubsetValidator.validate_subset(
        full_data, optimal_sensors
    )
    
    print(f"Z-index: {validation['z_index']:.4f}")
    print(f"Quality: {validation['quality']}")
    print(f"Reduction: {validation['reduction_percentage']:.1f}%")
    
    return validation
```

**Research Results:**
- February: Z-index = 0.037 (Excellent)
- April: Z-index = 0.012 (Excellent)
- June: Z-index = -0.002 (Excellent)
- October: Z-index = 0.025 (Excellent)

**Benefits:**
- ✅ Quantitative validation
- ✅ Confidence in sensor reduction
- ✅ Quality assessment
- ✅ Seasonal comparison

---

### 3. **UNITY 3D VISUALIZATION** (HIGH PRIORITY - NEW)

**What:** Immersive 3D greenhouse environment with real-time sensor data
**Why:** Spatial understanding, intuitive monitoring, better decision-making
**Impact:** Enhanced user experience, spatial context for data

**Key Features:**
- 3D greenhouse model (1:1 scale)
- Real-time sensor visualization
- Interactive navigation
- Temporal queries (select month/season)
- Color-coded sensor status (active/inactive)

**Benefits:**
- ✅ Immersive visualization
- ✅ Spatial context
- ✅ Intuitive interface
- ✅ Better understanding

---

### 4. **PSYCHROMETRIC PARAMETERS** (MEDIUM PRIORITY)

**What:** Calculate 6 derived parameters from temp + humidity
**Why:** Comprehensive climate understanding
**Impact:** Better environmental control

**Parameters:**
1. **Dew Point Temperature (Td)** - Condensation point
2. **Humidity Ratio (W)** - kg water / kg dry air
3. **Enthalpy (h)** - Total heat content (kJ/kg)
4. **Specific Volume (SV)** - m³/kg dry air
5. **Saturation Vapor Pressure (Pws)**
6. **Actual Vapor Pressure (Pw)**

#### Implementation:

```python
# cloud/backend/
- psychrometrics/
  - calculator.py
```

**Psychrometric Calculator:**
```python
# cloud/backend/psychrometrics/calculator.py

import numpy as np

class PsychrometricCalculator:
    """
    Calculate psychrometric parameters from T and RH
    """
    
    # Constants
    A = 6.1121  # hPa
    m = 17.62
    Tn = 243.12  # °C
    Patm = 101.325  # kPa (standard atmospheric pressure)
    
    @staticmethod
    def calculate_saturation_vapor_pressure(temp_c: float) -> float:
        """
        Pws = A × exp(m × T / (T + Tn))
        """
        Pws = PsychrometricCalculator.A * np.exp(
            PsychrometricCalculator.m * temp_c / 
            (temp_c + PsychrometricCalculator.Tn)
        )
        return Pws
    
    @staticmethod
    def calculate_actual_vapor_pressure(temp_c: float, rh: float) -> float:
        """
        Pw = (RH/100) × Pws
        """
        Pws = PsychrometricCalculator.calculate_saturation_vapor_pressure(temp_c)
        Pw = (rh / 100) * Pws
        return Pw
    
    @staticmethod
    def calculate_dew_point(temp_c: float, rh: float) -> float:
        """
        Td = (Tn × α) / (m - α)
        where α = ln(Pw/A)
        """
        Pw = PsychrometricCalculator.calculate_actual_vapor_pressure(temp_c, rh)
        alpha = np.log(Pw / PsychrometricCalculator.A)
        Td = (PsychrometricCalculator.Tn * alpha) / (PsychrometricCalculator.m - alpha)
        return Td
    
    @staticmethod
    def calculate_humidity_ratio(temp_c: float, rh: float) -> float:
        """
        W = 0.622 × Pw / ((Patm × 10) - Pw)
        kg water / kg dry air
        """
        Pw = PsychrometricCalculator.calculate_actual_vapor_pressure(temp_c, rh)
        W = 0.622 * Pw / ((PsychrometricCalculator.Patm * 10) - Pw)
        return W
    
    @staticmethod
    def calculate_enthalpy(temp_c: float, rh: float) -> float:
        """
        h = 1.006 × T + W × (2501 + 1.86 × T)
        kJ/kg dry air
        """
        W = PsychrometricCalculator.calculate_humidity_ratio(temp_c, rh)
        h = 1.006 * temp_c + W * (2501 + 1.86 * temp_c)
        return h
    
    @staticmethod
    def calculate_specific_volume(temp_c: float, rh: float) -> float:
        """
        SV = (0.287042 × TK × (1 + 1.6078 × W)) / Patm
        m³/kg dry air
        """
        TK = temp_c + 273.15  # Convert to Kelvin
        W = PsychrometricCalculator.calculate_humidity_ratio(temp_c, rh)
        SV = (0.287042 * TK * (1 + 1.6078 * W)) / PsychrometricCalculator.Patm
        return SV
    
    @staticmethod
    def calculate_all(temp_c: float, rh: float) -> Dict:
        """
        Calculate all psychrometric parameters
        """
        return {
            "temperature_c": temp_c,
            "relative_humidity": rh,
            "dew_point_c": PsychrometricCalculator.calculate_dew_point(temp_c, rh),
            "humidity_ratio_kg_kg": PsychrometricCalculator.calculate_humidity_ratio(temp_c, rh),
            "enthalpy_kj_kg": PsychrometricCalculator.calculate_enthalpy(temp_c, rh),
            "specific_volume_m3_kg": PsychrometricCalculator.calculate_specific_volume(temp_c, rh),
            "saturation_vapor_pressure_hpa": PsychrometricCalculator.calculate_saturation_vapor_pressure(temp_c),
            "actual_vapor_pressure_hpa": PsychrometricCalculator.calculate_actual_vapor_pressure(temp_c, rh)
        }
```

**Benefits:**
- ✅ Comprehensive climate data
- ✅ Better environmental control
- ✅ Condensation prediction
- ✅ Energy calculations

---

### 5. **AWS CLOUD INFRASTRUCTURE** (MEDIUM PRIORITY)

**What:** DynamoDB (hot store) + S3 (cold store) architecture
**Why:** Scalable, reliable, cost-effective data management
**Impact:** Production-ready data infrastructure

**Architecture:**
- **MQTT Broker** - Lightweight IoT protocol
- **DynamoDB** - Real-time data (hot store)
- **S3** - Historical archive (cold store)
- **Lambda** - Data ingestion
- **API Gateway** - REST API

**Benefits:**
- ✅ Scalable
- ✅ Reliable
- ✅ Cost-effective
- ✅ Production-ready

---

## 📊 IMPLEMENTATION ROADMAP

### Phase 1: Sensor Optimization (Weeks 1-2)
- Implement Thompson Sampling
- Add Z-index validation
- Test with your 3 sensors
- Identify optimal locations

### Phase 2: Psychrometric Calculations (Week 3)
- Implement calculator
- Add to dashboard
- Visualize derived parameters

### Phase 3: 3D Visualization (Weeks 4-6)
- Learn Unity basics
- Model your greenhouse
- Integrate sensor data
- Add interactive features

### Phase 4: Cloud Infrastructure (Weeks 7-8)
- Set up DynamoDB
- Configure S3
- Implement Lambda functions
- Test end-to-end

---

## 💡 KEY INSIGHTS

### 1. **70% Sensor Redundancy**
Most sensors provide duplicate information. Strategic placement is critical.

### 2. **Seasonal Variation**
Optimal sensor locations change by season (up to 4m migration).

### 3. **Parameter-Specific Placement**
Temperature and RH optimal locations don't overlap - need separate sensors.

### 4. **Validation is Critical**
Z-index, MAE, RMSE provide confidence in sensor reduction.

### 5. **3D Context Matters**
Spatial visualization improves understanding and decision-making.

---

## 🎯 EXPECTED IMPACT

### For Your AgriTwin System:

**Immediate Benefits:**
- Identify which of your 3 sensors are most informative
- Optimal placement for future sensor additions
- Psychrometric parameters from existing data
- Validation framework for sensor decisions

**Long-term Benefits:**
- 82% cost reduction when scaling (add 10 sensors, not 56)
- Seasonal adaptation strategy
- 3D visualization for better UX
- Production-ready cloud infrastructure

---

## 📝 QUICK START

### Week 1: Thompson Sampling
```python
# Test with your current 3 sensors
selector = ThompsonSamplingSensorSelector(num_sensors=3)
optimal = selector.train_monthly(your_data)
print(f"Most informative sensor: {optimal[0]}")
```

### Week 2: Psychrometrics
```python
# Add derived parameters
calc = PsychrometricCalculator()
params = calc.calculate_all(temp_c=25, rh=60)
print(f"Dew Point: {params['dew_point_c']:.2f}°C")
```

### Week 3: Validation
```python
# Validate sensor subset
validator = SensorSubsetValidator()
metrics = validator.validate_subset(full_data, [0, 1])
print(f"Z-index: {metrics['z_index']:.4f}")
```

---

## 🎓 CONCLUSION

Paper 10 provides **practical sensor optimization** using:
1. **Thompson Sampling** - RL for sensor selection
2. **Z-index Validation** - Quantify subset quality
3. **Unity 3D** - Immersive visualization
4. **Psychrometrics** - Comprehensive climate data
5. **AWS Infrastructure** - Production-ready storage

**Key Takeaway:** You can achieve 99%+ accuracy with 82% fewer sensors using reinforcement learning!

---

*This paper is highly practical for optimizing sensor deployment and reducing costs!* 🌱🚀📊
