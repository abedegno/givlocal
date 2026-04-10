"""Tests for settings_map module."""

from __future__ import annotations

import os

import pytest

from givlocal.settings_map import (
    convert_from_register_value,
    convert_to_register_value,
    load_settings_from_cloud_dump,
    resolve_register_name,
    resolve_setting_type,
    validate_setting_value,
)

CLOUD_DUMP_PATH = os.path.join(os.path.dirname(__file__), "..", "cloud-data", "settings.json")


@pytest.fixture
def settings():
    if not os.path.exists(CLOUD_DUMP_PATH):
        pytest.skip("cloud-data/settings.json not found")
    return load_settings_from_cloud_dump(CLOUD_DUMP_PATH)


# ---------------------------------------------------------------------------
# Name resolution tests (~15)
# ---------------------------------------------------------------------------


def test_resolve_ac_charge_start():
    assert resolve_register_name("AC Charge 1 Start Time") == "charge_slot_1_start"


def test_resolve_ac_charge_start_multi_digit():
    assert resolve_register_name("AC Charge 10 Start Time") == "charge_slot_10_start"


def test_resolve_ac_charge_end():
    assert resolve_register_name("AC Charge 2 End Time") == "charge_slot_2_end"


def test_resolve_ac_charge_upper_soc():
    assert resolve_register_name("AC Charge 1 Upper SOC % Limit") == "charge_target_soc_1"


def test_resolve_dc_discharge_start():
    assert resolve_register_name("DC Discharge 1 Start Time") == "discharge_slot_1_start"


def test_resolve_dc_discharge_end():
    assert resolve_register_name("DC Discharge 2 End Time") == "discharge_slot_2_end"


def test_resolve_dc_discharge_lower_soc():
    assert resolve_register_name("DC Discharge 1 Lower SOC % Limit") == "discharge_target_soc_1"


def test_resolve_enable_eco_mode():
    assert resolve_register_name("Enable Eco Mode") == "eco_mode"


def test_resolve_ac_charge_enable():
    assert resolve_register_name("AC Charge Enable") == "enable_charge"


def test_resolve_enable_dc_discharge():
    assert resolve_register_name("Enable DC Discharge") == "enable_discharge"


def test_resolve_battery_reserve():
    assert resolve_register_name("Battery Reserve % Limit") == "battery_soc_reserve"


def test_resolve_battery_cutoff():
    assert resolve_register_name("Battery Cutoff % Limit") == "battery_discharge_min_power_reserve"


def test_resolve_battery_charge_power():
    assert resolve_register_name("Battery Charge Power") == "battery_charge_limit"


def test_resolve_battery_discharge_power():
    assert resolve_register_name("Battery Discharge Power") == "battery_discharge_limit"


def test_resolve_ac_charge_upper_limit():
    assert resolve_register_name("AC Charge Upper % Limit") == "charge_target_soc"


def test_resolve_active_power_rate():
    assert resolve_register_name("Inverter Max Output Active Power") == "active_power_rate"


def test_resolve_inverter_reboot():
    assert resolve_register_name("Restart Inverter") == "inverter_reboot"


def test_resolve_pause_battery_start():
    assert resolve_register_name("Pause Battery Start Time") == "battery_pause_slot_1_start"


def test_resolve_pause_battery_end():
    assert resolve_register_name("Pause Battery End Time") == "battery_pause_slot_1_end"


def test_resolve_pause_battery_mode():
    assert resolve_register_name("Pause Battery") == "battery_pause_mode"


def test_resolve_inverter_charge_pct():
    assert resolve_register_name("Inverter Charge Power Percentage") == "battery_charge_limit_ac"


def test_resolve_inverter_discharge_pct():
    assert resolve_register_name("Inverter Discharge Power Percentage") == "battery_discharge_limit_ac"


def test_resolve_enable_eps():
    assert resolve_register_name("Enable EPS") == "enable_ups_mode"


def test_resolve_unknown_returns_none():
    assert resolve_register_name("Some Unknown Setting") is None


# ---------------------------------------------------------------------------
# Type inference tests (~5)
# ---------------------------------------------------------------------------


def test_resolve_type_boolean_rule():
    assert resolve_setting_type("Value must be either true or false", ["boolean"]) == "bool"


