# GivEnergy Local Cloud API

Self-hosted replacement for the GivEnergy Cloud API. Communicates with your
GivEnergy inverter locally via Modbus TCP - no cloud dependency.

## Quick Start

1. Copy `config.example.yaml` to `config.yaml` and set your inverter IP
2. `docker compose up`
3. Note the admin API token printed in the logs
4. Access the API at `http://localhost:8099/v1/`

## API Compatibility

This server implements the GivEnergy Cloud API v1.50.1. Existing integrations
(Octopus Energy, Axle Energy, Home Assistant) should work by changing the base
URL from `api.givenergy.cloud` to your server address.

## Endpoints

- `GET /v1/communication-device` - List connected inverters
- `GET /v1/inverter/{serial}/system-data-latest` - Current solar/battery/grid data
- `GET /v1/inverter/{serial}/meter-data-latest` - Energy totals
- `GET /metrics` - Prometheus metrics for Grafana integration

## Development

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e ".[dev]"
PYTHONPATH=src:. .venv/bin/pytest tests/ -v
```
