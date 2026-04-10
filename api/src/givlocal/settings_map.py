"""Settings map: Auto-resolution from cloud API dump JSON."""

from __future__ import annotations

import json
import re
from typing import Any

# SettingsById: setting_id -> setting_dict
SettingsById = dict[int, dict]


def resolve_register_name(cloud_name: str) -> str | None:
    """Pattern match a cloud setting name to a Modbus register name."""
    # Numbered slot patterns (N is one or more digits)
    m = re.fullmatch(r"AC Charge (\d+) Start Time", cloud_name)
    if m:
        return f"charge_slot_{m.group(1)}_start"

    m = re.fullmatch(r"AC Charge (\d+) End Time", cloud_name)
    if m:
        return f"charge_slot_{m.group(1)}_end"

    m = re.fullmatch(r"AC Charge (\d+) Upper SOC.*", cloud_name)
    if m:
        return f"charge_target_soc_{m.group(1)}"

    m = re.fullmatch(r"DC Discharge (\d+) Start Time", cloud_name)
    if m:
        return f"discharge_slot_{m.group(1)}_start"

    m = re.fullmatch(r"DC Discharge (\d+) End Time", cloud_name)
    if m:
        return f"discharge_slot_{m.group(1)}_end"

    m = re.fullmatch(r"DC Discharge (\d+) Lower SOC.*", cloud_name)
    if m:
        return f"discharge_target_soc_{m.group(1)}"

    # Exact/prefix matches
    if cloud_name == "Enable Eco Mode":
        return "eco_mode"
    if cloud_name.startswith("Enable AC Charge Upper"):
        return "enable_charge_target"
    if cloud_name == "AC Charge Enable":
        return "enable_charge"
    if cloud_name == "Enable DC Discharge":
        return "enable_discharge"
    if cloud_name == "Battery Reserve % Limit":
        return "battery_soc_reserve"
    if cloud_name == "Battery Cutoff % Limit":
        return "battery_discharge_min_power_reserve"
    if cloud_name.endswith("Battery Charge Power"):
        return "battery_charge_limit"
    if cloud_name.endswith("Battery Discharge Power"):
        return "battery_discharge_limit"
    if cloud_name.endswith("AC Charge Upper % Limit"):
        return "charge_target_soc"
    if cloud_name == "Inverter Max Output Active Power":
        return "active_power_rate"
    if cloud_name == "Restart Inverter":
        return "inverter_reboot"
    if cloud_name == "Pause Battery Start" or cloud_name == "Pause Battery Start Time":
        return "battery_pause_slot_1_start"
    if cloud_name == "Pause Battery End" or cloud_name == "Pause Battery End Time":
        return "battery_pause_slot_1_end"
    if cloud_name == "Pause Battery":
        return "battery_pause_mode"
    if cloud_name == "Inverter Charge Power Percentage":
        return "battery_charge_limit_ac"
    if cloud_name == "Inverter Discharge Power Percentage":
        return "battery_discharge_limit_ac"
    if cloud_name == "Enable EPS":
        return "enable_ups_mode"

    return None


def resolve_setting_type(validation: str, validation_rules: list[str]) -> str:
    """Infer setting type from cloud validation rules."""
    for rule in validation_rules:
        if rule == "boolean":
            return "bool"
        if rule.startswith("date_format"):
            return "time"
    if "true or false" in validation.lower():
        return "bool"
    if "HH:mm" in validation:
        return "time"
    return "int"


def load_settings_from_cloud_dump(json_path: str) -> SettingsById:
    """Load settings from a cloud API dump JSON file.

    Handles both ``{"data": [...]}`` and bare ``[...]`` formats.
    Returns a dict keyed by setting ID with resolved register name and type.
    """
    with open(json_path) as f:
        raw = json.load(f)

    if isinstance(raw, dict):
        items = raw.get("data", [])
    else:
        items = raw

    result: SettingsById = {}
    for item in items:
        setting_id = int(item["id"])
        name = item.get("name", "")
        validation = item.get("validation", "")
        validation_rules = item.get("validation_rules", [])

        register = resolve_register_name(name)
        setting_type = resolve_setting_type(validation, validation_rules)

        result[setting_id] = {
            "id": setting_id,
            "name": name,
            "register": register,
            "type": setting_type,
            "validation": validation,
            "validation_rules": validation_rules,
        }

    return result


