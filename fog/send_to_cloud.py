"""
Fog → Cloud Data Sender
========================
Runs on the **Raspberry Pi** fog node.
Reads all unsynced sensor readings from the Raspberry Pi's SQLite buffer
and POSTs them to the cloud backend  POST /api/v1/sensors/ingest
that runs on the **laptop**.

After a successful upload the rows are marked  synced=1.

Usage (run on the Raspberry Pi):
    python fog/send_to_cloud.py
    python fog/send_to_cloud.py --db fog/data/fog_buffer.db --cloud http://<laptop-ip>:8000
    python fog/send_to_cloud.py --dry-run          # preview without sending
    python fog/send_to_cloud.py --all              # re-send already synced rows too

Environment variables (override defaults):
    FOG_DB_PATH       path to the SQLite buffer file on the Raspberry Pi
    CLOUD_BACKEND_URL base URL of the cloud backend running on the laptop
                      e.g. export CLOUD_BACKEND_URL=http://192.168.x.x:8000
"""

import os
import sys
import json
import sqlite3
import argparse
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional

# ── defaults ──────────────────────────────────────────────────────────────────
DEFAULT_DB_PATH    = os.environ.get(
    "FOG_DB_PATH",
    str(Path(__file__).parent / "data" / "fog_buffer.db"),
)# CLOUD_BACKEND_URL must point to the laptop running the cloud backend.
# On the Raspberry Pi, set this env var before running:
#   export CLOUD_BACKEND_URL=http://<laptop-ip>:8000
# Do NOT use localhost here — localhost on the RPi is not the cloud backend.DEFAULT_CLOUD_URL  = os.environ.get("CLOUD_BACKEND_URL", "http://localhost:8000")
INGEST_ENDPOINT    = "/api/v1/sensors/ingest"
BATCH_SIZE         = 200   # rows per HTTP POST


# ── SQLite helpers ─────────────────────────────────────────────────────────────
def _open_db(path: str) -> sqlite3.Connection:
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Fog buffer database not found: {path}\n"
            "Make sure the fog node has run at least once, or pass --db <path>."
        )
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def _detect_schema(conn: sqlite3.Connection) -> str:
    """
    The project has two slightly different SQLite schemas.
    Returns 'src' or 'buffer_manager' so we can adjust queries.
    """
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {r[0] for r in cur.fetchall()}
    if "sensor_data" in tables:
        cur2 = conn.execute("PRAGMA table_info(sensor_data)")
        cols = {r[1] for r in cur2.fetchall()}
        if "sensor_id" in cols:
            return "buffer_manager"   # offline_buffer.py schema
        return "src"                  # buffer.py schema
    raise RuntimeError("No sensor_data table found in this database.")


def _fetch_unsynced(
    conn: sqlite3.Connection,
    schema: str,
    limit: int = 10_000,
    include_synced: bool = False,
) -> List[sqlite3.Row]:
    cond = "" if include_synced else "WHERE synced = 0"
    cur = conn.execute(
        f"SELECT * FROM sensor_data {cond} ORDER BY timestamp ASC LIMIT ?",
        (limit,)
    )
    return cur.fetchall()


