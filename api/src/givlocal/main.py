"""FastAPI application entry point for GivLocal API."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from givlocal.auth import TokenStore, generate_token
from givlocal.config import load_config
from givlocal.database import init_app_db
from givlocal.metrics_store import MetricsStore
from givlocal.state import AppState, InverterState, app_state  # re-exported

logger = logging.getLogger(__name__)

# Silence F401: these are re-exported for back-compat with existing callers
# that still do `from givlocal.main import InverterState`.
__all__ = ["AppState", "InverterState", "app", "app_state"]


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
        app_state.prometheus_auth_required = config.prometheus_auth_required
        logger.info("Loaded config from %s", config_path)
    except FileNotFoundError:
        # If the user explicitly set GIVENERGY_CONFIG, a missing file is an
        # error — don't silently boot with an empty inverter list. If the env
        # var was not set and the default config.yaml is missing, keep the
        # legacy "warn and use defaults" behaviour so tests and first-run
        # developer setups still work.
        if "GIVENERGY_CONFIG" in os.environ:
            raise RuntimeError(f"GIVENERGY_CONFIG={config_path!r} not found") from None
        logger.warning("Config file %s not found — using defaults", config_path)
        config = None
    except ValueError as e:
        raise RuntimeError(f"Invalid configuration in {config_path}: {e}") from e

    # 2. Initialise databases
    app_db_path = config.storage.app_db if config else "data/app.db"
    metrics_db_path = config.storage.metrics_db if config else "data/metrics.db"

    app_db_conn = init_app_db(app_db_path)
    app_state.app_db = app_db_conn
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
        # Deterministic pick: prefer "settings.json" if present, otherwise
        # the alphabetically-first *.json. `glob` iteration order is
        # filesystem-dependent, so sort explicitly.
        candidates = sorted(cloud_data_dir.glob("*.json"))
        preferred = cloud_data_dir / "settings.json"
        settings_file = preferred if preferred.exists() else (candidates[0] if candidates else None)
        if settings_file is not None:
            app_state.settings = load_settings_from_cloud_dump(str(settings_file))
            logger.info("Loaded %d settings from %s", len(app_state.settings), settings_file.name)
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
            reconnect=manager.reconnect,
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

from starlette.middleware.cors import CORSMiddleware  # noqa: E402

# CORSMiddleware is attached before lifespan runs, so the origin list is
# sourced from the GIVENERGY_CORS_ORIGINS env var (comma-separated) rather
# than config.yaml. Default "*" is fine on a trusted LAN.
_cors_env = os.environ.get("GIVENERGY_CORS_ORIGINS", "*")
_cors_origins = [o.strip() for o in _cors_env.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    # Starlette ignores allow_credentials when allow_origins=["*"]; only
    # meaningful when a specific origin list is supplied.
    allow_credentials=_cors_origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.get("/health")
async def health():
    """Per-inverter liveness: last successful poll and failure streak."""
    import time as _time

    now = _time.time()
    inverters = [
        {
            "serial": s.serial,
            "host": s.host,
            "last_poll_ok_age_s": (now - s.last_poll_ok_at) if s.last_poll_ok_at else None,
            "consecutive_failures": s.consecutive_failures,
        }
        for s in app_state.inverters.values()
    ]
    all_healthy = all(i["last_poll_ok_age_s"] is not None and i["last_poll_ok_age_s"] < 120 for i in inverters)
    return {"ok": all_healthy, "inverters": inverters}
