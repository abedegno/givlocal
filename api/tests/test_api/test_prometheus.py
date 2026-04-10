"""Tests for the /metrics Prometheus endpoint."""

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


def test_prometheus_metrics(client):
    response = client.get("/metrics")
    assert response.status_code == 200
    text = response.text
    assert 'givenergy_solar_power_watts{serial="FA2424G403"}' in text
    assert 'givenergy_battery_percent{serial="FA2424G403"}' in text
