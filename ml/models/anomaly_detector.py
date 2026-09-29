"""
Sensor Anomaly Detector
========================
Unsupervised anomaly detection for ESP32 sensor streams.
Uses Isolation Forest as the primary model.
Also includes a simple statistical Z-score detector for comparison.

Input features: temperature, humidity, light_level, soil_moisture_pct
                (+ optional physics features)
"""

import os
import pickle
import numpy as np
from typing import Dict, List, Tuple

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    classification_report, roc_auc_score, f1_score,
    precision_score, recall_score,
)

FEATURE_COLS = [
    # Only raw sensor features — anomalies manifest here, not in physics columns
    "temperature", "humidity", "light_level", "soil_moisture_pct",
    "solar_radiation", "hour_of_day",
]

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "saved_models")
os.makedirs(MODELS_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
class AnomalyDetector:
    """
    Isolation Forest anomaly detector for sensor data.
    Trained on *clean* data; any sample with high anomaly score gets flagged.
    """

    def __init__(self, contamination: float = 0.05):
        """
        contamination: expected fraction of anomalies in the training set.
                       Set equal to the anomaly_fraction used in data generation.
        """
        self.contamination = contamination
        self.pipeline: Pipeline | None = None
        self.threshold_: float = 0.0      # decision threshold on raw score

    # ── Build ─────────────────────────────────────────────────────────────────
    def _build(self):
        self.pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("clf", IsolationForest(
                n_estimators=200,
                max_samples="auto",
                contamination=self.contamination,
                max_features=1.0,
                bootstrap=False,
                n_jobs=-1,
                random_state=42,
            ))
        ])

    # ── Train ─────────────────────────────────────────────────────────────────
    def train(
        self,
        X_clean: np.ndarray,
        X_full: np.ndarray,
        y_full: np.ndarray,
        verbose: bool = True,
    ) -> Dict:
        """
        Train on clean data, then tune a decision threshold on the full
        labelled dataset to maximise F1.

        Args:
            X_clean: Feature matrix of clean rows only  (for training)
            X_full:  All rows  (for evaluation + threshold tuning)
            y_full:  Ground-truth anomaly labels (0=clean, 1=anomaly)

        Returns:
            Metrics dict
        """
        self._build()

        # IsolationForest is unsupervised → fit on clean only
        self.pipeline.fit(X_clean)

        # decision_function: lower (more negative) = more anomalous.
        # Negate so that higher score = more anomalous.
        scores = -self.pipeline.decision_function(X_full)

        # ── tune threshold to maximise F1 ────────────────────────────────────
        from sklearn.metrics import f1_score as _f1
        best_f1, best_thresh = 0.0, 0.0
        for pct in np.arange(80, 100, 0.5):            # search top percentiles
            thresh = float(np.percentile(scores, pct))
            y_pred_t = (scores >= thresh).astype(int)
            f = _f1(y_full, y_pred_t, zero_division=0)
            if f > best_f1:
                best_f1    = f
                best_thresh = thresh

        self.threshold_ = best_thresh
        y_pred_binary = (scores >= best_thresh).astype(int)

        metrics = {
            "precision":  float(precision_score(y_full, y_pred_binary, zero_division=0)),
            "recall":     float(recall_score(y_full, y_pred_binary, zero_division=0)),
            "f1":         float(f1_score(y_full, y_pred_binary, zero_division=0)),
            "roc_auc":    float(roc_auc_score(y_full, scores)),
            "threshold":  float(best_thresh),
        }

        if verbose:
            print("\n── Anomaly Detector (IsolationForest + tuned threshold) ─")
            print(f"  Threshold : {best_thresh:.6f}  (tuned for max-F1)")
            print(f"  Precision : {metrics['precision']:.4f}")
            print(f"  Recall    : {metrics['recall']:.4f}")
            print(f"  F1        : {metrics['f1']:.4f}")
            print(f"  ROC-AUC   : {metrics['roc_auc']:.4f}")
            print(classification_report(y_full, y_pred_binary,
                                        target_names=["Clean", "Anomaly"],
                                        zero_division=0))

        return metrics

    # ── Save / Load ───────────────────────────────────────────────────────────
    def save(self, path: str | None = None):
        path = path or os.path.join(MODELS_DIR, "anomaly_detector.pkl")
        with open(path, "wb") as f:
            pickle.dump({
                "pipeline":      self.pipeline,
                "contamination": self.contamination,
                "threshold":     self.threshold_,
                "feature_cols":  FEATURE_COLS,
            }, f)
        print(f"  Saved AnomalyDetector → {path}")

    @classmethod
    def load(cls, path: str | None = None) -> "AnomalyDetector":
        path = path or os.path.join(MODELS_DIR, "anomaly_detector.pkl")
        with open(path, "rb") as f:
            data = pickle.load(f)
        obj = cls(contamination=data.get("contamination", 0.05))
        obj.pipeline   = data["pipeline"]
        obj.threshold_ = data.get("threshold", 0.0)
        return obj

    # ── Inference ─────────────────────────────────────────────────────────────
    def predict(self, sensor_data: Dict[str, float]) -> Dict:
        """
        Detect anomaly in a single sensor reading using the tuned threshold.

        Returns:
            {
              "is_anomaly":   bool,
              "anomaly_score": float  (higher = more anomalous),
              "model":        "IsolationForest"
            }
        """
        if self.pipeline is None:
            raise RuntimeError("Model not trained/loaded.")

        X = np.array([[sensor_data.get(c, 0.0) for c in FEATURE_COLS]])
        score = float(-self.pipeline.decision_function(X)[0])   # higher = worse
        is_anomaly = score >= self.threshold_

        return {
            "is_anomaly":    bool(is_anomaly),
            "anomaly_score": round(score, 5),
            "model":         "IsolationForest",
        }

    def predict_batch(self, X: np.ndarray) -> np.ndarray:
        """Return binary anomaly labels (0=clean, 1=anomaly) using tuned threshold."""
        scores = -self.pipeline.decision_function(X)
        return (scores >= self.threshold_).astype(int)


# ─────────────────────────────────────────────────────────────────────────────
class ZScoreAnomalyDetector:
    """
    Simple statistical baseline: flag values > z_thresh standard deviations
    from the column mean (computed from clean training data).
    """

    def __init__(self, z_thresh: float = 3.5):
        self.z_thresh = z_thresh
        self._mean: np.ndarray | None  = None
        self._std:  np.ndarray | None  = None
        self.feature_cols: List[str]   = FEATURE_COLS       # raw sensor cols

    def fit(self, X_clean: np.ndarray):
        self._mean = np.mean(X_clean, axis=0)
        self._std  = np.std(X_clean, axis=0) + 1e-9   # avoid division by zero

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Return 1 for anomaly, 0 for clean."""
        z = np.abs((X - self._mean) / self._std)
        return (z.max(axis=1) > self.z_thresh).astype(int)
