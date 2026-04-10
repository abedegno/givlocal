"""Tests for the /v1/inverter/{serial}/system-data-latest and meter-data-latest routes."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path):
    from unittest.mock import MagicMock

    from givenergy_modbus_async.model.inverter import Inverter

    from givlocal.auth import TokenStore
    from givlocal.database import init_app_db
    from givlocal.main import InverterState, app, app_state
    from givlocal.metrics_store import MetricsStore
    from tests.fixtures.register_data import make_inverter_cache

    app_state.auth_required = False
    conn = init_app_db(str(tmp_path / "app.db"))
    app_state.token_store = TokenStore(conn)
    app_state.metrics_store = MetricsStore(str(tmp_path / "metrics.db"))

    cache = make_inverter_cache()
    mock_plant = MagicMock()
    mock_plant.inverter = Inverter(cache)
    mock_plant.inverter_serial_number = "FA2424G403"
    mock_plant.data_adapter_serial_number = "WH2424G403"
    mock_plant.number_batteries = 1

    app_state.inverters = {
        "FA2424G403": InverterState(serial="FA2424G403", host="192.168.86.44", port=8899, plant=mock_plant)
    }
    return TestClient(app, raise_server_exceptions=False)


def test_system_data_latest(client):
    response = client.get("/v1/inverter/FA2424G403/system-data-latest")
    assert response.status_code == 200
    body = response.json()
    data = body["data"]
    assert data["status"] == "Normal"
    assert data["solar"]["power"] == 1640  # p_pv1=1021 + p_pv2=619
    assert data["battery"]["percent"] == 100


def test_meter_data_latest(client):
    response = client.get("/v1/inverter/FA2424G403/meter-data-latest")
    assert response.status_code == 200
    body = response.json()
    data = body["data"]
    assert "today" in data
    assert "total" in data


def test_unknown_inverter_returns_404(client):
    response = client.get("/v1/inverter/UNKNOWN/system-data-latest")
    assert response.status_code == 404


def test_data_points_returns_paginated(client):
    import time

    from givlocal.main import app_state

    store = app_state.metrics_store
    ts = int(time.time())
    for i in range(5):
        store.write_data_point("FA2424G403", ts - (i * 300), {"status": 1, "p_pv1": 100 + i, "p_pv2": 50})

    from datetime import date

    today = date.today().isoformat()
    response = client.get(f"/v1/inverter/FA2424G403/data-points/{today}")
    assert response.status_code == 200
    body = response.json()
    assert "data" in body
    assert isinstance(body["data"], list)
    assert len(body["data"]) > 0
    first = body["data"][0]
    assert "power" in first
    assert "today" in first
    meta = body["meta"]
    assert meta["total"] == 5
    assert meta["current_page"] == 1


def test_events_returns_list(client):
    response = client.get("/v1/inverter/FA2424G403/events")
    assert response.status_code == 200
    body = response.json()
    assert "data" in body
    assert isinstance(body["data"], list)


def test_health_returns_checks(client):
    response = client.get("/v1/inverter/FA2424G403/health")
    assert response.status_code == 200
    body = response.json()
    checks = body["data"]["checks"]
    assert isinstance(checks, list)
    assert len(checks) > 0
    for check in checks:
        assert "name" in check
        assert "value" in check
        assert "status" in check
        assert "unit" in check


def test_health_unknown_inverter(client):
    response = client.get("/v1/inverter/UNKNOWN/health")
    assert response.status_code == 404
