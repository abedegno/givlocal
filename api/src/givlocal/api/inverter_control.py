"""API routes for inverter settings read/write (mirrors GivEnergy Cloud API)."""

from __future__ import annotations

import json
import logging
import threading
import time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from givlocal.api.dependencies import require_auth, require_scope

logger = logging.getLogger(__name__)

# Per-serial last-write timestamps, protected by _write_lock. Caps writes at
# MIN_WRITE_INTERVAL seconds per inverter. Holding registers aren't infinitely
# rewritable; this prevents a misbehaving client from hammering the device.
MIN_WRITE_INTERVAL = 1.0
_last_write: dict[str, float] = {}
_write_lock = threading.Lock()

# All control endpoints can write holding registers or expose setting values,
# so the whole router requires a valid bearer token.
router = APIRouter(tags=["Inverter Control"], dependencies=[Depends(require_auth)])


def _throttle_check(serial: str) -> float | None:
    """Return None if write is allowed, else seconds the caller should wait."""
    now = time.monotonic()
    with _write_lock:
        last = _last_write.get(serial, 0.0)
        wait = MIN_WRITE_INTERVAL - (now - last)
        if wait > 0:
            return wait
        _last_write[serial] = now
        return None


def _audit_write(serial: str, setting_id: int, name: str, value, success: bool, message: str) -> None:
    """Append a record of this write to the events table."""
    from givlocal.main import app_state

    conn = app_state.app_db
    if conn is None:
        return
    payload = {"setting_id": setting_id, "name": name, "value": value, "success": success, "message": message}
    try:
        conn.execute(
            "INSERT INTO events (inverter_serial, timestamp, event_type, description, data) "
            "VALUES (?, datetime('now'), ?, ?, ?)",
            (serial, "setting_write", f"setting {setting_id} ({name}) -> {value}", json.dumps(payload, default=str)),
        )
        conn.commit()
    except Exception:
        logger.exception("Failed to record audit event for %s setting=%s", serial, setting_id)


class WriteSettingRequest(BaseModel):
    value: bool | int | str
    context: str | None = None


@router.get("/inverter/{serial}/settings")
async def list_inverter_settings(serial: str):
    from givlocal.main import app_state
    from givlocal.settings_map import list_settings

    inv_state = app_state.inverters.get(serial)
    if not inv_state:
        raise HTTPException(status_code=404, detail="Inverter not found")
    return {"data": list_settings(app_state.settings)}


@router.post("/inverter/{serial}/settings/{setting_id}/read")
async def read_inverter_setting(serial: str, setting_id: int):
    from givenergy_modbus_async.model.register import HR

    from givlocal.main import app_state
    from givlocal.settings_map import convert_from_register_value, get_hr_index, get_setting

    inv_state = app_state.inverters.get(serial)
    if not inv_state:
        raise HTTPException(status_code=404, detail="Inverter not found")
    setting = get_setting(app_state.settings, setting_id)
    if setting is None:
        raise HTTPException(status_code=404, detail="Setting not found")
    register_name = setting.get("register")
    register_value = None
    if register_name:
        register_value = inv_state.plant.inverter.get(register_name)
    if register_value is None:
        hr_idx = get_hr_index(setting)
        if hr_idx is not None:
            register_value = inv_state.plant.inverter.cache.get(HR(hr_idx))
    if register_value is None:
        return {"data": {"value": None}}
    display_value = convert_from_register_value(setting, int(register_value))
    return {"data": {"value": display_value}}


@router.post(
    "/inverter/{serial}/settings/{setting_id}/write",
    dependencies=[Depends(require_scope("write"))],
)
async def write_inverter_setting(serial: str, setting_id: int, body: WriteSettingRequest):
    from givenergy_modbus_async.pdu import WriteHoldingRegisterRequest

    from givlocal.main import app_state
    from givlocal.settings_map import convert_to_register_value, get_hr_index, get_setting, validate_setting_value

    inv_state = app_state.inverters.get(serial)
    if not inv_state:
        raise HTTPException(status_code=404, detail="Inverter not found")
    setting = get_setting(app_state.settings, setting_id)
    if setting is None:
        raise HTTPException(status_code=404, detail="Setting not found")
    if not validate_setting_value(setting, body.value):
        raise HTTPException(status_code=422, detail=f"Invalid value {body.value!r} for setting {setting_id}")
    wait = _throttle_check(serial)
    if wait is not None:
        raise HTTPException(
            status_code=429,
            detail=f"Too many writes to {serial}; retry in {wait:.2f}s",
        )
    hr_idx = get_hr_index(setting)
    if hr_idx is None:
        raise HTTPException(status_code=500, detail=f"No register mapping for setting '{setting['name']}'")
    register_value = convert_to_register_value(setting, body.value)
    request = WriteHoldingRegisterRequest(hr_idx, register_value)
    name = setting.get("name", "")
    try:
        await inv_state.client.execute([request], timeout=3.0, retries=1)
    except Exception as exc:
        logger.exception("Setting write failed for %s setting=%s", serial, setting_id)
        message = f"{type(exc).__name__}: write failed (see server logs)"
        _audit_write(serial, setting_id, name, body.value, success=False, message=message)
        return {"data": {"value": body.value, "success": False, "message": message}}
    _audit_write(serial, setting_id, name, body.value, success=True, message="Written Successfully")
    return {"data": {"value": body.value, "success": True, "message": "Written Successfully"}}
