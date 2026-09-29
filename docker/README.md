# Docker Deployment Guide

> **Architecture note:** Fog services (Mosquitto, Redis, fog-gateway) run **natively on
> the Raspberry Pi** (`agritwin-fog.local`). Docker on the laptop only manages the cloud
> layer (backend + frontend).
> See [fog/README.md](../fog/README.md) for Raspberry Pi fog setup.

## Quick Start

```bash
# Clone the repository
git clone https://github.com/Am4l-babu/S6-MINI-PROJECT.git
cd S6-MINI-PROJECT

# Start cloud services only (laptop)
docker-compose up --build

# Or use production config
cd docker && docker-compose up --build -d
```

## Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| **cloud-backend** | build: ./cloud/backend | 8000 | FastAPI REST API + SQLite + Digital Twin |
| **frontend** | build: ./cloud/frontend | 3000 | Next.js dashboard |

> **Fog services** (Mosquitto :1883, Redis :6379, fog-gateway :8001) run on the
> Raspberry Pi — not in Docker on the laptop.

## After Starting

- **Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs

## Health Checks

```bash
# All services status
docker-compose ps

# Backend
curl http://localhost:8000/health

# MQTT broker (on Raspberry Pi)
mosquitto_sub -h agritwin-fog.local -t 'farms/#' -v
```

## Data Persistence

| Volume | Service | Contents |
|--------|---------|----------|
| `mosquitto-data` | mosquitto | MQTT message persistence |
| `redis-data` | redis | Hot buffer cache |
| `fog-data` | fog-gateway | SQLite cold buffer |
| `backend-data` | cloud-backend | SQLite sensor history (sensor_history.db) |

## Environment Variables

The fog gateway reads from environment variables (set in docker-compose.yml):

```env
MQTT_BROKER=mosquitto       # MQTT broker hostname (Docker service name)
MQTT_PORT=1883
REDIS_HOST=redis             # Redis hostname (Docker service name)
REDIS_PORT=6379
CLOUD_BACKEND_URL=http://cloud-backend:8000
EMERGENCY_CONTROL_ENABLED=true
IRRIGATION_THRESHOLD=30.0    # Soil moisture % to trigger irrigation
TEMPERATURE_ALERT=35.0       # Temperature °C to trigger cooling
```

## Troubleshooting

```bash
# View logs for a specific service
docker-compose logs -f fog-gateway

# Restart a service
docker-compose restart cloud-backend

# Reset everything (removes data!)
docker-compose down -v
docker-compose up --build
```

## Production Notes

The `docker/mosquitto/mosquitto.conf` enables password-based auth.
For production deployment:

- Set strong passwords in environment variables
- Enable TLS on Mosquitto (uncomment TLS section in mosquitto.conf)
- Use a reverse proxy (Nginx) for HTTPS
- Back up the SQLite databases regularly

## Future Services (Not Yet Integrated)

These services can be added when the project scales beyond the current setup:

| Service | When to Add | Purpose |
|---------|------------|---------|
| **InfluxDB** | When SQLite can't handle write volume | Time-series DB optimized for high-frequency sensor data |
| **PostgreSQL** | When adding user auth & multi-tenancy | Relational DB for user/farm/device management |
| **Grafana** | When needing advanced analytics dashboards | Alternative visualization with InfluxDB/Prometheus data sources |
| **Prometheus** | When deploying to production | Metrics collection, service health monitoring, alerting rules |
