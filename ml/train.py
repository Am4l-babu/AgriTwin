"""
AgriTwin – ML Training Pipeline
================================
Runs end-to-end:
  1. Generate (or reload) labelled datasets
  2. Train IrrigationPredictor    (Random Forest / Gradient Boosting / LR)
  3. Train GrowthStagePredictor   (Gradient Boosting / Random Forest)
  4. Train WaterDeficitRegressor  (Gradient Boosting / RF / Ridge)
  5. Train AnomalyDetector        (Isolation Forest)
  6. Save all models to  ml/saved_models/
  7. Persist training metrics to  ml/saved_models/training_results.json

Usage:
  python -m ml.train                       # full pipeline (generate + train)
  python -m ml.train --skip-datagen        # reuse existing CSVs
"""

import os
import sys
import csv
import json
import argparse
import time
from datetime import datetime
from typing import Dict, List, Tuple

import numpy as np

# ── project root on path ──────────────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ml.data_generator import (
    generate_dataset, save_datasets,
    FEATURE_COLUMNS, LABEL_IRRIGATION, LABEL_GROWTH_STAGE,
    DATA_DIR,
)
from ml.models.irrigation_predictor   import IrrigationPredictor,   FEATURE_COLS as IRR_COLS
from ml.models.growth_stage_predictor import GrowthStagePredictor,  FEATURE_COLS as GS_COLS
from ml.models.water_deficit_regressor import WaterDeficitRegressor, FEATURE_COLS as WD_COLS
from ml.models.anomaly_detector       import AnomalyDetector,       FEATURE_COLS as AD_COLS

MODELS_DIR   = os.path.join(os.path.dirname(__file__), "saved_models")
os.makedirs(MODELS_DIR, exist_ok=True)


# ──────────────────────────────────────────────────────────────────────────────
# CSV loader
# ──────────────────────────────────────────────────────────────────────────────
def _load_csv(path: str, feature_cols: List[str], label_col: str | None = None,
              label_type=int) -> Tuple[np.ndarray, np.ndarray | None]:
    X_rows, y_rows = [], []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                x = [float(row[c]) for c in feature_cols]
            except (KeyError, ValueError):
                continue
            X_rows.append(x)
            if label_col:
                y_rows.append(label_type(float(row[label_col])))

    X = np.array(X_rows, dtype=np.float32)
    y = np.array(y_rows, dtype=np.float32) if y_rows else None
    return X, y


def _load_anomaly_csv(path: str, feature_cols: List[str]):
    """Load anomaly dataset; return X_clean, X_full, y_full."""
    X_all, y_all = [], []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                x = [float(row[c]) for c in feature_cols]
                label = int(float(row["is_anomaly"]))
            except (KeyError, ValueError):
                continue
            X_all.append(x)
            y_all.append(label)

    X_full = np.array(X_all, dtype=np.float32)
    y_full = np.array(y_all, dtype=np.int32)
    X_clean = X_full[y_full == 0]           # IsolationForest trains on clean only
    return X_clean, X_full, y_full


# ──────────────────────────────────────────────────────────────────────────────
# Individual training helpers
# ──────────────────────────────────────────────────────────────────────────────
def train_irrigation(verbose: bool = True) -> Dict:
    print("\n" + "═" * 65)
    print("  [1/4] Training: Irrigation Predictor")
    print("═" * 65)

    csv_path = os.path.join(DATA_DIR, "irrigation_labels.csv")
    X, y = _load_csv(csv_path, IRR_COLS, LABEL_IRRIGATION, int)
    print(f"  Dataset: {X.shape[0]:,} rows × {X.shape[1]} features")
    print(f"  Class balance  →  No Irrigation: {(y==0).sum():,}  |  Irrigate: {(y==1).sum():,}")

    model = IrrigationPredictor()
    metrics = model.train(X, y, verbose=verbose)
    model.save()
    return metrics


def train_growth_stage(verbose: bool = True) -> Dict:
    print("\n" + "═" * 65)
    print("  [2/4] Training: Growth Stage Predictor")
    print("═" * 65)

    csv_path = os.path.join(DATA_DIR, "growth_stage_labels.csv")
    X, y = _load_csv(csv_path, GS_COLS, LABEL_GROWTH_STAGE, int)
    print(f"  Dataset: {X.shape[0]:,} rows × {X.shape[1]} features")
    stage_names = ["vegetative", "flowering", "fruiting", "ripening", "mature"]
    for i, n in enumerate(stage_names):
        print(f"  Stage {i} ({n:12s}) : {(y==i).sum():,}")

    model = GrowthStagePredictor()
    metrics = model.train(X, y, verbose=verbose)
    model.save()
    return metrics


