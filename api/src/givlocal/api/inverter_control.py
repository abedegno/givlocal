"""API routes for inverter settings read/write (mirrors GivEnergy Cloud API)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from givlocal.api.dependencies import require_auth

logger = logging.getLogger(__name__)

# All control endpoints can write holding registers or expose setting values,
# so the whole router requires a valid bearer token.
router = APIRouter(tags=["Inverter Control"], dependencies=[Depends(require_auth)])


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


@router.post("/inverter/{serial}/settings/{setting_id}/write")
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
    hr_idx = get_hr_index(setting)
    if hr_idx is None:
        raise HTTPException(status_code=500, detail=f"No register mapping for setting '{setting['name']}'")
    register_value = convert_to_register_value(setting, body.value)
    request = WriteHoldingRegisterRequest(hr_idx, register_value)
    try:
        await inv_state.client.execute([request], timeout=3.0, retries=1)
    except Exception as exc:
        logger.exception("Setting write failed for %s setting=%s", serial, setting_id)
        return {
            "data": {
                "value": body.value,
                "success": False,
                "message": f"{type(exc).__name__}: write failed (see server logs)",
            }
        }
    return {"data": {"value": body.value, "success": True, "message": "Written Successfully"}}
