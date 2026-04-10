"""FastAPI dependencies for authentication and resource lookup."""

from __future__ import annotations

from fastapi import Header, HTTPException


async def require_auth(authorization: str = Header(None)) -> None:
    """Validate Bearer token against the token store.

    Checks app_state.auth_required; if disabled, allows all requests through.
    """
    from givlocal.main import app_state

    if not app_state.auth_required:
        return

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = authorization[7:]
    if not app_state.token_store.validate(token):
        raise HTTPException(status_code=401, detail="Invalid API token")


async def get_inverter(inverter_serial_number: str):
    """Look up an inverter by serial number from app_state.

    Raises 404 if the inverter is not found.
    """
    from givlocal.main import app_state

    inv_state = app_state.inverters.get(inverter_serial_number)
    if not inv_state:
        raise HTTPException(status_code=404, detail="Inverter not found")
    return inv_state
