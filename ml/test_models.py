"""
AgriTwin – ML Model Evaluation & Test Suite
=============================================
Loads saved models and runs:
  1. Held-out test-set evaluation for each model (metrics + confusion matrices)
  2. Live inference demo with synthetic sensor readings
  3. Edge-case / sanity checks
  4. Outputs a full test report to  ml/saved_models/test_report.json

Usage:
  python -m ml.test_models
"""

import os
import sys
import csv
import json
import time
from datetime import datetime
from typing import Dict, List, Tuple

import numpy as np

# ── project root on path ──────────────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from ml.data_generator import FEATURE_COLUMNS, DATA_DIR
from ml.models.irrigation_predictor    import IrrigationPredictor,    FEATURE_COLS as IRR_COLS
from ml.models.growth_stage_predictor  import GrowthStagePredictor,   FEATURE_COLS as GS_COLS
from ml.models.water_deficit_regressor import WaterDeficitRegressor,  FEATURE_COLS as WD_COLS
from ml.models.anomaly_detector        import AnomalyDetector,        FEATURE_COLS as AD_COLS

from sklearn.metrics import (
    classification_report, confusion_matrix,
    accuracy_score, roc_auc_score, f1_score,
    mean_absolute_error, r2_score,
)
from sklearn.model_selection import train_test_split

MODELS_DIR = os.path.join(os.path.dirname(__file__), "saved_models")


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def _load_csv(path: str, feature_cols: List[str], label_col: str,
              label_type=int) -> Tuple[np.ndarray, np.ndarray]:
    X_rows, y_rows = [], []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                x = [float(row[c]) for c in feature_cols]
                y = label_type(float(row[label_col]))
            except (KeyError, ValueError):
                continue
            X_rows.append(x)
            y_rows.append(y)
    return np.array(X_rows, np.float32), np.array(y_rows, np.float32)


def _load_anomaly_csv(path, feature_cols):
    X_all, y_all = [], []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                x = [float(row[c]) for c in feature_cols]
                y = int(float(row["is_anomaly"]))
            except (KeyError, ValueError):
                continue
            X_all.append(x)
            y_all.append(y)
    X = np.array(X_all, np.float32)
    y = np.array(y_all, np.int32)
    return X, y


def _sep(title: str = ""):
    line = "─" * 65
    print(f"\n{line}")
    if title:
        print(f"  {title}")
        print(line)


# ──────────────────────────────────────────────────────────────────────────────
# Test: Irrigation Predictor
# ──────────────────────────────────────────────────────────────────────────────
def test_irrigation_predictor(report: Dict) -> bool:
    _sep("TEST 1 – Irrigation Predictor")

    model = IrrigationPredictor.load()
    csv_path = os.path.join(DATA_DIR, "irrigation_labels.csv")
    X, y = _load_csv(csv_path, IRR_COLS, "irrigation_needed", int)

    # Use a fixed held-out split (different from training split)
    _, X_test, _, y_test = train_test_split(X, y, test_size=0.15,
                                             random_state=99, stratify=y.astype(int))

    y_pred = model.predict_batch(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_prob)
    f1  = f1_score(y_test, y_pred)

    print(f"  Samples evaluated : {len(y_test):,}")
    print(f"  Accuracy           : {acc:.4f}")
    print(f"  ROC-AUC            : {auc:.4f}")
    print(f"  F1-Score           : {f1:.4f}")
    print("\n" + classification_report(y_test, y_pred,
                                       target_names=["No Irrigation", "Irrigate"],
                                       zero_division=0))
    cm = confusion_matrix(y_test, y_pred)
    print(f"  Confusion Matrix:\n  {cm}")

    # Single-sample inference demo
    sample = {c: float(X_test[0, i]) for i, c in enumerate(IRR_COLS)}
    result = model.predict(sample)
    print(f"\n  Single-sample inference: {result}")

    passed = acc >= 0.80 and auc >= 0.80
    status = "✓ PASS" if passed else "✗ FAIL (below threshold)"
    print(f"\n  Status: {status}  (threshold: acc≥0.80, auc≥0.80)")

    report["irrigation"] = {
        "accuracy": round(acc, 4), "roc_auc": round(auc, 4),
        "f1": round(f1, 4), "passed": passed,
        "n_test_samples": int(len(y_test)),
    }
    return passed


