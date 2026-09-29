"""
Thompson Sampling for Adaptive Sensor Polling

Runs on the Fog layer (Raspberry Pi). Learns the optimal polling interval
for each sensor by treating interval selection as a multi-armed bandit problem.

Why Fog, not Edge:
  - ESP32 lacks RAM/FPU for Beta-distribution sampling in a real-time loop.
  - Fog already sees every reading via MQTT and can publish commands back to
    the ESP32 on  farms/001/commands.
  - Cloud is too far away for tight feedback; Fog closes the loop locally.

Arms  (per sensor): 5 s, 10 s, 20 s, 30 s, 60 s
Reward signal     : information gain — standardised |delta| from rolling mean.
                    High gain  → sensor is changing → sample more often (alpha ++)
                    Low  gain  → sensor is quiet    → relax interval (beta ++)
State persistence : JSON file so the Pi can survive reboots.
"""

import json
import math
import random
import time
from collections import deque
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from loguru import logger


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SENSOR_TYPES = ["temperature", "humidity", "light", "soil_moisture"]

# Candidate polling intervals in milliseconds sent to ESP32
ARMS_MS: List[int] = [5_000, 10_000, 20_000, 30_000, 60_000]

# Rolling window for computing information gain
WINDOW = 10

# Fraction of readings between Thompson decisions
DECIDE_EVERY = 20          # re-run TS every 20 incoming readings

# Minimum interval the fog will ever recommend (safety floor)
MIN_INTERVAL_MS = 5_000
MAX_INTERVAL_MS = 60_000

# Reward threshold: |z-score| above this = "informative" reading
INFO_GAIN_THRESHOLD = 0.5

# State file path (relative to fog root)
STATE_FILE = Path(__file__).parent.parent.parent / "data" / "ts_state.json"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ArmState:
    """Beta(alpha, beta) distribution for one (sensor, interval) arm."""
    interval_ms: int
    alpha: float = 1.0   # successes (informative readings)
    beta: float  = 1.0   # failures  (quiet readings)

    @property
    def expected_reward(self) -> float:
        """E[Beta(α,β)] = α / (α+β)"""
        return self.alpha / (self.alpha + self.beta)

    def sample(self) -> float:
        """Draw one sample from Beta(α, β) — the Thompson step."""
        # Python's random.betavariate is available without numpy
        return random.betavariate(self.alpha, self.beta)

    def update(self, reward: float):
        """
        reward ∈ [0, 1].  We convert to a Bernoulli-style update:
          reward >= INFO_GAIN_THRESHOLD → success (alpha++)
          else                          → failure (beta++)
        """
        if reward >= INFO_GAIN_THRESHOLD:
            self.alpha += 1.0
        else:
            self.beta += 1.0

    # Decay old counts so the bandit keeps adapting (sliding window effect)
    def decay(self, factor: float = 0.995):
        self.alpha = max(1.0, self.alpha * factor)
        self.beta  = max(1.0, self.beta  * factor)


@dataclass
class SensorBandit:
    """All arms for a single sensor type."""
    sensor_type: str
    arms: List[ArmState] = field(default_factory=list)
    current_arm_idx: int = 0            # index into `arms`
    history: List[float] = field(default_factory=list)  # recent raw values
    message_count: int = 0

    def __post_init__(self):
        if not self.arms:
            self.arms = [ArmState(interval_ms=ms) for ms in ARMS_MS]

    # ---- Thompson selection --------------------------------------------------

    def select_arm(self) -> ArmState:
        """Sample from every arm's Beta distribution, pick the highest."""
        samples = [(arm.sample(), i) for i, arm in enumerate(self.arms)]
        best_idx = max(samples, key=lambda x: x[0])[1]
        self.current_arm_idx = best_idx
        return self.arms[best_idx]

    # ---- Reward calculation --------------------------------------------------

    def observe(self, value: float) -> float:
        """
        Record a new sensor reading, return the information-gain reward.

        Info gain = |z-score| of this value within the rolling window.
        Clipped to [0, 1] for the Beta update.
        """
        win = self.history[-WINDOW:]
        if len(win) >= 3:
            mean = sum(win) / len(win)
            variance = sum((v - mean) ** 2 for v in win) / len(win)
            std = math.sqrt(variance) if variance > 0 else 1e-6
            z = abs(value - mean) / std
            reward = min(1.0, z / 3.0)          # normalise: z=3 → reward=1
        else:
            reward = 0.5                          # neutral until we have history

        self.history.append(value)
        if len(self.history) > WINDOW * 4:       # cap memory
            self.history = self.history[-WINDOW * 2:]

        self.message_count += 1
        return reward

    @property
    def current_interval_ms(self) -> int:
        return self.arms[self.current_arm_idx].interval_ms


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------

