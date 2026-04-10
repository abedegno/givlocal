"""Tests for the /v1/inverter/{serial}/settings endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path):
    from unittest.mock import AsyncMock, MagicMock

    from givenergy_modbus_async.model.inverter import Inverter

    from givlocal.auth import TokenStore
    from givlocal.database import init_app_db
    from givlocal.main import InverterState, app, app_state
    from givlocal.settings_map import load_settings_from_cloud_dump
    from tests.fixtures.register_data import make_inverter_cache

    app_state.auth_required = False
    conn = init_app_db(str(tmp_path / "app.db"))
    app_state.token_store = TokenStore(conn)
    app_state.settings = load_settings_from_cloud_dump("cloud-data/settings.json")

    cache = make_inverter_cache()
    mock_plant = MagicMock()
    mock_plant.inverter = Inverter(cache)
    mock_plant.inverter_serial_number = "FA2424G403"
    mock_client = AsyncMock()
    mock_client.plant = mock_plant

    app_state.inverters = {
        "FA2424G403": InverterState(
            serial="FA2424G403",
            host="192.168.86.44",
            port=8899,
            plant=mock_plant,
            client=mock_client,
        )
    }
    return TestClient(app, raise_server_exceptions=False)


def test_list_settings(client):
    response = client.get("/v1/inverter/FA2424G403/settings")
    assert response.status_code == 200
    body = response.json()
    data = body["data"]
    assert len(data) > 20
    # Each setting should have id, name, and validation
    for s in data:
        assert "id" in s
        assert "name" in s
        assert "validation" in s


def test_read_setting_bool(client):
    # Setting 24 is "Enable Eco Mode" (bool)
    response = client.post("/v1/inverter/FA2424G403/settings/24/read")
    assert response.status_code == 200
    body = response.json()
    assert "value" in body["data"]


def test_read_setting_time(client):
    # Setting 64 is "AC Charge 1 Start Time" (charge_slot_1_start)
    # Fixture has HR(94) = 2330 -> "23:30"
    response = client.post("/v1/inverter/FA2424G403/settings/64/read")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["value"] == "23:30"


def test_read_setting_unknown_id(client):
    response = client.post("/v1/inverter/FA2424G403/settings/99999/read")
    assert response.status_code == 404


def test_read_setting_unknown_inverter(client):
    response = client.post("/v1/inverter/UNKNOWN/settings/64/read")
    assert response.status_code == 404


def test_write_setting(client):
    # Setting 71 is "Battery Reserve % Limit" (int, range:4,100)
    response = client.post(
        "/v1/inverter/FA2424G403/settings/71/write",
        json={"value": 20},
    )
    assert response.status_code in (200, 201)
    body = response.json()
    assert body["data"]["success"] is True


def test_write_setting_invalid_value(client):
    # Setting 71 validation is range:4,100 — value 2 is below min
    response = client.post(
        "/v1/inverter/FA2424G403/settings/71/write",
        json={"value": 2},
    )
    assert response.status_code == 422


def test_write_setting_time(client):
    # Setting 64 is "AC Charge 1 Start Time" (time)
    response = client.post(
        "/v1/inverter/FA2424G403/settings/64/write",
        json={"value": "01:30"},
    )
    assert response.status_code in (200, 201)
    body = response.json()
    assert body["data"]["success"] is True
