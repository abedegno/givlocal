"""Transform an Inverter model into the GivEnergy Cloud /meter-data-latest shape."""

from datetime import timezone


def transform_meter_data(inv) -> dict:
    """Convert an Inverter model object to the cloud /meter-data-latest JSON shape."""
    system_time = inv.get("system_time")
    if system_time is not None:
        time_str = system_time.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    else:
        time_str = None

    e_pv1_day = inv.get("e_pv1_day") or 0.0
    e_pv2_day = inv.get("e_pv2_day") or 0.0

    e_battery_charge_total = inv.get("e_battery_charge_total_2")
    e_battery_discharge_total = inv.get("e_battery_discharge_total_2")

    return {
        "time": time_str,
        "today": {
            "solar": round(e_pv1_day + e_pv2_day, 2),
            "grid": {
                "import": inv.get("e_grid_in_day"),
                "export": inv.get("e_grid_out_day"),
            },
            "battery": {
                "charge": inv.get("e_battery_charge_today"),
                "discharge": inv.get("e_battery_discharge_today"),
            },
            "consumption": inv.get("e_inverter_out_day"),
        },
        "total": {
            "solar": inv.get("e_pv_total"),
            "grid": {
                "import": inv.get("e_grid_in_total"),
                "export": inv.get("e_grid_out_total"),
            },
            "battery": {
                "charge": e_battery_charge_total,
                "discharge": e_battery_discharge_total,
            },
            "consumption": inv.get("e_inverter_out_total"),
        },
    }