def _group_into_readings(
    rows: List[sqlite3.Row],
    schema: str,
) -> List[Dict]:
    """
    The fog SQLite stores ONE sensor type per row.
    Group rows that belong to the same sensor snapshot (same farm + close timestamp)
    into a single reading dict matching the cloud ingest schema.

    Sensor type names → cloud field names:
        soil_moisture / soil → soil_moisture
        temperature / temp   → temperature
        humidity              → humidity
        light / light_level   → light_level
    """
    SENSOR_MAP = {
        "soil_moisture":   "soil_moisture",
        "soil":            "soil_moisture",
        "temperature":     "temperature",
        "temp":            "temperature",
        "humidity":        "humidity",
        "light_level":     "light_level",
        "light":           "light_level",
    }

    # --- group by (farm_id, timestamp_bucket_of_5s) so closely timed rows merge
    buckets: Dict[tuple, Dict] = {}
    row_ids: Dict[tuple, List[int]] = {}

    for row in rows:
        r       = dict(row)
        farm_id = r.get("farm_id", "farm_001")
        ts      = r.get("timestamp", 0)

        # Normalise timestamp → int epoch seconds
        if isinstance(ts, str):
            try:
                ts = int(datetime.fromisoformat(ts).timestamp())
            except Exception:
                ts = 0
        ts_int = int(ts)
        bucket_key = (farm_id, ts_int // 5)    # 5-second buckets

        if bucket_key not in buckets:
            # Convert epoch → ISO string for the cloud
            ts_iso = datetime.fromtimestamp(ts_int, tz=timezone.utc).isoformat()
            buckets[bucket_key] = {
                "farm_id":      farm_id,
                "device_id":    r.get("device_id",  "fog_node"),
                "timestamp":    ts_iso,
                "temperature":  None,
                "humidity":     None,
                "light_level":  None,
                "soil_moisture": None,
            }
            row_ids[bucket_key] = []

        row_ids[bucket_key].append(r["id"])

        sensor_type = r.get("sensor_type", "")
        field = SENSOR_MAP.get(sensor_type)
        if field:
            buckets[bucket_key][field] = r.get("value")

    return list(buckets.values()), row_ids


def _mark_synced(conn: sqlite3.Connection, ids: List[int]):
    if not ids:
        return
    placeholders = ",".join("?" * len(ids))
    conn.execute(
        f"UPDATE sensor_data SET synced = 1 WHERE id IN ({placeholders})",
        ids,
    )
    conn.commit()


# ── HTTP sender ────────────────────────────────────────────────────────────────
def _post_batch(cloud_url: str, readings: List[Dict]) -> Dict:
    """POST a batch of readings to the cloud. Returns response dict."""
    url     = cloud_url.rstrip("/") + INGEST_ENDPOINT
    payload = json.dumps({"readings": readings}).encode("utf-8")
    req     = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        raise RuntimeError(f"HTTP {e.code} from cloud: {body}")


def _check_health(cloud_url: str) -> bool:
    """Returns True if cloud backend is reachable."""
    try:
        with urllib.request.urlopen(
            cloud_url.rstrip("/") + "/health", timeout=5
        ) as resp:
            return resp.status == 200
    except Exception:
        return False


# ── main ───────────────────────────────────────────────────────────────────────
def send_buffered_data(
    db_path:       str  = DEFAULT_DB_PATH,
    cloud_url:     str  = DEFAULT_CLOUD_URL,
    batch_size:    int  = BATCH_SIZE,
    dry_run:       bool = False,
    include_synced: bool = False,
):
    print("=" * 65)
    print("  Fog → Cloud Data Sender")
    print(f"  DB   : {db_path}")
    print(f"  Cloud: {cloud_url}")
    print(f"  Mode : {'DRY-RUN (no data sent)' if dry_run else 'LIVE'}")
    print("=" * 65)

    # 1. Open database
    conn = _open_db(db_path)
    schema = _detect_schema(conn)
    print(f"\n  Database schema detected: {schema}")

    # 2. Fetch unsynced rows
    rows = _fetch_unsynced(conn, schema, limit=50_000, include_synced=include_synced)
    if not rows:
        print("\n  No unsynced rows found. Nothing to send.")
        conn.close()
        return

    print(f"  Unsynced rows  : {len(rows):,}")

    # 3. Group into readings
    readings, row_ids_map = _group_into_readings(rows, schema)
    print(f"  Readings formed: {len(readings):,}  "
          f"(grouped from {len(rows):,} individual sensor rows)")

    if dry_run:
        print("\n  [DRY-RUN] First 3 readings that would be sent:")
        for r in readings[:3]:
            print(f"    {r}")
        print("\n  [DRY-RUN] Done. No data was sent or marked synced.")
        conn.close()
        return

    # 4. Check cloud availability
    if not _check_health(cloud_url):
        print(f"\n  ✗ Cloud backend not reachable at {cloud_url}")
        print("    Make sure the backend is running:  docker-compose up  OR")
        print("    cd cloud/backend && uvicorn main_working:app --reload")
        conn.close()
        return
    print(f"\n  ✓ Cloud backend reachable at {cloud_url}")

    # 5. Send in batches
    total_stored = 0
    total_errors = 0
    all_synced_ids: List[int] = []

    # Flatten row_ids in order of readings list
    bucket_keys = list(row_ids_map.keys())

    for batch_start in range(0, len(readings), batch_size):
        batch        = readings[batch_start : batch_start + batch_size]
        batch_keys   = bucket_keys[batch_start : batch_start + batch_size]

        print(f"  Sending batch {batch_start//batch_size + 1}  "
              f"({len(batch)} readings) … ", end="", flush=True)
        try:
            result = _post_batch(cloud_url, batch)
            stored = result.get("stored", 0)
            errors = result.get("errors", 0)
            total_stored += stored
            total_errors += errors
            print(f"stored={stored}  errors={errors}")

            # Collect IDs to mark synced
            if stored > 0:
                for key in batch_keys:
                    all_synced_ids.extend(row_ids_map[key])

        except Exception as e:
            print(f"FAILED: {e}")
            total_errors += len(batch)

    # 6. Mark synced
    if all_synced_ids:
        _mark_synced(conn, all_synced_ids)
        print(f"\n  Marked {len(all_synced_ids):,} rows as synced in local DB.")

    conn.close()

    # 7. Summary
    print("\n" + "=" * 65)
    print(f"  DONE")
    print(f"  Readings sent  : {total_stored:,}")
    print(f"  Errors         : {total_errors}")
    print("=" * 65)


# ── CLI ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Send fog-buffered sensor data to the cloud backend."
    )
    parser.add_argument(
        "--db", default=DEFAULT_DB_PATH,
        help=f"Path to fog SQLite buffer (default: {DEFAULT_DB_PATH})"
    )
    parser.add_argument(
        "--cloud", default=DEFAULT_CLOUD_URL,
        help=f"Cloud backend base URL (default: {DEFAULT_CLOUD_URL})"
    )
    parser.add_argument(
        "--batch-size", type=int, default=BATCH_SIZE,
        help=f"Readings per HTTP request (default: {BATCH_SIZE})"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview what would be sent without actually sending"
    )
    parser.add_argument(
        "--all", dest="include_synced", action="store_true",
        help="Re-send already-synced rows too"
    )
    args = parser.parse_args()

    send_buffered_data(
        db_path        = args.db,
        cloud_url      = args.cloud,
        batch_size     = args.batch_size,
        dry_run        = args.dry_run,
        include_synced = args.include_synced,
    )
