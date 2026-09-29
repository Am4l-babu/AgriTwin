"""
AgriTwin – ML Training Data Generator
======================================
Generates realistic, labelled datasets by driving the DigitalTwinPhysics
engine through thousands of simulated time-steps.  The generated CSV files
are later consumed by the training scripts.

Output files (written to  ml/data/):
  sensor_dataset.csv      – all simulation steps, raw + physics columns
  irrigation_labels.csv   – binary classification (irrigation needed)
  growth_stage_labels.csv – 5-class growth-stage classification
  anomaly_samples.csv     – clean + injected anomaly rows for anomaly model
"""

import os
import sys
import math
import random
import csv
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

# ── make sure the project root is on the Python path ──────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from cloud.digital_twin.physics_model.comprehensive_physics import (
    DigitalTwinPhysics,
    SoilProperties,
    WeatherData,
)

# ── output directory ───────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ── constants ──────────────────────────────────────────────────────────────────
RANDOM_SEED = 42
NUM_SCENARIOS = 80          # independent farm scenarios
DAYS_PER_SCENARIO = 90      # growing season length (days)
STEPS_PER_DAY = 4           # sensor readings per simulated day (6 h each)

GROWTH_STAGE_MAP = {
    "vegetative": 0,
    "flowering":  1,
    "fruiting":   2,
    "ripening":   3,
    "mature":     4,
}

FEATURE_COLUMNS = [
    "temperature", "humidity", "light_level", "soil_moisture_pct",
    "solar_radiation", "hour_of_day",
    "water_deficit_mm", "moisture_fraction", "evapotranspiration",
    "accumulated_gdd", "growth_progress_pct",
    "day_of_season", "scenario_id",
]

LABEL_IRRIGATION   = "irrigation_needed"      # 0/1
LABEL_GROWTH_STAGE = "growth_stage"           # 0-4
LABEL_WATER_DEFICIT = "water_deficit_mm"      # continuous


# ──────────────────────────────────────────────────────────────────────────────
# Helper: realistic sensor noise
# ──────────────────────────────────────────────────────────────────────────────
def _add_noise(value: float, sigma_frac: float = 0.02) -> float:
    """Add Gaussian noise (sigma = sigma_frac * |value|)."""
    sigma = abs(value) * sigma_frac
    return value + random.gauss(0, sigma)


# ──────────────────────────────────────────────────────────────────────────────
# Helper: synthetic weather for one step
# ──────────────────────────────────────────────────────────────────────────────
def _make_weather(
    day: int,
    step: int,
    base_temp: float = 22.0,
    climate_variability: float = 1.0,
) -> Tuple[Dict[str, float], float]:
    """
    Generate synthetic sensor readings for a single simulation step.

    Returns:
        (sensor_dict, hour_of_day)
    """
    hour_of_day = (step / STEPS_PER_DAY) * 24.0        # 0 → 24
    day_of_year  = (day % 365) + 1

    # ── temperature (seasonal + diurnal) ─────────────────────────────────────
    seasonal_amp = 8.0 * climate_variability
    seasonal     = seasonal_amp * math.sin(2 * math.pi * (day_of_year - 80) / 365)
    diurnal      = 6.0 * math.sin((hour_of_day - 6) * math.pi / 12)
    temperature  = base_temp + seasonal + diurnal + random.gauss(0, 1.0)
    temperature  = max(5.0, min(45.0, temperature))

    # ── humidity (inverse of temperature + random) ────────────────────────────
    humidity = 80.0 - 0.8 * (temperature - base_temp) + random.gauss(0, 5.0)
    humidity = max(20.0, min(98.0, humidity))

    # ── light: only during daylight (06:00-18:00) ─────────────────────────────
    if 6.0 <= hour_of_day <= 18.0:
        noon_fraction = 1 - abs(hour_of_day - 12) / 6
        light_level   = 100.0 * noon_fraction + random.gauss(0, 5)
    else:
        light_level   = random.uniform(0, 3)
    light_level = max(0.0, min(100.0, light_level))

    # ── precipitation (random showers, ~15 % chance per day) ─────────────────
    rain = 0.0
    if step == 0 and random.random() < 0.15:
        rain = random.uniform(2.0, 20.0)

    sensor = {
        "temp":       temperature,
        "humidity":   humidity,
        "light":      light_level * 7,   # rough lux equivalent (0-700)
        "rain":       rain,
        "wind_speed": max(0, random.gauss(2.5, 1.0)),
    }
    return sensor, hour_of_day


