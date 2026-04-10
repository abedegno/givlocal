"""Tests for the /v1/communication-device API routes."""

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


def test_list_communication_devices(client):
    response = client.get("/v1/communication-device")
    assert response.status_code == 200
    body = response.json()
    assert "data" in body
    devices = body["data"]
    assert len(devices) == 1
    device = devices[0]
    assert device["serial_number"] == "WH2424G403"
    assert device["inverter"]["serial"] == "FA2424G403"


def test_get_single_device(client):
    response = client.get("/v1/communication-device/WH2424G403")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["serial_number"] == "WH2424G403"


def test_get_unknown_device_returns_404(client):
    response = client.get("/v1/communication-device/UNKNOWN")
    assert response.status_code == 404