def train_water_deficit(verbose: bool = True) -> Dict:
    print("\n" + "═" * 65)
    print("  [3/4] Training: Water Deficit Regressor")
    print("═" * 65)

    csv_path = os.path.join(DATA_DIR, "sensor_dataset.csv")
    X, y = _load_csv(csv_path, WD_COLS, "water_deficit_mm", float)
    print(f"  Dataset: {X.shape[0]:,} rows × {X.shape[1]} features")
    print(f"  Target range: [{y.min():.2f} – {y.max():.2f}] mm  |  mean: {y.mean():.2f} mm")

    model = WaterDeficitRegressor()
    metrics = model.train(X, y, verbose=verbose)
    model.save()
    return metrics


def train_anomaly_detector(verbose: bool = True) -> Dict:
    print("\n" + "═" * 65)
    print("  [4/4] Training: Anomaly Detector")
    print("═" * 65)

    csv_path = os.path.join(DATA_DIR, "anomaly_samples.csv")
    X_clean, X_full, y_full = _load_anomaly_csv(csv_path, AD_COLS)
    print(f"  Full dataset : {X_full.shape[0]:,} rows")
    print(f"  Clean rows   : {X_clean.shape[0]:,}  |  Anomaly rows: {(y_full==1).sum():,}")

    model = AnomalyDetector(contamination=0.05)
    metrics = model.train(X_clean, X_full, y_full, verbose=verbose)
    model.save()
    return metrics


# ──────────────────────────────────────────────────────────────────────────────
# Main pipeline
# ──────────────────────────────────────────────────────────────────────────────
def run_training_pipeline(skip_datagen: bool = False, verbose: bool = True):
    t_start = time.time()

    print("=" * 65)
    print("  AgriTwin – Complete ML Training Pipeline")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    # ── step 0: data generation ───────────────────────────────────────────────
    if not skip_datagen:
        print("\n[0/4] Generating labelled datasets …")
        rows = generate_dataset()
        save_datasets(rows)
    else:
        print("\n[0/4] Skipping data generation (--skip-datagen flag set).")
        sensor_csv = os.path.join(DATA_DIR, "sensor_dataset.csv")
        if not os.path.exists(sensor_csv):
            raise FileNotFoundError(
                "Dataset CSVs not found. Run without --skip-datagen first."
            )
        print(f"  Reusing existing datasets in: {DATA_DIR}")

    all_results = {}
    all_results["irrigation"]    = train_irrigation(verbose)
    all_results["growth_stage"]  = train_growth_stage(verbose)
    all_results["water_deficit"] = train_water_deficit(verbose)
    all_results["anomaly"]       = train_anomaly_detector(verbose)

    # ── save metrics ──────────────────────────────────────────────────────────
    elapsed = round(time.time() - t_start, 1)
    summary = {
        "trained_at":  datetime.now().isoformat(),
        "elapsed_sec": elapsed,
        "models":      all_results,
    }
    metrics_path = os.path.join(MODELS_DIR, "training_results.json")
    with open(metrics_path, "w") as f:
        json.dump(summary, f, indent=2)

    # ── print summary table ───────────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("  TRAINING COMPLETE")
    print("=" * 65)
    print(f"  Total time: {elapsed} s")
    print(f"\n  Best metrics per model:")

    irr_rf = all_results["irrigation"].get("RandomForest", {})
    gs_gb  = all_results["growth_stage"].get("GradientBoosting", {})
    wd_gb  = all_results["water_deficit"].get("GradientBoosting", {})
    anom   = all_results["anomaly"]

    print(f"  IrrigationPredictor    ROC-AUC = {irr_rf.get('roc_auc', 0):.4f}"
          f"   Acc = {irr_rf.get('accuracy', 0):.4f}")
    print(f"  GrowthStagePredictor   Acc     = {gs_gb.get('accuracy', 0):.4f}"
          f"   CV  = {gs_gb.get('cv_accuracy', 0):.4f}")
    print(f"  WaterDeficitRegressor  R²      = {wd_gb.get('r2', 0):.4f}"
          f"   MAE = {wd_gb.get('mae', 0):.4f} mm")
    print(f"  AnomalyDetector        F1      = {anom.get('f1', 0):.4f}"
          f"   AUC = {anom.get('roc_auc', 0):.4f}")

    print(f"\n  Saved models  → {MODELS_DIR}")
    print(f"  Saved metrics → {metrics_path}")
    print("=" * 65)

    return summary


# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AgriTwin ML Training Pipeline")
    parser.add_argument("--skip-datagen", action="store_true",
                        help="Skip dataset generation and use existing CSV files")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress per-model verbose output")
    args = parser.parse_args()

    run_training_pipeline(
        skip_datagen=args.skip_datagen,
        verbose=not args.quiet,
    )
