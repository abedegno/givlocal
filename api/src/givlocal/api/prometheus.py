"""Prometheus metrics endpoint for external scraping."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import PlainTextResponse

router = APIRouter()


async def _optional_auth(authorization: str = Header(None)) -> None:
    """Enforce bearer auth on /metrics iff config.prometheus_auth_required."""
    from givlocal.main import app_state

    if not app_state.prometheus_auth_required:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = authorization[7:]
    if not app_state.token_store.validate(token):
        raise HTTPException(status_code=401, detail="Invalid API token")


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

METRIC_HELP: dict[str, str] = {
    "givenergy_solar_power_watts": "Total PV generation (sum of both strings), W",
    "givenergy_pv1_power_watts": "PV string 1 instantaneous power, W",
    "givenergy_pv2_power_watts": "PV string 2 instantaneous power, W",
    "givenergy_grid_power_watts": "Grid power (positive = export, negative = import), W",
    "givenergy_battery_power_watts": "Battery power (positive = discharging), W",
    "givenergy_battery_percent": "Battery state of charge, %",
    "givenergy_consumption_watts": "House load demand, W",
    "givenergy_inverter_power_watts": "Inverter AC output power, W",
    "givenergy_ac_voltage": "Grid AC voltage, V",
    "givenergy_ac_frequency_hz": "Grid AC frequency, Hz",
    "givenergy_battery_voltage": "Battery pack voltage, V",
    "givenergy_inverter_temp_celsius": "Inverter heatsink temperature, °C",
    "givenergy_battery_temp_celsius": "Battery temperature, °C",
}


@router.get("/metrics", response_class=PlainTextResponse, dependencies=[Depends(_optional_auth)])
async def prometheus_metrics():
    """Expose current inverter state in Prometheus format.

    Auth is required iff `prometheus_auth_required: true` in config (the
    safe default). Set to `false` to allow unauthenticated scraping from
    trusted monitoring hosts.
    """
    from givlocal.main import app_state

    lines: list[str] = []
    # Emit HELP/TYPE once per metric at the top so scrapers can annotate.
    for metric_name, _registers in ((m[0], m[1:]) for m in METRICS):
        help_text = METRIC_HELP.get(metric_name, metric_name)
        lines.append(f"# HELP {metric_name} {help_text}")
        lines.append(f"# TYPE {metric_name} gauge")

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
