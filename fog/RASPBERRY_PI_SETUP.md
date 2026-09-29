# Raspberry Pi Fog Node — Setup & Verification Guide

## Architecture

```
Router / hotspot (same WiFi network)
├── ESP32  (edge device)
├── Raspberry Pi Zero 2 W  →  agritwin-fog.local  (fog node)
│   ├── Mosquitto MQTT broker  (port 1883)
│   └── Fog gateway service   (port 8001)
└── Laptop  (cloud backend, port 8000)
```

> **Critical requirement:** ESP32, Raspberry Pi, and laptop **must all be on
> the same WiFi network** for mDNS (`agritwin-fog.local`) to resolve.

---

## 1  One-time Pi Setup

### 1.1  Set the hostname

```bash
sudo hostnamectl set-hostname agritwin-fog
```

Edit `/etc/hosts` and make sure the line is:
```
127.0.1.1   agritwin-fog
```

### 1.2  Install & configure Mosquitto

```bash
sudo apt update
sudo apt install -y mosquitto mosquitto-clients

# Deploy the project config
sudo cp /path/to/project/fog/config/mosquitto-pi.conf \
        /etc/mosquitto/conf.d/agritwin.conf

# Disable the default config (it may conflict on port 1883)
sudo rm -f /etc/mosquitto/conf.d/default.conf

sudo systemctl enable mosquitto
sudo systemctl restart mosquitto
```

### 1.3  Install Avahi (mDNS daemon)

Raspberry Pi OS includes Avahi by default.  Verify it is running:

```bash
sudo systemctl enable avahi-daemon
sudo systemctl start  avahi-daemon
sudo systemctl status avahi-daemon
```

The Pi now advertises itself as `agritwin-fog.local` on the LAN.

---

## 2  Fog Gateway Service

### 2.1  Environment file

Copy the example and edit it:

```bash
cd /path/to/project/fog
cp config/.env.example .env    # must be at fog/.env  (Settings reads CWD/.env)
nano .env
```

Key variables to set:

| Variable         | Value                                  |
|------------------|----------------------------------------|
| `MQTT_BROKER_HOST` | `localhost` (broker is on the same Pi) |
| `CLOUD_API_URL`  | `http://<laptop-ip>:8000`              |

### 2.2  Run the fog gateway

```bash
cd /path/to/project/fog
pip install -r requirements.txt
python main.py
```

---

## 3  Testing the MQTT Connection

Run these commands **on the Raspberry Pi**.

### 3.1  Confirm Mosquitto is listening on port 1883

```bash
sudo ss -tlnp | grep 1883
# Expected:  LISTEN  0  ...  0.0.0.0:1883
```

### 3.2  Subscribe to all farm topics (leave this running in one terminal)

```bash
mosquitto_sub -h localhost -t "farms/#" -v
```

### 3.3  Publish a test message (second terminal)

```bash
mosquitto_pub -h localhost \
  -t "farms/001/sensors/temperature/data" \
  -m '{"device_id":"test","temperature":25.3,"timestamp":1000}'
```

You should immediately see the message appear in the subscriber terminal.

### 3.4  Test from another machine on the same network

Replace `192.168.x.x` with the Pi's IP address (or use the hostname):

```bash
# Subscribe
mosquitto_sub -h agritwin-fog.local -t "farms/#" -v

# Publish (simulates an ESP32)
mosquitto_pub -h agritwin-fog.local \
  -t "farms/001/sensors/temperature/data" \
  -m '{"device_id":"esp32_edge_001","temperature":24.5}'
```

---

## 4  Verifying ESP32 Data Arrives on the Pi

1. Flash the updated firmware to the ESP32 (`cd edge && pio run -t upload`).
2. On the Pi, subscribe to the wildcard topic:
   ```bash
   mosquitto_sub -h localhost -t "farms/001/sensors/#" -v
   ```
3. Open the ESP32 serial monitor (`pio device monitor`).
4. Wait for the ESP32 to connect and publish (every 10 s).
5. You should see three messages per cycle:
   - `farms/001/sensors/temperature/data  {"device_id":"esp32_edge_001","temperature":25.3,...}`
   - `farms/001/sensors/humidity/data     {"device_id":"esp32_edge_001","humidity":60.0,...}`
   - `farms/001/sensors/light/data        {"device_id":"esp32_edge_001","light_level":72.0,...}`

---

## 5  Full End-to-End Verification

```
ESP32  →(MQTT)→  Pi:1883  →(fog gateway)→  Laptop:8000
```

1. **Pi receives MQTT**: confirmed with `mosquitto_sub` (step 4 above).
2. **Fog gateway processes data**: check fog gateway logs:
   ```bash
   tail -f /path/to/project/fog/logs/fog_gateway.log
   # Look for: "Received sensor data from esp32_edge_001"
   ```
3. **Cloud backend receives data**: on the laptop, hit the health endpoint:
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/api/v1/farms/001/sensors/latest
   ```

---

## 6  Debugging

### ESP32 cannot connect to `agritwin-fog.local`

| Check | Command |
|-------|---------|
| WiFi connected | Serial monitor: `IP Address: ...` printed? |
| mDNS started | Serial monitor: `[mDNS] Started OK` printed? |
| Pi reachable (ping) | `ping agritwin-fog.local` from a laptop on same network |
| Mosquitto running | `sudo systemctl status mosquitto` on Pi |
| Port 1883 open | `sudo ss -tlnp \| grep 1883` on Pi |
| Firewall | `sudo ufw allow 1883/tcp` on Pi if ufw is enabled |

### Mosquitto service won't start

```bash
# View detailed errors
sudo journalctl -u mosquitto -n 50 --no-pager

# Validate config syntax
mosquitto -c /etc/mosquitto/conf.d/agritwin.conf --test-config
```

### ESP32 PubSubClient state codes

| Code | Meaning |
|------|---------|
| -4   | `MQTT_CONNECTION_TIMEOUT` — broker unreachable / port blocked |
| -3   | `MQTT_CONNECTION_LOST` |
| -2   | `MQTT_CONNECT_FAILED` — TCP connect failed |
| -1   | `MQTT_DISCONNECTED` |
|  0   | `MQTT_CONNECTED` ✓ |
|  5   | `MQTT_CONNECT_UNAUTHORIZED` — broker requires auth |

### Manually publish from the Pi to test the fog gateway

```bash
mosquitto_pub -h localhost \
  -t "farms/001/sensors/temperature/data" \
  -m '{"device_id":"debug_esp32","temperature":22.1,"humidity":55.0,"timestamp":1000}'
```

Then check the fog gateway log for the ingested record.

---

## 7  Topic Reference

| Topic | Direction | Publisher | Subscriber |
|-------|-----------|-----------|------------|
| `farms/001/sensors/temperature/data` | edge → fog | ESP32 | Fog gateway |
| `farms/001/sensors/humidity/data`    | edge → fog | ESP32 | Fog gateway |
| `farms/001/sensors/light/data`       | edge → fog | ESP32 | Fog gateway |
| `farms/001/status`                   | edge → fog | ESP32 | Fog gateway |
| `farms/001/lwt`                      | edge → fog | Mosquitto (LWT) | Fog gateway |
| `farms/001/commands`                 | fog → edge | Fog gateway | ESP32 |
