"""Shared application state dataclasses.

Lives outside main.py so that poller / inverter_manager / test harnesses can
import the types without pulling in the full FastAPI app (and its lifespan)
as a side effect.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from givlocal.auth import TokenStore
    from givlocal.config import AppConfig
    from givlocal.metrics_store import MetricsStore


@dataclass
class InverterState:
    """Runtime state for a connected inverter."""

    serial: str
    host: str
    port: int
    plant: Optional[object] = None
    client: Optional[object] = None
    last_poll_ok_at: float = 0.0
    consecutive_failures: int = 0


@dataclass
class AppState:
    """Global application state shared across request handlers."""

    config: Optional["AppConfig"] = None
    token_store: Optional["TokenStore"] = None
    metrics_store: Optional["MetricsStore"] = None
    # Shared sqlite connection for the app DB. Routes should use this rather
    # than reaching into TokenStore._conn.
    app_db: Optional[object] = None
    inverters: dict[str, InverterState] = field(default_factory=dict)
    settings: dict = field(default_factory=dict)
    auth_required: bool = True
    prometheus_auth_required: bool = True


# Singleton, imported by lifespan + routes + tests.
app_state = AppState()
