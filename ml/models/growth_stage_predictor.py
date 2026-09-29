"""
Growth Stage Predictor
======================
Multi-class classifier: vegetative / flowering / fruiting / ripening / mature

Model: Gradient Boosting (primary)
Input features: same 12-column set used by irrigation predictor
"""

import os
import pickle
import numpy as np
from typing import Dict, List

from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, accuracy_score

FEATURE_COLS = [
    "temperature", "humidity", "light_level", "soil_moisture_pct",
    "solar_radiation", "hour_of_day",
    "water_deficit_mm", "moisture_fraction", "evapotranspiration",
    "accumulated_gdd", "growth_progress_pct", "day_of_season",
]

LABEL_COL = "growth_stage"          # integer 0-4

STAGE_NAMES = [
    "vegetative", "flowering", "fruiting", "ripening", "mature"
]

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "saved_models")
os.makedirs(MODELS_DIR, exist_ok=True)


class GrowthStagePredictor:
    """
    Trains and evaluates multi-class growth-stage classifiers.
    """

    def __init__(self):
        self.gb_pipeline: Pipeline | None = None
        self.rf_pipeline: Pipeline | None = None
        self.feature_importances_: Dict[str, float] = {}

    # ── Build ─────────────────────────────────────────────────────────────────
    def _build_pipelines(self):
        self.gb_pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", GradientBoostingClassifier(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.08,
                subsample=0.8,
                random_state=42,
            ))
        ])

        self.rf_pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", RandomForestClassifier(
                n_estimators=200,
                max_depth=14,
                min_samples_leaf=3,
                class_weight="balanced",
                random_state=42,
                n_jobs=-1,
            ))
        ])

    # ── Train ─────────────────────────────────────────────────────────────────
    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        test_size: float = 0.20,
        verbose: bool = True,
    ) -> Dict:
        self._build_pipelines()

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )

        results = {}

        for name, pipe in [
            ("GradientBoosting", self.gb_pipeline),
            ("RandomForest",     self.rf_pipeline),
        ]:
            pipe.fit(X_train, y_train)
            y_pred = pipe.predict(X_test)

            cv = cross_val_score(pipe, X_train, y_train, cv=5,
                                 scoring="accuracy", n_jobs=-1)
            metrics = {
                "accuracy":   float(accuracy_score(y_test, y_pred)),
                "cv_accuracy": float(cv.mean()),
                "cv_std":      float(cv.std()),
            }
            results[name] = metrics

            if verbose:
                print(f"\n── {name} ──────────────────────────────────────")
                print(f"  Accuracy : {metrics['accuracy']:.4f}")
                print(f"  CV Acc   : {metrics['cv_accuracy']:.4f} ± {metrics['cv_std']:.4f}")
                print(classification_report(y_test, y_pred,
                                            target_names=STAGE_NAMES,
                                            zero_division=0))

        # Feature importances
        rf_clf = self.rf_pipeline.named_steps["clf"]
        self.feature_importances_ = {
            col: float(imp)
            for col, imp in zip(FEATURE_COLS, rf_clf.feature_importances_)
        }
        if verbose:
            print("\n── Feature Importances (RandomForest) ──────────────────")
            for col, imp in sorted(self.feature_importances_.items(),
                                   key=lambda x: -x[1]):
                bar = "█" * int(imp * 40)
                print(f"  {col:<28} {imp:.4f}  {bar}")

        return results

    # ── Save / Load ───────────────────────────────────────────────────────────
    def save(self, path: str | None = None):
        path = path or os.path.join(MODELS_DIR, "growth_stage_predictor.pkl")
        with open(path, "wb") as f:
            pickle.dump({
                "gb_pipeline":         self.gb_pipeline,
                "rf_pipeline":         self.rf_pipeline,
                "feature_importances": self.feature_importances_,
                "feature_cols":        FEATURE_COLS,
                "stage_names":         STAGE_NAMES,
            }, f)
        print(f"  Saved GrowthStagePredictor → {path}")

    @classmethod
    def load(cls, path: str | None = None) -> "GrowthStagePredictor":
        path = path or os.path.join(MODELS_DIR, "growth_stage_predictor.pkl")
        with open(path, "rb") as f:
            data = pickle.load(f)
        obj = cls()
        obj.gb_pipeline          = data["gb_pipeline"]
        obj.rf_pipeline          = data["rf_pipeline"]
        obj.feature_importances_ = data.get("feature_importances", {})
        return obj

    # ── Inference ─────────────────────────────────────────────────────────────
    def predict(self, sensor_data: Dict[str, float]) -> Dict:
        """
        Predict crop growth stage from sensor reading dict.

        Returns:
            {
              "growth_stage_id":   int (0-4),
              "growth_stage_name": str,
              "model":             "GradientBoosting"
            }
        """
        if self.gb_pipeline is None:
            raise RuntimeError("Model not trained/loaded.")

        X = np.array([[sensor_data.get(c, 0.0) for c in FEATURE_COLS]])
        stage_id = int(self.gb_pipeline.predict(X)[0])
        return {
            "growth_stage_id":   stage_id,
            "growth_stage_name": STAGE_NAMES[stage_id] if stage_id < len(STAGE_NAMES) else "unknown",
            "model":             "GradientBoosting",
        }

    def predict_batch(self, X: np.ndarray) -> np.ndarray:
        return self.gb_pipeline.predict(X)