def test_resolve_type_time_rule():
    assert resolve_setting_type("Value format should be HH:mm.", ["date_format:H:i"]) == "time"


def test_resolve_type_int_between():
    assert resolve_setting_type("Value must be between 0 and 100", ["between:0,100"]) == "int"


def test_resolve_type_int_in():
    assert resolve_setting_type("Value must be one of: 0, 1, 2", ["in:0,1,2"]) == "int"


def test_resolve_type_fallback_int():
    assert resolve_setting_type("Value can only be 100", ["writeonly", "exact:100"]) == "int"


# ---------------------------------------------------------------------------
# Load from cloud dump tests (~3)
# ---------------------------------------------------------------------------


def test_load_returns_dict(settings):
    assert isinstance(settings, dict)
    assert len(settings) > 10


def test_load_known_bool_setting(settings):
    # ID 17: Enable AC Charge Upper % Limit -> bool -> enable_charge_target
    s = settings.get(17)
    assert s is not None
    assert s["name"] == "Enable AC Charge Upper % Limit"
    assert s["type"] == "bool"
    assert s["register"] == "enable_charge_target"


def test_load_known_time_setting(settings):
    # ID 64: AC Charge 1 Start Time -> time -> charge_slot_1_start
    s = settings.get(64)
    assert s is not None
    assert s["type"] == "time"
    assert s["register"] == "charge_slot_1_start"


def test_load_known_int_setting(settings):
    # ID 71: Battery Reserve % Limit -> int -> battery_soc_reserve
    s = settings.get(71)
    assert s is not None
    assert s["type"] == "int"
    assert s["register"] == "battery_soc_reserve"


# ---------------------------------------------------------------------------
# Validation tests (~4)
# ---------------------------------------------------------------------------


def test_validate_bool_true_false():
    setting = {"type": "bool", "validation_rules": ["boolean"]}
    assert validate_setting_value(setting, True) is True
    assert validate_setting_value(setting, False) is True
    assert validate_setting_value(setting, "yes") is False
    assert validate_setting_value(setting, 1) is False


def test_validate_time():
    setting = {"type": "time", "validation_rules": ["date_format:H:i"]}
    assert validate_setting_value(setting, "23:30") is True
    assert validate_setting_value(setting, "00:00") is True
    assert validate_setting_value(setting, "25:00") is False
    assert validate_setting_value(setting, "abc") is False
    assert validate_setting_value(setting, "23:60") is False


def test_validate_int_range():
    setting = {"type": "int", "validation_rules": ["between:4,100"]}
    assert validate_setting_value(setting, 50) is True
    assert validate_setting_value(setting, 4) is True
    assert validate_setting_value(setting, 100) is True
    assert validate_setting_value(setting, 3) is False
    assert validate_setting_value(setting, 101) is False


def test_validate_int_in():
    setting = {"type": "int", "validation_rules": ["in:0,1,2"]}
    assert validate_setting_value(setting, 0) is True
    assert validate_setting_value(setting, 2) is True
    assert validate_setting_value(setting, 3) is False


# ---------------------------------------------------------------------------
# Conversion tests (~3)
# ---------------------------------------------------------------------------


def test_convert_time_to_register():
    setting = {"type": "time", "validation_rules": ["date_format:H:i"]}
    assert convert_to_register_value(setting, "23:30") == 2330
    assert convert_to_register_value(setting, "05:30") == 530
    assert convert_to_register_value(setting, "00:00") == 0


def test_convert_bool_to_register():
    setting = {"type": "bool", "validation_rules": ["boolean"]}
    assert convert_to_register_value(setting, True) == 1
    assert convert_to_register_value(setting, False) == 0


def test_convert_from_register():
    time_setting = {"type": "time", "validation_rules": ["date_format:H:i"]}
    bool_setting = {"type": "bool", "validation_rules": ["boolean"]}
    int_setting = {"type": "int", "validation_rules": ["between:0,100"]}

    assert convert_from_register_value(time_setting, 2330) == "23:30"
    assert convert_from_register_value(time_setting, 530) == "05:30"
    assert convert_from_register_value(bool_setting, 1) is True
    assert convert_from_register_value(bool_setting, 0) is False
    assert convert_from_register_value(int_setting, 50) == 50
