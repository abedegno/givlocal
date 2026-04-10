"""Transform raw register values into the GivEnergy Cloud data-point shape."""

from datetime import datetime, timezone

_STATUS_MAP = {0: "WAITING", 1: "NORMAL", 2: "WARNING", 3: "FAULT", 4: "UPDATING"}


def _get(data: dict, key: str, default=0):
    """Return data[key] coerced to a number, or default if missing/None/non-numeric."""
    val = data.get(key)
    if val is None:
        return default
    if isinstance(val, str):
        try:
            return float(val)
        except (ValueError, TypeError):
            return default
    return val


def transform_data_point(timestamp: int, data: dict) -> dict:
    """Convert a unix timestamp and register dict to the cloud data-point JSON shape."""
    time_str = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    status_raw = data.get("status")
    status_int = int(status_raw) if status_raw is not None else 0
    status = _STATUS_MAP.get(status_int, "UNKNOWN")

    p_pv1 = _get(data, "p_pv1")
    p_pv2 = _get(data, "p_pv2")

    e_pv1_day = _get(data, "e_pv1_day", 0.0)
    e_pv2_day = _get(data, "e_pv2_day", 0.0)

    return {
        "time": time_str,
        "status": status,
        "power": {
            "solar": {
                "power": p_pv1 + p_pv2,
                "arrays": [
                    {
                        "array": 1,
                        "voltage": _get(data, "v_pv1"),
                        "current": _get(data, "i_pv1"),
                        "power": p_pv1,
                    },
                    {
                        "array": 2,
                        "voltage": _get(data, "v_pv2"),
                        "current": _get(data, "i_pv2"),
                        "power": p_pv2,
                    },
                ],
            },
            "grid": {
                "voltage": _get(data, "v_ac1"),
                "current": _get(data, "i_ac1"),
                "power": _get(data, "p_grid_out"),
                "frequency": _get(data, "f_ac1"),
            },
            "battery": {
                "percent": _get(data, "battery_percent"),
                "power": _get(data, "p_battery"),
                "temperature": _get(data, "temp_battery"),
            },
            "consumption": {
                "power": _get(data, "p_load_demand"),
            },
            "inverter": {
                "temperature": _get(data, "temp_inverter_heatsink"),
                "power": _get(data, "p_inverter_out"),
                "output_voltage": _get(data, "v_eps_backup"),
                "output_frequency": _get(data, "f_eps_backup"),
                "eps_power": 0,
            },
        },
        "today": {
            "solar": round(e_pv1_day + e_pv2_day, 2),
            "grid": {
                "import": _get(data, "e_grid_in_day", 0.0),
                "export": _get(data, "e_grid_out_day", 0.0),
            },
            "battery": {
                "charge": _get(data, "e_battery_charge_today", 0.0),
                "discharge": _get(data, "e_battery_discharge_today", 0.0),
            },
            "consumption": _get(data, "e_inverter_out_day", 0.0),
        },
    }
