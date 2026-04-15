"""FastAPI dependencies for authentication and resource lookup."""

from __future__ import annotations

from fastapi import Header, HTTPException

# Scope hierarchy: a token with a higher scope satisfies lower-scope checks.
# admin > write > read.
_SCOPE_RANK = {"read": 1, "write": 2, "admin": 3}


async def require_auth(authorization: str = Header(None)) -> str | None:
    """Validate Bearer token and return its scope (or None if auth disabled).

    Checks app_state.auth_required; if disabled, allows all requests through.
    """
    from givlocal.state import app_state

    if not app_state.auth_required:
        return None

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = authorization[7:]
    scope = app_state.token_store.validate(token)
    if scope is None:
        raise HTTPException(status_code=401, detail="Invalid API token")
    return scope


def require_scope(minimum: str):
    """Return a dependency that requires the token to satisfy `minimum`.

    Usage: `@router.post(..., dependencies=[Depends(require_scope("write"))])`.
    A token with scope 'admin' satisfies 'read' and 'write'. If auth is
    disabled globally, the check is a no-op.
    """
    if minimum not in _SCOPE_RANK:
        raise ValueError(f"unknown scope {minimum!r}")
    required = _SCOPE_RANK[minimum]

    async def _dep(authorization: str = Header(None)) -> None:
        from givlocal.state import app_state

        if not app_state.auth_required:
            return
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid token")
        scope = app_state.token_store.validate(authorization[7:])
        if scope is None:
            raise HTTPException(status_code=401, detail="Invalid API token")
        if _SCOPE_RANK.get(scope, 0) < required:
            raise HTTPException(
                status_code=403,
                detail=f"Token scope '{scope}' insufficient (requires '{minimum}')",
            )

    return _dep


async def get_inverter(inverter_serial_number: str):
    """Look up an inverter by serial number from app_state.

    Raises 404 if the inverter is not found.
    """
    from givlocal.main import app_state

    inv_state = app_state.inverters.get(inverter_serial_number)
    if not inv_state:
        raise HTTPException(status_code=404, detail="Inverter not found")
    return inv_state
