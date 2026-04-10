"""End-to-end smoke tests covering auth, data, and metrics endpoints."""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from givenergy_modbus_async.model.battery import Battery
from givenergy_modbus_async.model.inverter import Inverter

from tests.fixtures.register_data import make_battery_cache, make_inverter_cache


@pytest.fixture
def e2e_client(tmp_path):
    from givlocal.auth import TokenStore, generate_token
    from givlocal.database import init_app_db
    from givlocal.main import InverterState, app, app_state
    from givlocal.metrics_store import MetricsStore

    app_state.auth_required = True
    conn = init_app_db(str(tmp_path / "app.db"))
    app_state.token_store = TokenStore(conn)
    app_state.metrics_store = MetricsStore(str(tmp_path / "metrics.db"))

    plaintext, _ = generate_token()
    app_state.token_store.create("test", plaintext)

    inv_cache = make_inverter_cache()
    bat_cache = make_battery_cache()
    mock_plant = MagicMock()
    mock_plant.inverter = Inverter(inv_cache)
    mock_plant.inverter_serial_number = "FA2424G403"
    mock_plant.data_adapter_serial_number = "WH2424G403"
    mock_plant.number_batteries = 1
    mock_plant.batteries = [Battery(bat_cache)]

    app_state.inverters = {
        "FA2424G403": InverterState(serial="FA2424G403", host="192.168.86.44", port=8899, plant=mock_plant)
    }
    return TestClient(app), plaintext


def test_auth_required_without_token(e2e_client):
    client, _ = e2e_client
    resp = client.get("/v1/inverter/FA2424G403/system-data-latest")
    assert resp.status_code == 401


def test_auth_works_with_valid_token(e2e_client):
    client, token = e2e_client
    resp = client.get(
        "/v1/inverter/FA2424G403/system-data-latest",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["status"] == "Normal"
    assert data["solar"]["power"] == 1640


def test_full_data_flow(e2e_client):
    client, token = e2e_client
    headers = {"Authorization": f"Bearer {token}"}
    # Communication devices
    resp = client.get("/v1/communication-device", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1
    # System data
    resp = client.get("/v1/inverter/FA2424G403/system-data-latest", headers=headers)
    assert resp.status_code == 200
    # Meter data
    resp = client.get("/v1/inverter/FA2424G403/meter-data-latest", headers=headers)
    assert resp.status_code == 200
    # Prometheus (no auth)
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "givenergy_solar_power_watts" in resp.text
    # Root
    resp = client.get("/")
    assert resp.status_code == 200
