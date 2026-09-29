"""
Fog Layer Camera Service
Runs on Raspberry Pi — captures images on schedule and on-demand (MQTT trigger).
Uploads every image to the cloud backend.

Requirements on Pi:
    pip install requests paho-mqtt
    sudo apt install fswebcam
"""

import subprocess
import time
import requests
import threading
import json
import os
from datetime import datetime

import paho.mqtt.client as mqtt

# ── Config ────────────────────────────────────────────────────────────────────
# Edit these to match your deployment
CLOUD_URL = os.environ.get("CLOUD_URL", "http://YOUR_SERVER_IP:5000")
MQTT_BROKER = os.environ.get("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
FARM_ID = os.environ.get("FARM_ID", "farm_001")

IMAGE_DIR = "/home/pi/camera_images"
CAPTURE_INTERVAL = 300          # seconds between automatic captures
RESOLUTION = "1280x960"

UPLOAD_ENDPOINT = f"{CLOUD_URL}/api/v1/camera/upload"
CAPTURE_TOPIC = f"farm/{FARM_ID}/camera/capture"   # listen for on-demand trigger
STATUS_TOPIC  = f"farm/{FARM_ID}/camera/status"    # publish capture status
# ─────────────────────────────────────────────────────────────────────────────

os.makedirs(IMAGE_DIR, exist_ok=True)


def _free_camera():
    """Release /dev/video0 if another process is holding it."""
    subprocess.run(
        ["sudo", "fuser", "-k", "/dev/video0"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(1)


def capture_image() -> str | None:
    """Capture a JPEG from the USB webcam. Returns the file path or None."""
    _free_camera()
    # Compute filename AFTER the free-camera sleep so the timestamp is current
    filename = datetime.now().strftime(f"{IMAGE_DIR}/image_%Y%m%d_%H%M%S.jpg")

    result = subprocess.run([
        "fswebcam",
        "-r", RESOLUTION,
        "--no-banner",
        filename,
    ])  # allow fswebcam to print to terminal so errors are visible

    if result.returncode == 0 and os.path.exists(filename):
        print(f"[Camera] Captured: {filename}")
        return filename
    else:
        print(f"[Camera] Capture failed or file not written (rc={result.returncode})")
        return None


def upload_image(filepath: str) -> bool:
    """Upload a JPEG to the cloud backend. Returns True on success."""
    try:
        with open(filepath, "rb") as f:
            response = requests.post(
                UPLOAD_ENDPOINT,
                files={"file": (os.path.basename(filepath), f, "image/jpeg")},
                data={"farm_id": FARM_ID},
                timeout=30,
            )
        if response.status_code == 200:
            print(f"[Camera] Uploaded: {os.path.basename(filepath)}")
            return True
        else:
            print(f"[Camera] Upload error {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"[Camera] Upload failed: {e}")
        return False


def capture_and_upload() -> bool:
    path = capture_image()
    if path:
        return upload_image(path)
    return False


# ── MQTT ──────────────────────────────────────────────────────────────────────

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[MQTT] Connected to broker {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(CAPTURE_TOPIC)
        print(f"[MQTT] Subscribed to {CAPTURE_TOPIC}")
    else:
        print(f"[MQTT] Connection failed, rc={rc}")


def on_message(client, userdata, msg):
    """Handle incoming capture request from cloud/dashboard."""
    print(f"[MQTT] On-demand capture requested")
    threading.Thread(target=_handle_on_demand_capture, args=(client,), daemon=True).start()


def _handle_on_demand_capture(client):
    success = capture_and_upload()
    payload = json.dumps({
        "status": "ok" if success else "error",
        "farm_id": FARM_ID,
        "timestamp": datetime.utcnow().isoformat(),
    })
    client.publish(STATUS_TOPIC, payload)


def start_mqtt_listener():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"camera_{FARM_ID}")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    client.loop_start()
    return client


# ── Main loop ─────────────────────────────────────────────────────────────────

def main():
    print("[Camera] Starting AgriTwin Camera Service")
    print(f"[Camera] Cloud: {CLOUD_URL}")
    print(f"[Camera] Broker: {MQTT_BROKER}:{MQTT_PORT}")

    mqtt_client = start_mqtt_listener()

    # Take an initial photo on startup
    capture_and_upload()

    while True:
        time.sleep(CAPTURE_INTERVAL)
        capture_and_upload()


if __name__ == "__main__":
    main()
