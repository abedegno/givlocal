"""Tests for the system_data transform."""

import pytest
from givenergy_modbus_async.model.inverter import Inverter

from givlocal.transforms.system_data import transform_system_data
from tests.fixtures.register_data import make_inverter_cache


@pytest.fixture
def result():
    cache = make_inverter_cache()
    inv = Inverter(cache)
    return transform_system_data(inv)


def test_status(result):
    assert result["status"] == "Normal"


def test_solar_power(result):
    # 1021 + 619
    assert result["solar"]["power"] == 1640


def test_solar_array1(result):
    arr = result["solar"]["arrays"][0]
    assert arr["array"] == 1
    assert arr["voltage"] == 275.3
    assert arr["current"] == 3.7
    assert arr["power"] == 1021


def test_solar_array2(result):
    arr = result["solar"]["arrays"][1]
    assert arr["array"] == 2


def test_grid_voltage(result):
    assert result["grid"]["voltage"] == 245.9


def test_grid_frequency(result):
    assert result["grid"]["frequency"] == 50.04


def test_battery_percent(result):
    assert result["battery"]["percent"] == 100


def test_battery_power(result):
    assert result["battery"]["power"] == 10


def test_inverter_power(result):
    assert result["inverter"]["power"] == 1440


def test_consumption(result):
    assert result["consumption"] == 138
