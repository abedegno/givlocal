"""API routes for communication devices (inverters)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from givlocal.api.dependencies import require_auth
from givlocal.api.schemas import DataResponse

router = APIRouter(tags=["Communication Devices"])


def _build_device_info(inv_state) -> dict:
    """Build a device info dict from an InverterState."""
    plant = inv_state.plant
    serial_number = plant.data_adapter_serial_number
    inverter_serial = plant.inverter_serial_number
    inverter = plant.inverter

    battery_type = inverter.get("battery_type")
    model = inverter.get("device_type_code")
    arm_firmware = inverter.get("arm_firmware_version")
    dsp_firmware = inverter.get("dsp_firmware_version")
    firmware_version = f"ARM {arm_firmware} DSP {dsp_firmware}" if arm_firmware and dsp_firmware else None

    status_map = {0: "Waiting", 1: "Normal", 2: "Warning", 3: "Fault", 4: "Updating"}
    status_raw = inverter.get("status")
    status_int = int(status_raw) if status_raw is not None else 0
    status = status_map.get(status_int, "Unknown")

    num_batteries = getattr(plant, "number_batteries", 0) or 0
    batteries = [{"serial": None} for _ in range(num_batteries)]

    return {
        "serial_number": serial_number,
        "type": "WIFI",
        "inverter": {
            "serial": inverter_serial,
            "status": status,
            "info": {
                "battery_type": battery_type,
                "model": model,
                "firmware_version": firmware_version,
            },
            "connections": {
                "batteries": batteries,
                "meters": [],
            },
        },
    }


@router.get("/communication-device", dependencies=[Depends(require_auth)])
async def list_devices():
    """Return all connected inverters as communication devices."""
    from givlocal.main import app_state

    devices = [_build_device_info(inv_state) for inv_state in app_state.inverters.values()]
    return DataResponse(data=devices)


@router.get("/communication-device/{serial_number}", dependencies=[Depends(require_auth)])
async def get_device(serial_number: str):
    """Return a single device by its data adapter serial. 404 if not found."""
    from givlocal.main import app_state

    for inv_state in app_state.inverters.values():
        if inv_state.plant.data_adapter_serial_number == serial_number:
            return DataResponse(data=_build_device_info(inv_state))

    raise HTTPException(status_code=404, detail="Device not found")
