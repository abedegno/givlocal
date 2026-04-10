"""Prometheus metrics endpoint for external scraping."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter()

METRICS = [
    ("givenergy_solar_power_watts", "p_pv1", "p_pv2"),  # sum of two
    ("givenergy_pv1_power_watts", "p_pv1"),
    ("givenergy_pv2_power_watts", "p_pv2"),
    ("givenergy_grid_power_watts", "p_grid_out"),
    ("givenergy_battery_power_watts", "p_battery"),
    ("givenergy_battery_percent", "battery_percent"),
    ("givenergy_consumption_watts", "p_load_demand"),
    ("givenergy_inverter_power_watts", "p_inverter_out"),
    ("givenergy_ac_voltage", "v_ac1"),
    ("givenergy_ac_frequency_hz", "f_ac1"),
    ("givenergy_battery_voltage", "v_battery"),
    ("givenergy_inverter_temp_celsius", "temp_inverter_heatsink"),
    ("givenergy_battery_temp_celsius", "temp_battery"),
]


@router.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics():
    """Expose current inverter state in Prometheus format. No auth required."""
    from givlocal.main import app_state

    lines = []
    for serial, inv_state in app_state.inverters.items():
        inverter = inv_state.plant.inverter
        for entry in METRICS:
            metric_name = entry[0]
            registers = entry[1:]
            if len(registers) == 2:
                v1 = inverter.get(registers[0]) or 0
                v2 = inverter.get(registers[1]) or 0
                value = v1 + v2
            else:
                raw = inverter.get(registers[0])
                value = raw if raw is not None else 0
            lines.append(f'{metric_name}{{serial="{serial}"}} {value}')

    return "\n".join(lines) + "\n" if lines else ""
