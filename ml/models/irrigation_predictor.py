"""
Irrigation Predictor
====================
Binary classifier: does this farm parcel need irrigation right now?

Model: Random Forest  (also exposes a Logistic Regression baseline)
Input features: temperature, humidity, light_level, soil_moisture_pct,
                solar_radiation, hour_of_day, water_deficit_mm,
                moisture_fraction, evapotranspiration, accumulated_gdd,
                growth_progress_pct, day_of_season
"""

import os
import pickle
import numpy as np
from typing import Dict, Tuple, List

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    classification_report, confusion_matrix,
    roc_auc_score, accuracy_score,
)

FEATURE_COLS = [
    "temperature", "humidity", "light_level", "soil_moisture_pct",
    "solar_radiation", "hour_of_day",
    "water_deficit_mm", "moisture_fraction", "evapotranspiration",
    "accumulated_gdd", "growth_progress_pct", "day_of_season",
]

LABEL_COL = "irrigation_needed"

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "saved_models")
os.makedirs(MODELS_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
class IrrigationPredictor:
    """
    Trains and evaluates irrigation-need classifiers.
    Saves the best model (Random Forest) as a sklearn Pipeline.
    """

    def __init__(self):
        self.rf_pipeline: Pipeline | None = None
        self.gb_pipeline: Pipeline | None = None
        self.lr_pipeline: Pipeline | None = None
        self.feature_importances_: Dict[str, float] = {}

    # ── Build pipelines ───────────────────────────────────────────────────────
    def _build_pipelines(self):
        scaler = StandardScaler()

        self.rf_pipeline = Pipeline([
            ("scaler", scaler),
            ("clf", RandomForestClassifier(
                n_estimators=200,
                max_depth=12,
                min_samples_leaf=5,
                class_weight="balanced",
                random_state=42,
                n_jobs=-1,
            ))
        ])

        self.gb_pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", GradientBoostingClassifier(
                n_estimators=150,
                max_depth=5,
                learning_rate=0.1,
                subsample=0.8,
                random_state=42,
            ))
        ])

        self.lr_pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(
                C=1.0,
                max_iter=500,
                class_weight="balanced",
                random_state=42,
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
        """
        Train all classifiers and return evaluation metrics.

        Args:
            X: Feature matrix  (n_samples, n_features)
            y: Binary labels   (n_samples,)
            test_size: Fraction of data held out for evaluation
            verbose: Print detailed results

        Returns:
            Dict with metrics for each model
        """
        self._build_pipelines()

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )

        results = {}

        for name, pipe in [
            ("RandomForest",        self.rf_pipeline),
            ("GradientBoosting",    self.gb_pipeline),
            ("LogisticRegression",  self.lr_pipeline),
        ]:
            pipe.fit(X_train, y_train)
            y_pred = pipe.predict(X_test)
            y_prob = pipe.predict_proba(X_test)[:, 1]

            cv_scores = cross_val_score(pipe, X_train, y_train, cv=5,
                                        scoring="roc_auc", n_jobs=-1)
            metrics = {
                "accuracy":   float(accuracy_score(y_test, y_pred)),
                "roc_auc":    float(roc_auc_score(y_test, y_prob)),
                "cv_roc_auc": float(cv_scores.mean()),
                "cv_std":     float(cv_scores.std()),
            }
            results[name] = metrics

            if verbose:
                print(f"\n── {name} ──────────────────────────────────────")
                print(f"  Accuracy : {metrics['accuracy']:.4f}")
                print(f"  ROC-AUC  : {metrics['roc_auc']:.4f}")
                print(f"  CV AUC   : {metrics['cv_roc_auc']:.4f} ± {metrics['cv_std']:.4f}")
                print(classification_report(y_test, y_pred,
                                            target_names=["No Irrigation", "Irrigate"]))

        # Feature importances from Random Forest
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
        path = path or os.path.join(MODELS_DIR, "irrigation_predictor.pkl")
        with open(path, "wb") as f:
            pickle.dump({
                "rf_pipeline":          self.rf_pipeline,
                "gb_pipeline":          self.gb_pipeline,
                "lr_pipeline":          self.lr_pipeline,
                "feature_importances":  self.feature_importances_,
                "feature_cols":         FEATURE_COLS,
            }, f)
        print(f"  Saved IrrigationPredictor → {path}")

    @classmethod
    def load(cls, path: str | None = None) -> "IrrigationPredictor":
        path = path or os.path.join(MODELS_DIR, "irrigation_predictor.pkl")
        with open(path, "rb") as f:
            data = pickle.load(f)
        obj = cls()
        obj.rf_pipeline         = data["rf_pipeline"]
        obj.gb_pipeline         = data["gb_pipeline"]
        obj.lr_pipeline         = data["lr_pipeline"]
        obj.feature_importances_ = data.get("feature_importances", {})
        return obj

    # ── Inference ─────────────────────────────────────────────────────────────
    def predict(self, sensor_data: Dict[str, float]) -> Dict:
        """
        Predict irrigation need from a single sensor reading dict.

        Returns:
            {
              "irrigation_needed": bool,
              "confidence": float (0-1),
              "model": "RandomForest"
            }
        """
        if self.rf_pipeline is None:
            raise RuntimeError("Model not trained/loaded. Call train() or load() first.")

        X = np.array([[sensor_data.get(c, 0.0) for c in FEATURE_COLS]])
        pred  = int(self.rf_pipeline.predict(X)[0])
        prob  = float(self.rf_pipeline.predict_proba(X)[0, 1])

        return {
            "irrigation_needed": bool(pred),
            "confidence":        round(prob, 4),
            "model":             "RandomForest",
        }

    def predict_batch(self, X: np.ndarray) -> np.ndarray:
        """Return binary predictions for a feature matrix."""
        return self.rf_pipeline.predict(X)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Return class probabilities for a feature matrix."""
        return self.rf_pipeline.predict_proba(X)