# ──────────────────────────────────────────────────────────────────────────────
# Core simulation loop
# ──────────────────────────────────────────────────────────────────────────────
def generate_dataset(
    num_scenarios: int = NUM_SCENARIOS,
    days_per_scenario: int = DAYS_PER_SCENARIO,
    steps_per_day: int = STEPS_PER_DAY,
    seed: int = RANDOM_SEED,
) -> List[Dict]:
    """
    Run the digital-twin simulation and collect labelled rows.

    Returns:
        List of dicts, one per simulation step.
    """
    random.seed(seed)
    rows: List[Dict] = []

    for scenario_id in range(num_scenarios):
        # Randomise farm conditions per scenario
        base_temp  = random.uniform(18.0, 30.0)
        init_moist = random.uniform(0.20, 0.42)   # volumetric fraction
        rooting_d  = random.uniform(0.20, 0.45)
        crop_types = [
            ("Tomato",   10.0, 30.0, 1500.0),
            ("Wheat",     5.0, 25.0,  900.0),
            ("Maize",    10.0, 32.0, 1200.0),
            ("Lettuce",   7.0, 22.0,  600.0),
        ]
        crop_name, base_t, max_t, gdd_mat = random.choice(crop_types)

        soil = SoilProperties(
            field_capacity=random.uniform(0.28, 0.42),
            wilting_point=random.uniform(0.10, 0.18),
            saturation=random.uniform(0.42, 0.52),
            rooting_depth=rooting_d,
        )
        twin = DigitalTwinPhysics(soil_properties=soil)
        twin.water_balance.current_moisture = init_moist
        twin.crop_growth.base_temp       = base_t
        twin.crop_growth.max_temp        = max_t
        twin.crop_growth.gdd_to_maturity = gdd_mat

        for day in range(days_per_scenario):
            # Decide irrigation for this day (rule-based ground-truth)
            irrigate_today = twin.water_balance.is_irrigation_needed(threshold=0.55)
            daily_irrigation = random.uniform(8.0, 15.0) if irrigate_today else 0.0

            for step in range(steps_per_day):
                sensor, hour = _make_weather(
                    day, step, base_temp=base_temp,
                    climate_variability=random.uniform(0.7, 1.3),
                )

                # Apply irrigation only in first step of the day
                irrig = daily_irrigation if step == 0 else 0.0

                state = twin.simulate_step(
                    sensor_data=sensor,
                    irrigation=irrig,
                    timestep_hours=24.0 / steps_per_day,
                )

                water  = state["water"]
                crop   = state["crop"]
                weather_state = state["weather"]

                row = {
                    # Raw sensor readings (with noise)
                    "temperature":        round(_add_noise(sensor["temp"]),    2),
                    "humidity":           round(_add_noise(sensor["humidity"]), 2),
                    "light_level":        round(_add_noise(sensor["light"] / 7 * 100, 0.03), 1),
                    "soil_moisture_pct":  round(_add_noise(water["moisture_percent"], 0.02), 2),
                    "solar_radiation":    round(weather_state["solar_radiation"], 4),
                    "hour_of_day":        round(hour, 1),

                    # Physics-derived features
                    "water_deficit_mm":    round(water["water_deficit"],       4),
                    "moisture_fraction":   round(water["moisture"],            5),
                    "evapotranspiration":  round(water["evapotranspiration"],  4),
                    "accumulated_gdd":     round(crop["gdd_accumulated"],      2),
                    "growth_progress_pct": round(crop["growth_progress"],      2),

                    # Context
                    "day_of_season": day,
                    "scenario_id":   scenario_id,

                    # ── LABELS ────────────────────────────────────────────────
                    LABEL_IRRIGATION:   int(irrigate_today),
                    LABEL_GROWTH_STAGE: GROWTH_STAGE_MAP.get(
                        crop["growth_stage"], 0
                    ),
                    "growth_stage_name": crop["growth_stage"],
                    "crop_type":         crop_name,
                    "irrigation_amount_mm": round(irrig, 2),
                    "precipitation_mm":  round(sensor["rain"], 2),
                }
                rows.append(row)

        if (scenario_id + 1) % 10 == 0:
            print(f"  Generated {scenario_id + 1}/{num_scenarios} scenarios "
                  f"({len(rows):,} rows so far) …")

    return rows


