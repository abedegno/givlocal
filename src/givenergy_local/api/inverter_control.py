"""API routes for inverter settings read/write (mirrors GivEnergy Cloud API)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["Inverter Control"])


class WriteSettingRequest(BaseModel):
    value: bool | int | str
    context: str | None = None


@router.get("/inverter/{serial}/settings")
async def list_inverter_settings(serial: str):
    """Return available settings for the inverter."""
    from givenergy_local.main import app_state
    from givenergy_local.settings_map import list_settings

    inv_state = app_state.inverters.get(serial)
    if not inv_state:
        raise HTTPException(status_code=404, detail="Inverter not found")

    # Determine device model code from register cache (default "2001")
    device_type_code = "2001"
    try:
        raw = inv_state.plant.inverter.get("device_type_code")
        if raw is not None:
            device_type_code = str(raw)
    except Exception:
        pass

    settings = list_settings(app_state.settings_map, device_type_code)
    return {"data": settings}


@router.post("/inverter/{serial}/settings/{setting_id}/read")
async def read_inverter_setting(serial: str, setting_id: int):
    """Read the current value of a setting from the in-memory register cache."""
    from givenergy_modbus_async.model.register import HR

    from givenergy_local.main import app_state
    from givenergy_local.settings_map import convert_from_register_value, get_setting

    inv_state = app_state.inverters.get(serial)
    if not inv_state:
        raise HTTPException(status_code=404, detail="Inverter not found")

    device_type_code = "2001"
    try:
        raw = inv_state.plant.inverter.get("device_type_code")
        if raw is not None:
            device_type_code = str(raw)
    except Exception:
        pass

    setting = get_setting(app_state.settings_map, device_type_code, setting_id)
    if setting is None:
        raise HTTPException(status_code=404, detail="Setting not found")

    inv = inv_state.plant.inverter
    register_name = setting.get("register", "")
    hr_override = setting.get("hr_override")

    register_value = inv.get(register_name)

    if register_value is None and hr_override is not None:
        # Fall back to direct cache lookup
        register_value = inv_state.plant.inverter.cache.get(HR(hr_override))

    if register_value is None:
        raise HTTPException(status_code=404, detail="Register value not available")

    display_value = convert_from_register_value(setting, int(register_value))
    return {"data": {"value": display_value}}


@router.post("/inverter/{serial}/settings/{setting_id}/write")
async def write_inverter_setting(serial: str, setting_id: int, body: WriteSettingRequest):
    """Write a value to the inverter."""
    from givenergy_modbus_async.model.inverter import Inverter
    from givenergy_modbus_async.pdu import WriteHoldingRegisterRequest

    from givenergy_local.main import app_state
    from givenergy_local.settings_map import (
        convert_to_register_value,
        get_setting,
        validate_setting_value,
    )

    inv_state = app_state.inverters.get(serial)
    if not inv_state:
        raise HTTPException(status_code=404, detail="Inverter not found")

    device_type_code = "2001"
    try:
        raw = inv_state.plant.inverter.get("device_type_code")
        if raw is not None:
            device_type_code = str(raw)
    except Exception:
        pass

    setting = get_setting(app_state.settings_map, device_type_code, setting_id)
    if setting is None:
        raise HTTPException(status_code=404, detail="Setting not found")

    value = body.value

    if not validate_setting_value(setting, value):
        raise HTTPException(
            status_code=422,
            detail=f"Invalid value {value!r} for setting {setting_id}",
        )

    register_value = convert_to_register_value(setting, value)

    # Determine HR index
    hr_override = setting.get("hr_override")
    if hr_override is not None:
        hr_index = hr_override
    else:
        register_name = setting.get("register", "")
        lut_entry = Inverter.REGISTER_LUT.get(register_name)
        if lut_entry is None:
            raise HTTPException(
                status_code=500,
                detail=f"No register mapping found for {register_name!r}",
            )
        # lut_entry.registers is a tuple of HR objects; use the first one
        hr_obj = lut_entry.registers[0]
        hr_index = hr_obj._idx

    request = WriteHoldingRegisterRequest(hr_index, register_value)

    try:
        await inv_state.client.execute([request], timeout=3.0, retries=1)
    except Exception as exc:
        return {
            "data": {
                "value": value,
                "success": False,
                "message": str(exc),
            }
        }

    return {
        "data": {
            "value": value,
            "success": True,
            "message": "Written Successfully",
        }
    }