class AdaptiveSamplingTS:
    """
    Thompson Sampling scheduler for adaptive sensor polling.

    Usage (inside fog MQTT handler):
        ts = AdaptiveSamplingTS()
        ts.on_reading("temperature", 31.5)     # call each time a reading arrives
        cmd = ts.get_command()                  # returns dict or None
        if cmd:
            mqtt_client.publish("farms/001/commands", json.dumps(cmd))
    """

    def __init__(self, state_file: Path = STATE_FILE):
        self._file = state_file
        self._bandits: Dict[str, SensorBandit] = {
            s: SensorBandit(sensor_type=s) for s in SENSOR_TYPES
        }
        self._total_messages = 0
        self._pending_command: Optional[dict] = None
        self._load_state()
        logger.info("✓ AdaptiveSamplingTS initialised "
                    f"(arms={ARMS_MS}, decide_every={DECIDE_EVERY})")

    # ---- Public API ---------------------------------------------------------

    def on_reading(self, sensor_type: str, value: float):
        """
        Call every time a sensor reading arrives at the fog layer.
        Internally:
          1. Compute information-gain reward for the current arm.
          2. Update that arm's Beta distribution.
          3. Every DECIDE_EVERY readings, run Thompson selection for ALL sensors
             and set a pending command if any interval changed.
        """
        if sensor_type not in self._bandits:
            return

        bandit = self._bandits[sensor_type]
        reward = bandit.observe(value)
        bandit.arms[bandit.current_arm_idx].update(reward)

        # Decay all arms slightly on each observation (slow forgetting)
        for arm in bandit.arms:
            arm.decay()

        self._total_messages += 1

        # Periodically re-run Thompson selection
        if self._total_messages % DECIDE_EVERY == 0:
            self._run_selection()
            self._save_state()

    def get_command(self) -> Optional[dict]:
        """
        Return an MQTT command dict if the TS has decided to change intervals,
        then clear the pending command. Returns None otherwise.

        Command schema (sent to farms/001/commands):
        {
          "command": "set_interval",
          "read_ms":    <fastest interval across all sensors>,
          "publish_ms": <slightly slower — aggregate before publish>
          "sensor_intervals": {
              "temperature": 10000,
              "humidity":    20000,
              ...
          }
        }
        """
        cmd = self._pending_command
        self._pending_command = None
        return cmd

    def get_status(self) -> dict:
        """Return a human-readable status dict (for API endpoint)."""
        sensors = {}
        for s, bandit in self._bandits.items():
            arm = bandit.arms[bandit.current_arm_idx]
            sensors[s] = {
                "current_interval_ms": arm.interval_ms,
                "expected_reward":     round(arm.expected_reward, 3),
                "alpha":               round(arm.alpha, 2),
                "beta":                round(arm.beta, 2),
                "messages_seen":       bandit.message_count,
                "arm_rankings": [
                    {
                        "interval_ms":      a.interval_ms,
                        "expected_reward":  round(a.expected_reward, 3),
                        "alpha":            round(a.alpha, 2),
                        "beta":             round(a.beta, 2),
                    }
                    for a in sorted(bandit.arms,
                                    key=lambda x: x.expected_reward,
                                    reverse=True)
                ],
            }
        return {
            "total_messages_processed": self._total_messages,
            "decide_every":             DECIDE_EVERY,
            "arms_ms":                  ARMS_MS,
            "sensors":                  sensors,
        }

    # ---- Internal -----------------------------------------------------------

    def _run_selection(self):
        """Run Thompson selection for every sensor and emit a command if any changed."""
        new_intervals: Dict[str, int] = {}
        changed = False

        for s, bandit in self._bandits.items():
            old_ms = bandit.current_interval_ms
            new_arm = bandit.select_arm()
            new_ms = new_arm.interval_ms
            new_intervals[s] = new_ms
            if new_ms != old_ms:
                changed = True
                logger.info(
                    f"TS adaptive sensing [{s}]: "
                    f"{old_ms // 1000}s → {new_ms // 1000}s  "
                    f"(α={new_arm.alpha:.1f}, β={new_arm.beta:.1f})"
                )

        if changed:
            # The read interval on the ESP32 is a single value that gates ALL sensors.
            # Use the fastest interval chosen so no sensor misses its window.
            read_ms    = min(new_intervals.values())
            # Publish slightly less often than read (at least 2× read)
            publish_ms = max(read_ms * 2, MIN_INTERVAL_MS)

            self._pending_command = {
                "command":          "set_interval",
                "read_ms":          read_ms,
                "publish_ms":       publish_ms,
                "sensor_intervals": new_intervals,
                "ts":               int(time.time()),
            }
            logger.info(
                f"TS command queued → read={read_ms // 1000}s, "
                f"publish={publish_ms // 1000}s"
            )

    # ---- Persistence --------------------------------------------------------

    def _save_state(self):
        try:
            self._file.parent.mkdir(parents=True, exist_ok=True)
            state = {
                "total_messages": self._total_messages,
                "bandits": {
                    s: {
                        "current_arm_idx": b.current_arm_idx,
                        "history":         b.history[-WINDOW:],
                        "message_count":   b.message_count,
                        "arms": [
                            {"interval_ms": a.interval_ms,
                             "alpha":       a.alpha,
                             "beta":        a.beta}
                            for a in b.arms
                        ],
                    }
                    for s, b in self._bandits.items()
                },
            }
            self._file.write_text(json.dumps(state, indent=2))
        except Exception as e:
            logger.warning(f"Could not save TS state: {e}")

    def _load_state(self):
        if not self._file.exists():
            return
        try:
            state = json.loads(self._file.read_text())
            self._total_messages = state.get("total_messages", 0)
            for s, bdata in state.get("bandits", {}).items():
                if s not in self._bandits:
                    continue
                b = self._bandits[s]
                b.current_arm_idx = bdata.get("current_arm_idx", 0)
                b.history          = bdata.get("history", [])
                b.message_count    = bdata.get("message_count", 0)
                for i, adata in enumerate(bdata.get("arms", [])):
                    if i < len(b.arms):
                        b.arms[i].alpha = adata.get("alpha", 1.0)
                        b.arms[i].beta  = adata.get("beta",  1.0)
            logger.info(f"Loaded TS state from {self._file} "
                        f"({self._total_messages} prior messages)")
        except Exception as e:
            logger.warning(f"Could not load TS state ({e}) — starting fresh")
