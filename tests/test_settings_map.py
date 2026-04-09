"""Tests for settings_map module."""

import os

import pytest

from givenergy_local.settings_map import (
    convert_from_register_value,
    convert_to_register_value,
    get_setting,
    list_settings,
    load_settings_map,
    validate_setting_value,
)

SETTINGS_DIR = os.path.join(os.path.dirname(__file__), "..", "settings")


@pytest.fixture
def settings_map():
    return load_settings_map(SETTINGS_DIR)


# --- Test 1: load_settings_map ---

def test_load_settings_map(settings_map):
    assert "2001" in settings_map
    setting_17 = settings_map["2001"][17]
    assert setting_17["name"] == "Enable AC Charge Upper % Limit"
    assert setting_17["register"] == "enable_charge_target"
    assert setting_17["type"] == "bool"


# --- Test 2: get_setting_by_id ---

def test_get_setting_by_id(settings_map):
    setting = get_setting(settings_map, "2001", 64)
    assert setting is not None
    assert setting["name"] == "AC Charge 1 Start Time"
    assert setting["register"] == "charge_slot_1_start"
    assert setting["type"] == "time"


# --- Test 3: get_setting_unknown_id ---

def test_get_setting_unknown_id(settings_map):
    result = get_setting(settings_map, "2001", 99999)
    assert result is None


# --- Test 4: list_settings_for_model ---

def test_list_settings_for_model(settings_map):
    settings = list_settings(settings_map, "2001")
    assert len(settings) > 20
    for s in settings:
        assert "id" in s
        assert "name" in s
        assert "validation" in s


# --- Test 5: validate_bool_setting ---

def test_validate_bool_setting(settings_map):
    setting = get_setting(settings_map, "2001", 17)  # bool type
    assert validate_setting_value(setting, True) is True
    assert validate_setting_value(setting, False) is True
    assert validate_setting_value(setting, "yes") is False
    assert validate_setting_value(setting, 1) is False


# --- Test 6: validate_int_setting ---

def test_validate_int_setting(settings_map):
    setting = get_setting(settings_map, "2001", 71)  # int range:4,100
    assert validate_setting_value(setting, 50) is True
    assert validate_setting_value(setting, 4) is True
    assert validate_setting_value(setting, 100) is True
    assert validate_setting_value(setting, 3) is False
    assert validate_setting_value(setting, 101) is False


# --- Test 7: validate_time_setting ---

def test_validate_time_setting(settings_map):
    setting = get_setting(settings_map, "2001", 64)  # time type
    assert validate_setting_value(setting, "23:30") is True
    assert validate_setting_value(setting, "00:00") is True
    assert validate_setting_value(setting, "25:00") is False
    assert validate_setting_value(setting, "abc") is False
    assert validate_setting_value(setting, "23:60") is False


# --- Test 8: convert_time_to_register_value ---

def test_convert_time_to_register_value(settings_map):
    time_setting = get_setting(settings_map, "2001", 64)
    assert convert_to_register_value(time_setting, "23:30") == 2330
    assert convert_to_register_value(time_setting, "05:30") == 530
    assert convert_to_register_value(time_setting, "00:00") == 0


# --- Test 9: convert_bool_to_register_value ---

def test_convert_bool_to_register_value(settings_map):
    bool_setting = get_setting(settings_map, "2001", 17)
    assert convert_to_register_value(bool_setting, True) == 1
    assert convert_to_register_value(bool_setting, False) == 0


# --- Test 10: convert_register_to_display_value ---

def test_convert_register_to_display_value(settings_map):
    time_setting = get_setting(settings_map, "2001", 64)
    bool_setting = get_setting(settings_map, "2001", 17)
    int_setting = get_setting(settings_map, "2001", 71)

    assert convert_from_register_value(time_setting, 2330) == "23:30"
    assert convert_from_register_value(time_setting, 530) == "05:30"
    assert convert_from_register_value(bool_setting, 1) is True
    assert convert_from_register_value(bool_setting, 0) is False
    assert convert_from_register_value(int_setting, 50) == 50


# --- Test 11: hr_override present in list_settings ---

def test_hr_override_in_list_settings(settings_map):
    settings = list_settings(settings_map, "2001")
    # setting 56 (Enable DC Discharge) has hr_override: 59
    setting_56 = next((s for s in settings if s["id"] == 56), None)
    assert setting_56 is not None
    assert setting_56.get("hr_override") == 59
    # setting 64 has no hr_override
    setting_64 = next((s for s in settings if s["id"] == 64), None)
    assert setting_64 is not None
    assert "hr_override" not in setting_64