# ──────────────────────────────────────────────────────────────────────────────
# Test: Growth Stage Predictor
# ──────────────────────────────────────────────────────────────────────────────
def test_growth_stage_predictor(report: Dict) -> bool:
    _sep("TEST 2 – Growth Stage Predictor")

    model = GrowthStagePredictor.load()
    csv_path = os.path.join(DATA_DIR, "growth_stage_labels.csv")
    X, y = _load_csv(csv_path, GS_COLS, "growth_stage", int)

    _, X_test, _, y_test = train_test_split(X, y, test_size=0.15,
                                             random_state=99, stratify=y.astype(int))

    y_pred = model.predict_batch(X_test)

    stage_names = ["vegetative", "flowering", "fruiting", "ripening", "mature"]
    acc = accuracy_score(y_test, y_pred)
    f1  = f1_score(y_test, y_pred, average="weighted", zero_division=0)

    print(f"  Samples evaluated : {len(y_test):,}")
    print(f"  Accuracy           : {acc:.4f}")
    print(f"  Weighted F1        : {f1:.4f}")
    print("\n" + classification_report(y_test, y_pred,
                                       target_names=stage_names,
                                       zero_division=0))
    cm = confusion_matrix(y_test, y_pred)
    print(f"  Confusion Matrix:\n  {cm}")

    # Single-sample inference demo
    sample = {c: float(X_test[0, i]) for i, c in enumerate(GS_COLS)}
    result = model.predict(sample)
    print(f"\n  Single-sample inference: {result}")

    passed = acc >= 0.75
    status = "✓ PASS" if passed else "✗ FAIL (below threshold)"
    print(f"\n  Status: {status}  (threshold: acc≥0.75)")

    report["growth_stage"] = {
        "accuracy": round(acc, 4), "f1_weighted": round(f1, 4),
        "passed": passed, "n_test_samples": int(len(y_test)),
    }
    return passed


# ──────────────────────────────────────────────────────────────────────────────
# Test: Water Deficit Regressor
# ──────────────────────────────────────────────────────────────────────────────
def test_water_deficit_regressor(report: Dict) -> bool:
    _sep("TEST 3 – Water Deficit Regressor")

    model = WaterDeficitRegressor.load()
    csv_path = os.path.join(DATA_DIR, "sensor_dataset.csv")
    X, y = _load_csv(csv_path, WD_COLS, "water_deficit_mm", float)

    _, X_test, _, y_test = train_test_split(X, y, test_size=0.15, random_state=99)

    y_pred = model.predict_batch(X_test)

    mae  = mean_absolute_error(y_test, y_pred)
    r2   = r2_score(y_test, y_pred)
    rmse = float(np.sqrt(np.mean((y_test - y_pred) ** 2)))

    print(f"  Samples evaluated  : {len(y_test):,}")
    print(f"  MAE                : {mae:.4f} mm")
    print(f"  RMSE               : {rmse:.4f} mm")
    print(f"  R²                 : {r2:.4f}")

    # Predictions vs actuals (5 samples)
    print("\n  Sample predictions (first 5):")
    print(f"  {'Actual':>10}  {'Predicted':>10}  {'Error':>10}")
    for a, p in zip(y_test[:5], y_pred[:5]):
        print(f"  {a:10.3f}  {p:10.3f}  {abs(a-p):10.3f}")

    # Single-sample inference demo
    sample = {c: float(X_test[0, i]) for i, c in enumerate(WD_COLS)}
    result = model.predict(sample)
    print(f"\n  Single-sample inference: {result}")

    passed = r2 >= 0.75 and mae <= 5.0
    status = "✓ PASS" if passed else "✗ FAIL (below threshold)"
    print(f"\n  Status: {status}  (threshold: R²≥0.75, MAE≤5.0 mm)")

    report["water_deficit"] = {
        "mae": round(mae, 4), "rmse": round(rmse, 4), "r2": round(r2, 4),
        "passed": passed, "n_test_samples": int(len(y_test)),
    }
    return passed


# ──────────────────────────────────────────────────────────────────────────────
# Test: Anomaly Detector
# ──────────────────────────────────────────────────────────────────────────────
def test_anomaly_detector(report: Dict) -> bool:
    _sep("TEST 4 – Anomaly Detector")

    model = AnomalyDetector.load()
    csv_path = os.path.join(DATA_DIR, "anomaly_samples.csv")
    X_full, y_full = _load_anomaly_csv(csv_path, AD_COLS)

    y_pred = model.predict_batch(X_full)
    neg_scores = -model.pipeline.decision_function(X_full)

    f1  = f1_score(y_full, y_pred, zero_division=0)
    auc = roc_auc_score(y_full, neg_scores)

    print(f"  Samples evaluated  : {len(y_full):,}")
    print(f"  Anomalies (actual) : {y_full.sum():,}")
    print(f"  F1-Score           : {f1:.4f}")
    print(f"  ROC-AUC            : {auc:.4f}")
    print("\n" + classification_report(y_full, y_pred,
                                       target_names=["Clean", "Anomaly"],
                                       zero_division=0))

    # Sanity checks
    # Normal reading → should be clean
    normal_sensor = {
        "temperature": 24.0, "humidity": 65.0, "light_level": 50.0,
        "soil_moisture_pct": 50.0, "solar_radiation": 15.0, "hour_of_day": 12.0,
        "water_deficit_mm": 2.0, "moisture_fraction": 0.30,
        "evapotranspiration": 3.0, "accumulated_gdd": 400.0,
        "growth_progress_pct": 30.0, "day_of_season": 30,
    }
    r_normal = model.predict(normal_sensor)
    print(f"\n  Normal sensor:   is_anomaly={r_normal['is_anomaly']}  "
          f"score={r_normal['anomaly_score']}")

    # Spike → should be anomaly
    spike_sensor = dict(normal_sensor, temperature=999.0)
    r_spike = model.predict(spike_sensor)
    print(f"  Spike (temp=999): is_anomaly={r_spike['is_anomaly']}  "
          f"score={r_spike['anomaly_score']}")

    passed = f1 >= 0.20 and auc >= 0.70
    status = "✓ PASS" if passed else "✗ FAIL (below threshold)"
    print(f"\n  Status: {status}  (threshold: F1≥0.20, AUC≥0.70)")

    report["anomaly"] = {
        "f1": round(f1, 4), "roc_auc": round(auc, 4),
        "passed": passed, "n_test_samples": int(len(y_full)),
    }
    return passed


