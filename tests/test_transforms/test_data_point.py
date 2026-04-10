"""Tests for the data_point transform."""

import pytest

from givlocal.transforms.data_point import transform_data_point

# Unix timestamp for 2024-04-09T16:00:00Z
_TIMESTAMP = 1712678400

_SAMPLE_DATA = {
    "status": 1,
    # solar
    "p_pv1": 1021,
    "p_pv2": 619,
    "v_pv1": 275.3,
    "i_pv1": 3.7,
    "v_pv2": 165.9,
    "i_pv2": 3.7,
    # grid
    "v_ac1": 245.9,
    "i_ac1": 6.4,
    "p_grid_out": 1302,
    "f_ac1": 50.04,
    # battery
    "battery_percent": 100,
    "p_battery": 10,
    "temp_battery": 18.0,
    # consumption
    "p_load_demand": 138,
    # inverter
    "temp_inverter_heatsink": 38.0,
    "p_inverter_out": 1440,
    "v_eps_backup": 247.3,
    "f_eps_backup": 50.05,
    # today energy totals
    "e_pv1_day": 4.8,
    "e_pv2_day": 3.0,
    "e_grid_in_day": 5.3,
    "e_grid_out_day": 3.5,
    "e_battery_charge_today": 4.1,
    "e_battery_discharge_today": 1.4,
    "e_inverter_out_day": 7.0,
}


@pytest.fixture
def result():
    return transform_data_point(_TIMESTAMP, _SAMPLE_DATA)


def test_transform_data_point_has_required_fields(result):
    # top-level fields
    assert result["time"] == "2024-04-09T16:00:00Z"
    assert result["status"] == "NORMAL"

    # power.solar
    assert result["power"]["solar"]["power"] == 1640  # p_pv1 + p_pv2
    arrays = result["power"]["solar"]["arrays"]
    assert arrays[0]["array"] == 1
    assert arrays[0]["power"] == 1021
    assert arrays[1]["array"] == 2
    assert arrays[1]["power"] == 619

    # power.grid
    assert result["power"]["grid"]["voltage"] == 245.9
    assert result["power"]["grid"]["current"] == 6.4
    assert result["power"]["grid"]["power"] == 1302
    assert result["power"]["grid"]["frequency"] == 50.04

    # power.battery
    assert result["power"]["battery"]["percent"] == 100
    assert result["power"]["battery"]["power"] == 10
    assert result["power"]["battery"]["temperature"] == 18.0

    # power.consumption
    assert result["power"]["consumption"]["power"] == 138

    # power.inverter
    assert result["power"]["inverter"]["temperature"] == 38.0
    assert result["power"]["inverter"]["power"] == 1440

    # today
    assert result["today"]["solar"] == 7.8  # e_pv1_day + e_pv2_day
    assert result["today"]["grid"]["import"] == 5.3
    assert result["today"]["grid"]["export"] == 3.5
    assert result["today"]["battery"]["charge"] == 4.1
    assert result["today"]["battery"]["discharge"] == 1.4
    assert result["today"]["consumption"] == 7.0


def test_transform_data_point_handles_missing_fields():
    result = transform_data_point(_TIMESTAMP, {"status": 1})

    assert result["status"] == "NORMAL"
    assert result["power"]["solar"]["power"] == 0
    assert result["power"]["grid"]["voltage"] == 0
    assert result["power"]["battery"]["percent"] == 0
    assert result["power"]["consumption"]["power"] == 0
    assert result["power"]["inverter"]["power"] == 0
    assert result["today"]["solar"] == 0.0
    assert result["today"]["grid"]["import"] == 0.0
    assert result["today"]["battery"]["charge"] == 0.0
    assert result["today"]["consumption"] == 0.0
