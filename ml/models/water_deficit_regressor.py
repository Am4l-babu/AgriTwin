"""
Water-Deficit Regressor
========================
Predicts continuous water deficit (mm) from sensor readings.

Model: Gradient Boosting Regressor (primary) + Ridge baseline
"""

import os
import pickle
import numpy as np
from typing import Dict

from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

FEATURE_COLS = [
    "temperature", "humidity", "light_level", "soil_moisture_pct",
    "solar_radiation", "hour_of_day",
    "moisture_fraction", "evapotranspiration",
    "accumulated_gdd", "growth_progress_pct", "day_of_season",
]

LABEL_COL = "water_deficit_mm"

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "saved_models")
os.makedirs(MODELS_DIR, exist_ok=True)


class WaterDeficitRegressor:
    """Predicts water deficit in mm from sensor/twin features."""

    def __init__(self):
        self.gb_pipeline: Pipeline | None = None
        self.rf_pipeline: Pipeline | None = None
        self.ridge_pipeline: Pipeline | None = None
        self.feature_importances_: Dict[str, float] = {}

    def _build(self):
        self.gb_pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("reg", GradientBoostingRegressor(
                n_estimators=200,
                max_depth=5,
                learning_rate=0.08,
                subsample=0.85,
                random_state=42,
            ))
        ])
        self.rf_pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("reg", RandomForestRegressor(
                n_estimators=200,
                max_depth=12,
                random_state=42,
                n_jobs=-1,
            ))
        ])
        self.ridge_pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("reg", Ridge(alpha=1.0)),
        ])

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        test_size: float = 0.20,
        verbose: bool = True,
    ) -> Dict:
        self._build()

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )

        results = {}
        for name, pipe in [
            ("GradientBoosting", self.gb_pipeline),
            ("RandomForest",     self.rf_pipeline),
            ("Ridge",            self.ridge_pipeline),
        ]:
            pipe.fit(X_train, y_train)
            y_pred = pipe.predict(X_test)

            mae  = float(mean_absolute_error(y_test, y_pred))
            rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
            r2   = float(r2_score(y_test, y_pred))

            cv = cross_val_score(pipe, X_train, y_train, cv=5,
                                 scoring="r2", n_jobs=-1)

            results[name] = {
                "mae": mae, "rmse": rmse, "r2": r2,
                "cv_r2": float(cv.mean()), "cv_std": float(cv.std()),
            }

            if verbose:
                print(f"\n── {name} ──────────────────────────────────────")
                print(f"  MAE  : {mae:.4f} mm")
                print(f"  RMSE : {rmse:.4f} mm")
                print(f"  R²   : {r2:.4f}")
                print(f"  CV R²: {cv.mean():.4f} ± {cv.std():.4f}")

        # Feature importances
        rf_reg = self.rf_pipeline.named_steps["reg"]
        self.feature_importances_ = {
            col: float(imp)
            for col, imp in zip(FEATURE_COLS, rf_reg.feature_importances_)
        }
        if verbose:
            print("\n── Feature Importances (RandomForest) ──────────────────")
            for col, imp in sorted(self.feature_importances_.items(),
                                   key=lambda x: -x[1]):
                bar = "█" * int(imp * 40)
                print(f"  {col:<28} {imp:.4f}  {bar}")

        return results

    def save(self, path: str | None = None):
        path = path or os.path.join(MODELS_DIR, "water_deficit_regressor.pkl")
        with open(path, "wb") as f:
            pickle.dump({
                "gb_pipeline":         self.gb_pipeline,
                "rf_pipeline":         self.rf_pipeline,
                "ridge_pipeline":      self.ridge_pipeline,
                "feature_importances": self.feature_importances_,
                "feature_cols":        FEATURE_COLS,
            }, f)
        print(f"  Saved WaterDeficitRegressor → {path}")

    @classmethod
    def load(cls, path: str | None = None) -> "WaterDeficitRegressor":
        path = path or os.path.join(MODELS_DIR, "water_deficit_regressor.pkl")
        with open(path, "rb") as f:
            data = pickle.load(f)
        obj = cls()
        obj.gb_pipeline          = data["gb_pipeline"]
        obj.rf_pipeline          = data["rf_pipeline"]
        obj.ridge_pipeline       = data["ridge_pipeline"]
        obj.feature_importances_ = data.get("feature_importances", {})
        return obj

    def predict(self, sensor_data: Dict[str, float]) -> Dict:
        """Predict water deficit (mm) from sensor dict."""
        if self.gb_pipeline is None:
            raise RuntimeError("Model not trained/loaded.")
        X = np.array([[sensor_data.get(c, 0.0) for c in FEATURE_COLS]])
        deficit = float(self.gb_pipeline.predict(X)[0])
        return {
            "water_deficit_mm": round(max(0.0, deficit), 3),
            "model": "GradientBoosting",
        }

    def predict_batch(self, X: np.ndarray) -> np.ndarray:
        return self.gb_pipeline.predict(X)
