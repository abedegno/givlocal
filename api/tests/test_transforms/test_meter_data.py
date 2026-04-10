"""Tests for the meter_data transform."""

import pytest
from givenergy_modbus_async.model.inverter import Inverter

from givlocal.transforms.meter_data import transform_meter_data
from tests.fixtures.register_data import make_inverter_cache


@pytest.fixture
def result():
    cache = make_inverter_cache()
    inv = Inverter(cache)
    return transform_meter_data(inv)


def test_today_solar(result):
    # e_pv1_day + e_pv2_day = 4.8 + 3.0
    assert result["today"]["solar"] == 7.8


def test_today_grid_import(result):
    assert result["today"]["grid"]["import"] == 5.3


def test_today_grid_export(result):
    assert result["today"]["grid"]["export"] == 3.5


def test_today_battery_charge(result):
    assert result["today"]["battery"]["charge"] == 4.1


def test_today_battery_discharge(result):
    assert result["today"]["battery"]["discharge"] == 1.4


def test_today_consumption(result):
    assert result["today"]["consumption"] == 7.0


def test_total_solar(result):
    assert result["total"]["solar"] == 5724.2


def test_total_grid_import(result):
    assert result["total"]["grid"]["import"] == 13528.8


def test_total_grid_export(result):
    assert result["total"]["grid"]["export"] == 7190.6