# ──────────────────────────────────────────────────────────────────────────────
# Anomaly injection
# ──────────────────────────────────────────────────────────────────────────────
def inject_anomalies(
    rows: List[Dict],
    anomaly_fraction: float = 0.05,
    seed: int = RANDOM_SEED + 1,
) -> List[Dict]:
    """
    Inject synthetic sensor anomalies into a copy of the dataset.
    Adds an 'is_anomaly' label (0 = clean, 1 = anomaly).
    """
    random.seed(seed)
    anomaly_types = [
        "sensor_spike",
        "sensor_dropout",   # value stuck near zero
        "out_of_range",
    ]

    augmented = []
    for row in rows:
        r = dict(row)
        r["is_anomaly"] = 0

        if random.random() < anomaly_fraction:
            atype = random.choice(anomaly_types)
            sensor_key = random.choice(
                ["temperature", "humidity", "light_level", "soil_moisture_pct"]
            )
            if atype == "sensor_spike":
                r[sensor_key] = r[sensor_key] * random.uniform(3.0, 8.0)
            elif atype == "sensor_dropout":
                r[sensor_key] = random.uniform(0, 0.5)
            elif atype == "out_of_range":
                r[sensor_key] = random.choice([-999.0, 9999.0])
            r["is_anomaly"] = 1
            r["anomaly_type"] = atype

        augmented.append(r)
    return augmented


# ──────────────────────────────────────────────────────────────────────────────
# CSV writers
# ──────────────────────────────────────────────────────────────────────────────
def _write_csv(path: str, rows: List[Dict], fieldnames: List[str]):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"  Saved {len(rows):,} rows → {path}")


def save_datasets(rows: List[Dict]):
    """Write all output CSV files."""
    # 1. Full sensor dataset
    full_cols = FEATURE_COLUMNS + [
        LABEL_IRRIGATION, LABEL_GROWTH_STAGE, "growth_stage_name",
        "crop_type", "irrigation_amount_mm", "precipitation_mm",
    ]
    _write_csv(os.path.join(DATA_DIR, "sensor_dataset.csv"), rows, full_cols)

    # 2. Irrigation classification dataset
    irr_cols = FEATURE_COLUMNS + [LABEL_IRRIGATION]
    _write_csv(os.path.join(DATA_DIR, "irrigation_labels.csv"), rows, irr_cols)

    # 3. Growth-stage classification dataset
    gs_cols = FEATURE_COLUMNS + [LABEL_GROWTH_STAGE, "growth_stage_name"]
    _write_csv(os.path.join(DATA_DIR, "growth_stage_labels.csv"), rows, gs_cols)

    # 4. Anomaly dataset
    anomaly_rows = inject_anomalies(rows)
    anomaly_cols = FEATURE_COLUMNS + ["is_anomaly"]
    _write_csv(os.path.join(DATA_DIR, "anomaly_samples.csv"), anomaly_rows, anomaly_cols)

    # 5. Data-summary JSON
    summary = {
        "generated_at":   datetime.now().isoformat(),
        "total_rows":     len(rows),
        "num_scenarios":  NUM_SCENARIOS,
        "days_per_scenario": DAYS_PER_SCENARIO,
        "steps_per_day":  STEPS_PER_DAY,
        "feature_columns": FEATURE_COLUMNS,
        "labels": {
            "irrigation_needed": "binary 0/1",
            "growth_stage": "0=vegetative, 1=flowering, 2=fruiting, 3=ripening, 4=mature",
            "water_deficit_mm": "continuous (regression target)",
            "is_anomaly":    "binary 0/1 (anomaly dataset only)",
        },
        "class_distribution": {
            LABEL_IRRIGATION: {
                "0": sum(1 for r in rows if r[LABEL_IRRIGATION] == 0),
                "1": sum(1 for r in rows if r[LABEL_IRRIGATION] == 1),
            },
            LABEL_GROWTH_STAGE: {
                str(v): sum(1 for r in rows if r[LABEL_GROWTH_STAGE] == v)
                for v in range(5)
            },
        },
    }
    summary_path = os.path.join(DATA_DIR, "dataset_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"  Saved summary  → {summary_path}")


# ──────────────────────────────────────────────────────────────────────────────
# Entry-point
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 65)
    print("AgriTwin – ML Data Generator")
    print("=" * 65)
    print(f"\nGenerating {NUM_SCENARIOS} scenarios × {DAYS_PER_SCENARIO} days "
          f"× {STEPS_PER_DAY} steps …\n")

    rows = generate_dataset()

    print(f"\nTotal rows generated: {len(rows):,}")
    print("\nSaving datasets …")
    save_datasets(rows)

    print("\nDone! Files written to: ml/data/")
    print("=" * 65)