def get_setting(settings: SettingsById, setting_id: int) -> dict | None:
    """Look up a single setting by ID."""
    return settings.get(int(setting_id))


def list_settings(settings: SettingsById) -> list[dict]:
    """Return all settings in cloud API format (id, name, validation, validation_rules)."""
    result = []
    for setting_id in sorted(settings.keys()):
        s = settings[setting_id]
        result.append(
            {
                "id": s["id"],
                "name": s["name"],
                "validation": s.get("validation", ""),
                "validation_rules": s.get("validation_rules", []),
            }
        )
    return result


def get_hr_index(setting: dict) -> int | None:
    """Look up the HR index for a setting's register name from BaseInverter.REGISTER_LUT."""
    register = setting.get("register")
    if not register:
        return None
    try:
        from givenergy_modbus_async.model.inverter import BaseInverter

        lut = BaseInverter.REGISTER_LUT
        rd = lut.get(register)
        if rd is None:
            return None
        registers = rd.registers
        if not registers:
            return None
        return registers[0]._idx
    except Exception:
        return None


def validate_setting_value(setting: dict, value: Any) -> bool:
    """Validate a value against a setting's type and validation_rules."""
    setting_type = setting.get("type", "")
    validation_rules = setting.get("validation_rules", [])

    if setting_type == "bool":
        return isinstance(value, bool)

    if setting_type == "time":
        return _validate_time(value)

    if setting_type == "int":
        if not isinstance(value, int) or isinstance(value, bool):
            return False
        for rule in validation_rules:
            if rule.startswith("between:"):
                parts = rule[len("between:") :].split(",")
                lo, hi = int(parts[0]), int(parts[1])
                if not (lo <= value <= hi):
                    return False
            elif rule.startswith("in:"):
                allowed = [int(v.strip()) for v in rule[len("in:") :].split(",")]
                if value not in allowed:
                    return False
        return True

    return True


def _validate_time(value: Any) -> bool:
    """Validate a time string in HH:MM format."""
    if not isinstance(value, str):
        return False
    match = re.fullmatch(r"(\d{2}):(\d{2})", value)
    if not match:
        return False
    hours, minutes = int(match.group(1)), int(match.group(2))
    return 0 <= hours <= 23 and 0 <= minutes <= 59


def convert_to_register_value(setting: dict, value: Any) -> int:
    """Convert a display value to a register integer.

    - bool: True -> 1, False -> 0
    - time: "23:30" -> 2330, "05:30" -> 530
    - int: returned as-is
    """
    setting_type = setting.get("type", "")

    if setting_type == "bool":
        return 1 if value else 0

    if setting_type == "time":
        if not isinstance(value, str):
            raise ValueError(f"Expected time string, got {type(value)}")
        match = re.fullmatch(r"(\d{2}):(\d{2})", value)
        if not match:
            raise ValueError(f"Invalid time format: {value!r}")
        hours, minutes = int(match.group(1)), int(match.group(2))
        return hours * 100 + minutes

    if setting_type == "int":
        return int(value)

    raise ValueError(f"Unknown setting type: {setting_type!r}")


def convert_from_register_value(setting: dict, register_value: int) -> Any:
    """Convert a register integer to a display value.

    - bool: 1 -> True, 0 -> False
    - time: 2330 -> "23:30", 530 -> "05:30"
    - int: returned as-is
    """
    setting_type = setting.get("type", "")

    if setting_type == "bool":
        return bool(register_value)

    if setting_type == "time":
        hours = register_value // 100
        minutes = register_value % 100
        return f"{hours:02d}:{minutes:02d}"

    if setting_type == "int":
        return register_value

    raise ValueError(f"Unknown setting type: {setting_type!r}")
