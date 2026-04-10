"""API routes for inverter data (system data and meter data)."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from givlocal.api.dependencies import require_auth
from givlocal.api.schemas import DataResponse
from givlocal.transforms.data_point import transform_data_point
from givlocal.transforms.meter_data import transform_meter_data
from givlocal.transforms.system_data import transform_system_data

router = APIRouter(tags=["Inverter Data"])


@router.get(
    "/inverter/{inverter_serial_number}/system-data-latest",
    dependencies=[Depends(require_auth)],
)
async def system_data_latest(inverter_serial_number: str):
    """Transform current register cache to cloud JSON format."""
    from givlocal.main import app_state

    inv_state = app_state.inverters.get(inverter_serial_number)
    if not inv_state:
        raise HTTPException(status_code=404, detail="Inverter not found")

    result = transform_system_data(inv_state.plant.inverter)
    return DataResponse(data=result)


@router.get(
    "/inverter/{inverter_serial_number}/meter-data-latest",
    dependencies=[Depends(require_auth)],
)
async def meter_data_latest(inverter_serial_number: str):
    """Transform current register cache to cloud meter data JSON format."""
    from givlocal.main import app_state

    inv_state = app_state.inverters.get(inverter_serial_number)
    if not inv_state:
        raise HTTPException(status_code=404, detail="Inverter not found")

    result = transform_meter_data(inv_state.plant.inverter)
    return DataResponse(data=result)


@router.get(
    "/inverter/{serial}/data-points/{date_str}",
    dependencies=[Depends(require_auth)],
)
async def data_points(
    serial: str,
    date_str: str,
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=15, ge=1),
):
    """Return historical data points for a given date (YYYY-MM-DD), paginated."""
    from givlocal.main import app_state

    try:
        d = date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format, expected YYYY-MM-DD")

    start_dt = datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=timezone.utc)
    end_dt = datetime(d.year, d.month, d.day, 23, 59, 59, tzinfo=timezone.utc)
    start_ts = int(start_dt.timestamp())
    end_ts = int(end_dt.timestamp())

    rows = app_state.metrics_store.query_data_points(serial, start_ts, end_ts)
    items = [transform_data_point(row["timestamp"], json.loads(row["data"])) for row in rows]

    total = len(items)
    start_idx = (page - 1) * pageSize
    page_items = items[start_idx : start_idx + pageSize]

    return {
        "data": page_items,
        "meta": {
            "current_page": page,
            "total": total,
            "per_page": pageSize,
        },
    }


@router.get(
    "/inverter/{serial}/events",
    dependencies=[Depends(require_auth)],
)
async def inverter_events(
    serial: str,
    cleared: bool = Query(default=False),
    start: Optional[str] = Query(default=None),
    end: Optional[str] = Query(default=None),
):
    """Return fault events for the given inverter serial."""
    from givlocal.main import app_state

    conn = app_state.token_store._conn

    query = (
        "SELECT id, inverter_serial, timestamp, event_type, description, cleared_at"
        " FROM events WHERE inverter_serial = ?"
    )
    params: list = [serial]

    if not cleared:
        query += " AND cleared_at IS NULL"

    if start:
        query += " AND timestamp >= ?"
        params.append(start)

    if end:
        query += " AND timestamp <= ?"
        params.append(end)

    query += " ORDER BY timestamp DESC"

    rows = conn.execute(query, params).fetchall()
    data = [
        {
            "id": row[0],
            "inverter_serial": row[1],
            "timestamp": row[2],
            "event_type": row[3],
            "description": row[4],
            "cleared_at": row[5],
        }
        for row in rows
    ]
    return {"data": data}


@router.get(
    "/inverter/{serial}/health",
    dependencies=[Depends(require_auth)],
)
async def inverter_health(serial: str):
    """Return health checks derived from live inverter data."""
    from givlocal.main import app_state

    inv_state = app_state.inverters.get(serial)
    if not inv_state:
        raise HTTPException(status_code=404, detail="Inverter not found")

    inverter = inv_state.plant.inverter

    def _val(attr: str, default=0):
        v = getattr(inverter, attr, None)
        if v is None:
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    def _check(name: str, attr: str, unit: str, low=None, high=None) -> dict:
        value = _val(attr)
        if value is None:
            status = "unknown"
        elif (low is not None and value < low) or (high is not None and value > high):
            status = "warning"
        else:
            status = "ok"
        return {"name": name, "value": value, "status": status, "unit": unit}

    checks = [
        _check("Import/Export Power", "p_grid_out", "W"),
        _check("Grid Voltage", "v_ac1", "V", low=215, high=260),
        _check("Battery Voltage", "v_battery", "V", low=40, high=60),
        _check("Grid Frequency", "f_ac1", "Hz", low=49.5, high=50.5),
        _check("Inverter Temperature", "temp_inverter_heatsink", "°C", high=60),
        _check("Battery Temperature", "temp_battery", "°C", low=5, high=45),
        _check("Battery Percent", "battery_percent", "%", low=10),
        _check("Solar Generation", "p_pv1", "W"),
        _check("Consumption", "p_load_demand", "W"),
    ]

    return DataResponse(data={"checks": checks})
