"""FastAPI application entry point for GivLocal API."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Optional

from fastapi import FastAPI

from givlocal.auth import TokenStore, generate_token
from givlocal.config import AppConfig, load_config
from givlocal.database import init_app_db
from givlocal.metrics_store import MetricsStore

logger = logging.getLogger(__name__)


@dataclass
class InverterState:
    """Runtime state for a connected inverter."""

    serial: str
    host: str
    port: int
    plant: Optional[object] = None
    client: Optional[object] = None


@dataclass
class AppState:
    """Global application state shared across request handlers."""

    config: Optional[AppConfig] = None
    token_store: Optional[TokenStore] = None
    metrics_store: Optional[MetricsStore] = None
    inverters: dict[str, InverterState] = field(default_factory=dict)
    settings: dict = field(default_factory=dict)
    auth_required: bool = True


app_state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialise resources on startup, clean up on shutdown."""
    global app_state

    # 1. Load configuration
    config_path = os.environ.get("GIVENERGY_CONFIG", "config.yaml")
    try:
        config = load_config(config_path)
        app_state.config = config
        app_state.auth_required = config.auth_required
        logger.info("Loaded config from %s", config_path)
    except FileNotFoundError:
        logger.warning("Config file %s not found — using defaults", config_path)
        config = None

    # 2. Initialise databases
    app_db_path = config.storage.app_db if config else "data/app.db"
    metrics_db_path = config.storage.metrics_db if config else "data/metrics.db"

    app_db_conn = init_app_db(app_db_path)
    app_state.token_store = TokenStore(app_db_conn)

    app_state.metrics_store = MetricsStore(metrics_db_path)
    logger.info("Databases initialised (app=%s, metrics=%s)", app_db_path, metrics_db_path)

    # 3. Generate admin token if none exist
    existing_tokens = app_state.token_store.list_all()
    if not existing_tokens:
        plaintext, _ = generate_token()
        app_state.token_store.create("admin", plaintext)
        logger.warning(
            "No API tokens found — generated admin token: %s  (store this securely, it will not be shown again)",
            plaintext,
        )

    # 3b. Load settings from cloud dump
    from pathlib import Path

    from .settings_map import load_settings_from_cloud_dump

    cloud_data_dir = Path("cloud-data")
    if cloud_data_dir.exists():
        for settings_file in cloud_data_dir.glob("*.json"):
            app_state.settings = load_settings_from_cloud_dump(str(settings_file))
            logger.info("Loaded %d settings from %s", len(app_state.settings), settings_file.name)
            break
    if not app_state.settings:
        logger.warning("No settings found in cloud-data/. Run cloud_dump --settings-only first.")

    # 4. Connect to inverters
    from .inverter_manager import InverterManager

    manager = InverterManager()
    if config and config.inverters:
        await manager.connect_all(config.inverters)
    app_state.inverters = manager.inverters

    if not app_state.inverters:
        logger.warning("No inverters connected. API will return empty data.")

    # 5. Start background poller
    import asyncio

    from .poller import poll_loop

    poller_task = asyncio.create_task(
        poll_loop(
            app_state.inverters,
            app_state.metrics_store,
            interval=config.poll_interval if config else 30,
            full_refresh_interval=config.full_refresh_interval if config else 300,
        )
    )

    yield

    # Shutdown: clean up resources
    poller_task.cancel()
    try:
        await poller_task
    except asyncio.CancelledError:
        pass
    await manager.close_all()
    app_state.metrics_store.close()
    app_db_conn.close()

    logger.info("GivLocal API shut down")


app = FastAPI(
    title="GivLocal API",
    version="0.1.0",
    lifespan=lifespan,
)

from .api.devices import router as devices_router  # noqa: E402
from .api.inverter_control import router as inverter_control_router  # noqa: E402
from .api.inverter_data import router as inverter_data_router  # noqa: E402
from .api.presets import router as presets_router  # noqa: E402
from .api.prometheus import router as prometheus_router  # noqa: E402

app.include_router(devices_router, prefix="/v1")
app.include_router(inverter_data_router, prefix="/v1")
app.include_router(inverter_control_router, prefix="/v1")
app.include_router(prometheus_router)
app.include_router(presets_router, prefix="/v1")


@app.get("/")
async def root():
    """Health-check / discovery endpoint."""
    return {"name": "GivLocal API", "version": "0.1.0"}