# ──────────────────────────────────────────────────────────────────────────────
# Live inference demo — simulate one hour of sensor readings
# ──────────────────────────────────────────────────────────────────────────────
def run_live_inference_demo():
    _sep("LIVE INFERENCE DEMO – 3 synthetic sensor snapshots")

    irr_model  = IrrigationPredictor.load()
    gs_model   = GrowthStagePredictor.load()
    wd_model   = WaterDeficitRegressor.load()
    anom_model = AnomalyDetector.load()

    snapshots = [
        {   # Dry daytime conditions → irrigation likely needed
            "label": "Dry midday (soil=28%, temp=33°C)",
            "temperature": 33.0, "humidity": 45.0, "light_level": 90.0,
            "soil_moisture_pct": 28.0, "solar_radiation": 22.0, "hour_of_day": 13.0,
            "water_deficit_mm": 18.0, "moisture_fraction": 0.18,
            "evapotranspiration": 5.5, "accumulated_gdd": 600.0,
            "growth_progress_pct": 50.0, "day_of_season": 50,
        },
        {   # Well-watered night → no irrigation
            "label": "Moist night (soil=62%, temp=19°C)",
            "temperature": 19.0, "humidity": 82.0, "light_level": 2.0,
            "soil_moisture_pct": 62.0, "solar_radiation": 0.5,  "hour_of_day": 2.0,
            "water_deficit_mm": 0.0, "moisture_fraction": 0.38,
            "evapotranspiration": 0.3, "accumulated_gdd": 300.0,
            "growth_progress_pct": 20.0, "day_of_season": 20,
        },
        {   # Sensor anomaly: negative humidity
            "label": "Anomalous reading (humidity=-50)",
            "temperature": 25.0, "humidity": -50.0, "light_level": 50.0,
            "soil_moisture_pct": 45.0, "solar_radiation": 15.0, "hour_of_day": 9.0,
            "water_deficit_mm": 3.0, "moisture_fraction": 0.28,
            "evapotranspiration": 3.0, "accumulated_gdd": 500.0,
            "growth_progress_pct": 40.0, "day_of_season": 40,
        },
    ]

    for snap in snapshots:
        label = snap.pop("label")
        print(f"\n  ▶  {label}")

        irr  = irr_model.predict(snap)
        gs   = gs_model.predict(snap)
        wd   = wd_model.predict(snap)
        anom = anom_model.predict(snap)

        print(f"     Irrigation needed : {irr['irrigation_needed']}  "
              f"(confidence {irr['confidence']:.2f})")
        print(f"     Growth stage      : {gs['growth_stage_name']} (id={gs['growth_stage_id']})")
        print(f"     Water deficit     : {wd['water_deficit_mm']:.2f} mm")
        print(f"     Anomaly detected  : {anom['is_anomaly']}  "
              f"(score {anom['anomaly_score']:.4f})")

        snap["label"] = label   # restore for safety


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────
def run_tests():
    t0 = time.time()

    print("=" * 65)
    print("  AgriTwin – ML Model Test Suite")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    report: Dict = {}

    p1 = test_irrigation_predictor(report)
    p2 = test_growth_stage_predictor(report)
    p3 = test_water_deficit_regressor(report)
    p4 = test_anomaly_detector(report)

    run_live_inference_demo()

    # ── final summary ─────────────────────────────────────────────────────────
    all_passed = all([p1, p2, p3, p4])
    elapsed = round(time.time() - t0, 1)

    print("\n" + "=" * 65)
    print("  TEST SUMMARY")
    print("=" * 65)
    rows_summary = [
        ("IrrigationPredictor",    p1),
        ("GrowthStagePredictor",   p2),
        ("WaterDeficitRegressor",  p3),
        ("AnomalyDetector",        p4),
    ]
    for name, passed in rows_summary:
        icon = "✓" if passed else "✗"
        print(f"  {icon}  {name}")

    print(f"\n  Overall : {'ALL PASSED ✓' if all_passed else 'SOME TESTS FAILED ✗'}")
    print(f"  Time    : {elapsed} s")

    # Persist report
    report["overall_passed"] = all_passed
    report["elapsed_sec"]    = elapsed
    report["tested_at"]      = datetime.now().isoformat()

    report_path = os.path.join(MODELS_DIR, "test_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Report saved → {report_path}")
    print("=" * 65)

    return all_passed


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
