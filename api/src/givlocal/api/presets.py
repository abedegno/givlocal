"""API routes for preset profiles."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from givlocal.api.dependencies import require_auth

router = APIRouter(tags=["Preset Profiles"])


class CreateProfileRequest(BaseModel):
    name: str
    settings: dict


class DeleteProfileRequest(BaseModel):
    id: int


@router.get("/inverter/{serial}/presets", dependencies=[Depends(require_auth)])
async def list_presets_legacy(serial: str):
    """Legacy endpoint — returns empty list."""
    from givlocal.main import app_state

    if serial not in app_state.inverters:
        raise HTTPException(status_code=404, detail="Inverter not found")

    return {"data": []}


@router.get("/inverter/{serial}/preset-profile", dependencies=[Depends(require_auth)])
async def list_preset_profiles(serial: str):
    """List saved preset profiles for the given inverter."""
    from givlocal.main import app_state

    if serial not in app_state.inverters:
        raise HTTPException(status_code=404, detail="Inverter not found")

    conn = app_state.token_store._conn
    cursor = conn.execute(
        "SELECT id, name, settings, created_at FROM preset_profiles WHERE inverter_serial = ? ORDER BY id",
        (serial,),
    )
    rows = cursor.fetchall()
    data = [
        {
            "id": row[0],
            "name": row[1],
            "settings": json.loads(row[2]) if isinstance(row[2], str) else row[2],
            "created_at": row[3],
        }
        for row in rows
    ]
    return {"data": data}


@router.post("/inverter/{serial}/preset-profile", status_code=201, dependencies=[Depends(require_auth)])
async def create_preset_profile(serial: str, body: CreateProfileRequest):
    """Create a new preset profile for the given inverter."""
    from givlocal.main import app_state

    if serial not in app_state.inverters:
        raise HTTPException(status_code=404, detail="Inverter not found")

    conn = app_state.token_store._conn
    cursor = conn.execute(
        "INSERT INTO preset_profiles (inverter_serial, name, settings) VALUES (?, ?, ?)",
        (serial, body.name, json.dumps(body.settings)),
    )
    conn.commit()
    return {"data": {"id": cursor.lastrowid, "name": body.name}}


@router.delete("/inverter/{serial}/preset-profile", dependencies=[Depends(require_auth)])
async def delete_preset_profile(serial: str, body: DeleteProfileRequest):
    """Delete a preset profile by ID."""
    from givlocal.main import app_state

    if serial not in app_state.inverters:
        raise HTTPException(status_code=404, detail="Inverter not found")

    conn = app_state.token_store._conn
    conn.execute(
        "DELETE FROM preset_profiles WHERE id = ? AND inverter_serial = ?",
        (body.id, serial),
    )
    conn.commit()
    return {"data": {"success": True}}
