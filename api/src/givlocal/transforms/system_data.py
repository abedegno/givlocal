"""Transform an Inverter model into the GivEnergy Cloud /system-data-latest shape."""

from datetime import timezone

_STATUS_MAP = {0: "Waiting", 1: "Normal", 2: "Warning", 3: "Fault", 4: "Updating"}


def transform_system_data(inv) -> dict:
    """Convert an Inverter model object to the cloud /system-data-latest JSON shape."""
    system_time = inv.get("system_time")
    if system_time is not None:
        time_str = system_time.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    else:
        time_str = None

    status_raw = inv.get("status")
    status_int = int(status_raw) if status_raw is not None else 0
    status = _STATUS_MAP.get(status_int, "Unknown")

    p_pv1 = inv.get("p_pv1") or 0
    p_pv2 = inv.get("p_pv2") or 0

    return {
        "time": time_str,
        "status": status,
        "solar": {
            "power": p_pv1 + p_pv2,
            "arrays": [
                {
                    "array": 1,
                    "voltage": inv.get("v_pv1"),
                    "current": inv.get("i_pv1"),
                    "power": p_pv1,
                },
                {
                    "array": 2,
                    "voltage": inv.get("v_pv2"),
                    "current": inv.get("i_pv2"),
                    "power": p_pv2,
                },
            ],
        },
        "grid": {
            "voltage": inv.get("v_ac1"),
            "current": inv.get("i_ac1"),
            "power": inv.get("p_grid_out"),
            "frequency": inv.get("f_ac1"),
        },
        "battery": {
            "percent": inv.get("battery_percent"),
            "power": inv.get("p_battery"),
            "temperature": inv.get("temp_battery"),
        },
        "inverter": {
            "temperature": inv.get("temp_inverter_heatsink"),
            "power": inv.get("p_inverter_out"),
            "output_voltage": inv.get("v_eps_backup"),
            "output_frequency": inv.get("f_eps_backup"),
            "eps_power": 0,
        },
        "consumption": inv.get("p_load_demand"),
    }
