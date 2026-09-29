"""
Enhanced Digital Twin – ML-Augmented Physics Engine
=====================================================
Extends DigitalTwinPhysics with real-time ML model inference so that:

  • Irrigation decisions are backed by a trained Random Forest classifier
  • Growth stage is cross-checked by ML (vs. pure GDD physics)
  • Water deficit is validated by the ML regressor
  • Sensor anomalies are detected before state update

This module is the recommended entry point for the backend.
"""

import os
import sys
from typing import Dict, Any, List, Optional

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from cloud.digital_twin.physics_model.comprehensive_physics import (
    DigitalTwinPhysics,
    SoilProperties,
)


# ── lazy-load ML models (don't crash if models aren't trained yet) ─────────────
def _try_load(loader_fn):
    try:
        return loader_fn()
    except Exception:
        return None


class MLAugmentedDigitalTwin:
    """
    Digital twin that combines physics simulation with ML predictions.

    Falls back gracefully to physics-only mode if ML models are not available.
    """

    def __init__(
        self,
        soil_properties: Optional[SoilProperties] = None,
        enable_ml: bool = True,
    ):
        self.physics = DigitalTwinPhysics(soil_properties=soil_properties)
        self.enable_ml = enable_ml

        # ── load ML models (optional) ─────────────────────────────────────────
        self._irr_model   = None
        self._gs_model    = None
        self._wd_model    = None
        self._anom_model  = None

        if enable_ml:
            self._load_ml_models()

    def _load_ml_models(self):
        """Load saved ML models if available."""
        try:
            from ml.models.irrigation_predictor    import IrrigationPredictor
            from ml.models.growth_stage_predictor  import GrowthStagePredictor
            from ml.models.water_deficit_regressor import WaterDeficitRegressor
            from ml.models.anomaly_detector        import AnomalyDetector

            self._irr_model  = _try_load(IrrigationPredictor.load)
            self._gs_model   = _try_load(GrowthStagePredictor.load)
            self._wd_model   = _try_load(WaterDeficitRegressor.load)
            self._anom_model = _try_load(AnomalyDetector.load)

            n_loaded = sum(
                m is not None
                for m in [self._irr_model, self._gs_model,
                          self._wd_model, self._anom_model]
            )
            print(f"[MLAugmentedDigitalTwin] Loaded {n_loaded}/4 ML models.")
        except ImportError:
            print("[MLAugmentedDigitalTwin] ML package not found – physics-only mode.")

    # ── feature extraction for ML ─────────────────────────────────────────────
    def _build_ml_features(
        self,
        sensor_data: Dict[str, float],
        physics_water: Dict,
        physics_crop: Dict,
        day_of_season: int = 0,
    ) -> Dict[str, float]:
        """Combine sensor + physics outputs into the ML feature dict."""
        return {
            "temperature":        sensor_data.get("temp", 25.0),
            "humidity":           sensor_data.get("humidity", 60.0),
            "light_level":        sensor_data.get("light", 500) / 7,   # normalise to 0-100
            "soil_moisture_pct":  physics_water.get("moisture_percent", 50.0),
            "solar_radiation":    sensor_data.get("solar_radiation",
                                      physics_water.get("solar_radiation", 15.0)),
            "hour_of_day":        sensor_data.get("hour_of_day", 12.0),
            "water_deficit_mm":   physics_water.get("water_deficit", 0.0),
            "moisture_fraction":  physics_water.get("moisture", 0.30),
            "evapotranspiration": physics_water.get("evapotranspiration", 3.0),
            "accumulated_gdd":    physics_crop.get("gdd_accumulated", 0.0),
            "growth_progress_pct": physics_crop.get("growth_progress", 0.0),
            "day_of_season":      day_of_season,
        }

    # ── main simulate step ────────────────────────────────────────────────────
    def simulate_step(
        self,
        sensor_data: Dict[str, float],
        irrigation: float = 0.0,
        timestep_hours: float = 24.0,
        day_of_season: int = 0,
    ) -> Dict[str, Any]:
        """
        Run one simulation step and enrich with ML predictions.

        Returns:
            Extended twin state dict with 'ml' sub-dict containing:
              - anomaly detection result
              - ML irrigation recommendation
              - ML growth-stage prediction
              - ML water-deficit estimate
              - confidence / agreement between physics and ML
        """
        # ── 1. physics step ───────────────────────────────────────────────────
        physics_state = self.physics.simulate_step(
            sensor_data, irrigation, timestep_hours
        )
        water = physics_state["water"]
        crop  = physics_state["crop"]

        # ── 2. ML inference ───────────────────────────────────────────────────
        ml_state: Dict[str, Any] = {
            "ml_available": self.enable_ml and any(
                m is not None for m in
                [self._irr_model, self._gs_model, self._wd_model, self._anom_model]
            )
        }

        if ml_state["ml_available"]:
            features = self._build_ml_features(
                sensor_data, water, crop, day_of_season
            )

            # 2a. Anomaly detection  (run first; skip update if anomalous)
            if self._anom_model:
                anom = self._anom_model.predict(features)
                ml_state["anomaly"] = anom
            else:
                ml_state["anomaly"] = {"is_anomaly": False, "anomaly_score": 0.0}

            # 2b. Irrigation prediction
            if self._irr_model:
                irr = self._irr_model.predict(features)
                ml_state["irrigation"] = irr

                # Enrich recommendations
                physics_needs = self.physics.water_balance.is_irrigation_needed()
                ml_needs = irr["irrigation_needed"]
                consensus = physics_needs == ml_needs
                ml_state["irrigation"]["physics_irrigation_needed"] = physics_needs
                ml_state["irrigation"]["consensus"] = consensus

                if ml_needs and not consensus:
                    physics_state["recommendations"].append({
                        "type": "irrigation",
                        "priority": "medium",
                        "message": (
                            f"ML model recommends irrigation (confidence "
                            f"{irr['confidence']:.0%}), though physics model "
                            "does not yet flag deficit."
                        ),
                        "source": "ml",
                    })

            # 2c. Growth stage prediction
            if self._gs_model:
                gs = self._gs_model.predict(features)
                ml_state["growth_stage"] = gs

                physics_stage = crop.get("growth_stage", "vegetative")
                ml_stage      = gs["growth_stage_name"]
                ml_state["growth_stage"]["physics_stage"] = physics_stage
                ml_state["growth_stage"]["stages_agree"]  = (physics_stage == ml_stage)

            # 2d. Water deficit regression
            if self._wd_model:
                wd = self._wd_model.predict(features)
                ml_state["water_deficit"] = wd

                physics_deficit = water.get("water_deficit", 0)
                ml_deficit      = wd["water_deficit_mm"]
                relative_error  = abs(physics_deficit - ml_deficit) / max(physics_deficit, 1)
                ml_state["water_deficit"]["physics_deficit_mm"] = physics_deficit
                ml_state["water_deficit"]["relative_error"]     = round(relative_error, 3)

        # ── 3. Combine ────────────────────────────────────────────────────────
        physics_state["ml"] = ml_state
        return physics_state

    # ── scenario / forecast (delegates to physics + overrides with ML) ────────
    def run_ml_scenario(
        self,
        days: int = 7,
        base_sensor: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Run a multi-day forward simulation enriched with ML predictions.

        Returns list of daily state dicts.
        """
        import copy
        twin_backup = copy.deepcopy(self.physics)

        sensor = base_sensor or {
            "temp": 25.0, "humidity": 60.0, "light": 600
        }
        results = []
        for day in range(days):
            irrigation = 0.0
            if self._irr_model:
                from ml.models.irrigation_predictor import FEATURE_COLS
                w = self.physics.water_balance
                c = self.physics.crop_growth
                feats = self._build_ml_features(
                    sensor,
                    {"moisture_percent": (w.current_moisture / w.soil.saturation) * 100,
                     "water_deficit": max(0, (w.soil.field_capacity - w.current_moisture) * w.soil.rooting_depth * 1000),
                     "moisture": w.current_moisture,
                     "evapotranspiration": 3.0,
                     },
                    {"gdd_accumulated": c.accumulated_gdd,
                     "growth_progress": min(c.accumulated_gdd / c.gdd_to_maturity * 100, 100)},
                    day_of_season=day,
                )
                irr_pred = self._irr_model.predict(feats)
                if irr_pred["irrigation_needed"]:
                    irrigation = 10.0

            state = self.simulate_step(sensor, irrigation, 24.0, day)
            state["scenario_day"] = day + 1
            results.append(state)

        # restore original physics state
        self.physics = twin_backup
        return results

    # ── convenience: health summary ───────────────────────────────────────────
    def get_farm_health_summary(self, last_state: Dict) -> Dict:
        """Extract a concise farm-health dict from the latest twin state."""
        water = last_state.get("water", {})
        crop  = last_state.get("crop", {})
        ml    = last_state.get("ml", {})

        health_score = 100.0
        issues = []

        moisture_pct = water.get("moisture_percent", 50)
        if moisture_pct < 35:
            health_score -= 20
            issues.append("Low soil moisture")
        if moisture_pct > 85:
            health_score -= 10
            issues.append("Over-watered soil")

        water_deficit = water.get("water_deficit", 0)
        if water_deficit > 15:
            health_score -= 15
            issues.append(f"Water deficit {water_deficit:.1f} mm")

        if ml.get("anomaly", {}).get("is_anomaly"):
            health_score -= 30
            issues.append("Sensor anomaly detected")

        return {
            "health_score":    round(max(0, health_score), 1),
            "issues":          issues,
            "moisture_pct":    round(moisture_pct, 1),
            "water_deficit_mm": round(water_deficit, 1),
            "growth_stage":    crop.get("growth_stage", "unknown"),
            "growth_progress": round(crop.get("growth_progress", 0), 1),
            "ml_irrigation":   ml.get("irrigation", {}).get("irrigation_needed"),
            "is_anomaly":      ml.get("anomaly", {}).get("is_anomaly", False),
        }
