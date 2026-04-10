# GivLocal

Self-hosted replacement for the GivEnergy Cloud API. Communicates with your GivEnergy inverter locally via Modbus TCP -- no cloud dependency.

## URGENT: Archive Your Cloud Data

GivEnergy has filed notice to appoint administrators. Archive your data from `api.givenergy.cloud` **now** before it goes offline.

### Quick Start

```bash
# Clone the repo
git clone https://github.com/abedegno/givlocal.git
cd givlocal/api

# Set up a virtual environment (required on Raspberry Pi / Debian)
python3 -m venv .venv
.venv/bin/pip install requests pyyaml

# Run the cloud dump tool
PYTHONPATH=src .venv/bin/python -m givlocal.cli.cloud_dump \
  --token YOUR_API_TOKEN \
  --output ./my-cloud-dump \
  --days 1460
```

### Getting an API token

1. Go to https://givenergy.cloud/account-settings/api-tokens
2. Click "Create Token"
3. Tick all scopes (or at minimum: `api:inverter`, `api:meter`, `api:account:read`, `api:site`)
4. Copy the token

### What gets archived

| Data | Description |
|------|-------------|
| **settings.json** | All inverter settings with IDs, names, and validation rules |
| **data_points.json** | Historical solar/battery/grid data (one entry per 5 minutes) |
| **presets.json** | Saved preset configurations |
| **events.json** | Fault and warning history |
| **communication_devices.json** | Inverter and dongle details |
| **sites.json** | Site configuration |
| **account.json** | Account details |

### Options

```bash
# Full dump (all history, takes ~20 minutes for 4 years)
# Full dump (all history, takes ~20 minutes for 4 years)
PYTHONPATH=src .venv/bin/python -m givlocal.cli.cloud_dump --token TOKEN --output ./dump --days 1460

# Settings only (fastest -- critical for GivLocal to work)
PYTHONPATH=src .venv/bin/python -m givlocal.cli.cloud_dump --token TOKEN --output ./dump --settings-only

# Last 30 days only
PYTHONPATH=src .venv/bin/python -m givlocal.cli.cloud_dump --token TOKEN --output ./dump --days 30
```

**Important:** The `settings.json` file is needed by GivLocal to control your inverter. Copy it to `cloud-data/settings.json` in your GivLocal installation after dumping.

---

## GivLocal API Server

A drop-in replacement for `api.givenergy.cloud/v1`. Existing integrations (Octopus Energy, Axle Energy, Home Assistant ge_cloud) work by changing the base URL.

### Quick Start

```bash
# 1. Copy config and set your inverter IP
cp config.example.yaml config.yaml
# Edit config.yaml: set host to your inverter's IP address

# 2. Place your cloud dump settings
mkdir -p cloud-data
cp /path/to/my-cloud-dump/inverters/YOUR_SERIAL/settings.json cloud-data/

# 3. Run with Docker
docker compose up
```

Or without Docker:

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e .
PYTHONPATH=src:. .venv/bin/python -m uvicorn givlocal.main:app --port 8099
```

Note the admin API token printed in the logs on first run.

### API Endpoints

**Data (read):**
- `GET /v1/inverter/{serial}/system-data-latest` -- Solar, battery, grid, consumption
- `GET /v1/inverter/{serial}/meter-data-latest` -- Energy totals (today + lifetime)
- `GET /v1/communication-device` -- List connected inverters

**Control (read/write):**
- `GET /v1/inverter/{serial}/settings` -- List all available settings
- `POST /v1/inverter/{serial}/settings/{id}/read` -- Read a setting value
- `POST /v1/inverter/{serial}/settings/{id}/write` -- Write a setting value

**Monitoring:**
- `GET /metrics` -- Prometheus metrics (no auth required)

### Authentication

All endpoints (except `/metrics`) require a Bearer token:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8099/v1/inverter/SERIAL/system-data-latest
```

### Prometheus / Grafana

The `/metrics` endpoint exposes inverter data in Prometheus format:

```
givenergy_solar_power_watts{serial="FA2424G403"} 1640
givenergy_battery_percent{serial="FA2424G403"} 98
givenergy_grid_power_watts{serial="FA2424G403"} -500
givenergy_consumption_watts{serial="FA2424G403"} 850
```

Point Prometheus at `http://your-server:8099/metrics` and build Grafana dashboards.

### Finding Your Inverter IP

Your GivEnergy inverter runs a WiFi access point. Find its IP on your router's DHCP client list -- look for a device with a hostname starting with `WH` or `WG`.

Verify it's reachable:

```bash
python3 -c "import socket; s=socket.socket(); s.settimeout(3); s.connect(('YOUR_IP', 8899)); print('OK'); s.close()"
```

---

## How It Works

GivLocal talks directly to your inverter over your local network using the Modbus TCP protocol on port 8899. This is the same protocol the inverter's WiFi module uses internally -- no cloud involved.

```
                          ┌──────────────┐
  Octopus / Axle ────────>│              │
  Home Assistant ────────>│   GivLocal   │──── Modbus TCP :8899 ────> Inverter
  Grafana ───────────────>│  (your LAN)  │
                          └──────────────┘
```

The server polls your inverter every 30 seconds and stores data in a local SQLite database. Settings are read from and written to the inverter in real-time.

## Development

```bash
git clone https://github.com/abedegno/givlocal.git
cd givlocal
python3.12 -m venv .venv
.venv/bin/pip install -e ".[dev]"
PYTHONPATH=src:. .venv/bin/pytest tests/ -v
```

## License

Apache-2.0

## Acknowledgements

- [givenergy-modbus-async](https://github.com/britkat1980/givenergy-modbus-async) -- Modbus TCP library (forked from GivTCP)
- [GivTCP](https://github.com/britkat1980/giv_tcp) -- The original GivEnergy local control project
- [GivEnergy Cloud API](https://givenergy.cloud/docs/api/v1) -- API specification (archived)
