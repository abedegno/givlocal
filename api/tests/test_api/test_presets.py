"""Tests for the /v1/inverter/{serial}/preset-profile API routes."""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path):
    from unittest.mock import AsyncMock, MagicMock

    from givenergy_modbus_async.model.inverter import Inverter

    from givlocal.auth import TokenStore
    from givlocal.database import init_app_db
    from givlocal.main import InverterState, app, app_state
    from givlocal.metrics_store import MetricsStore
    from givlocal.settings_map import load_settings_from_cloud_dump
    from tests.fixtures.register_data import make_inverter_cache

    app_state.auth_required = False
    conn = init_app_db(str(tmp_path / "app.db"))
    app_state.token_store = TokenStore(conn)
    app_state.metrics_store = MetricsStore(str(tmp_path / "metrics.db"))
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


def test_list_presets_empty(client):
    response = client.get("/v1/inverter/FA2424G403/preset-profile")
    assert response.status_code == 200
    body = response.json()
    assert body["data"] == []


def test_create_and_list_preset(client):
    # Create a profile
    create_response = client.post(
        "/v1/inverter/FA2424G403/preset-profile",
        json={"name": "Winter Mode", "settings": {"24": True, "71": 20}},
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["data"]["name"] == "Winter Mode"
    assert "id" in created["data"]

    # List should now contain the profile
    list_response = client.get("/v1/inverter/FA2424G403/preset-profile")
    assert list_response.status_code == 200
    data = list_response.json()["data"]
    assert len(data) == 1
    assert data[0]["name"] == "Winter Mode"


def test_delete_preset(client):
    # Create a profile
    create_response = client.post(
        "/v1/inverter/FA2424G403/preset-profile",
        json={"name": "Summer Mode", "settings": {"24": False, "71": 50}},
    )
    assert create_response.status_code == 201
    profile_id = create_response.json()["data"]["id"]

    # Delete it (TestClient.delete() doesn't support a body; use request() instead)
    delete_response = client.request(
        "DELETE",
        "/v1/inverter/FA2424G403/preset-profile",
        json={"id": profile_id},
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["data"]["success"] is True

    # List should be empty again
    list_response = client.get("/v1/inverter/FA2424G403/preset-profile")
    assert list_response.status_code == 200
    assert list_response.json()["data"] == []
