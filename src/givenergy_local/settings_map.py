"""Settings map: Cloud API setting ID -> Modbus register mapping."""

from __future__ import annotations

import os
import re
from typing import Any

import yaml

# SettingsMap: model_code -> {setting_id -> setting_dict}
SettingsMap = dict[str, dict[int, dict]]


def load_settings_map(settings_dir: str) -> SettingsMap:
    """Load all YAML files from settings_dir/models/, return dict keyed by model code."""
    models_dir = os.path.join(settings_dir, "models")
    result: SettingsMap = {}

    if not os.path.isdir(models_dir):
        return result

    for filename in os.listdir(models_dir):
        if not filename.endswith(".yaml") and not filename.endswith(".yml"):
            continue
        filepath = os.path.join(models_dir, filename)
        with open(filepath) as f:
            data = yaml.safe_load(f)

        model_code = str(data["model"])
        settings_raw = data.get("settings", {})

        # Ensure keys are ints
        settings: dict[int, dict] = {}
        for k, v in settings_raw.items():
            settings[int(k)] = v

        result[model_code] = settings

    return result


def get_setting(settings_map: SettingsMap, model: str, setting_id: int) -> dict | None:
    """Lookup a single setting by model code and cloud API setting ID."""
    model_settings = settings_map.get(str(model))
    if model_settings is None:
        return None
    return model_settings.get(int(setting_id))


def list_settings(settings_map: SettingsMap, model: str) -> list[dict]:
    """Return all settings for a model in cloud API format."""
    model_settings = settings_map.get(str(model), {})
    result = []
    for setting_id, setting in sorted(model_settings.items()):
        validation_rules = _parse_validation_rules(setting.get("validation", ""))
        result.append(
            {
                "id": setting_id,
                "name": setting.get("name", ""),
                "validation": setting.get("validation", ""),
                "validation_rules": validation_rules,
                "register": setting.get("register", ""),
                "type": setting.get("type", ""),
                **({"hr_override": setting["hr_override"]} if "hr_override" in setting else {}),
            }
        )
    return result


def _parse_validation_rules(validation: str) -> dict:
    """Parse validation string into structured rules dict."""
    if not validation:
        return {}

    if validation == "time":
        return {"type": "time"}

    if validation.startswith("range:"):
        parts = validation[len("range:") :].split(",")
        return {"type": "range", "min": int(parts[0]), "max": int(parts[1])}

    if validation.startswith("in:"):
        raw_values = validation[len("in:") :].split(",")
        # Try to parse as ints; fall back to strings
        values: list[Any] = []
        for v in raw_values:
            v = v.strip()
            if v in ("true", "false"):
                values.append(v == "true")
            else:
                try:
                    values.append(int(v))
                except ValueError:
                    values.append(v)
        return {"type": "in", "values": values}

    return {"raw": validation}


def validate_setting_value(setting: dict, value: Any) -> bool:
    """Validate a value against a setting's type and rules."""
    setting_type = setting.get("type", "")
    validation = setting.get("validation", "")

    if setting_type == "bool":
        return isinstance(value, bool)

    if setting_type == "time":
        return _validate_time(value)

    if setting_type == "int":
        if not isinstance(value, int) or isinstance(value, bool):
            return False
        if validation.startswith("range:"):
            parts = validation[len("range:") :].split(",")
            lo, hi = int(parts[0]), int(parts[1])
            return lo <= value <= hi
        if validation.startswith("in:"):
            allowed = [int(v.strip()) for v in validation[len("in:") :].split(",")]
            return value in allowed
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
