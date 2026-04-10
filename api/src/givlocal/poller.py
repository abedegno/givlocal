"""Background polling service for GivEnergy inverters."""

from __future__ import annotations

import asyncio
import logging
import time

from .main import InverterState
from .metrics_store import MetricsStore

logger = logging.getLogger(__name__)


async def poll_once(
    state: InverterState,
    store: MetricsStore,
    full_refresh: bool = False,
) -> None:
    """Poll a single inverter and store the resulting data point."""
    client = state.client
    try:
        plant = await client.refresh_plant(
            full_refresh=full_refresh,
            number_batteries=client.plant.number_batteries,
            timeout=3.0,
            retries=1,
        )
    except Exception as e:
        logger.warning("Poll failed for %s: %s", state.serial, e)
        return

    inv = plant.inverter
    if inv is None:
        return

    data = inv.getall()
    ts = int(time.time())
    store.write_data_point(state.serial, ts, data)
    state.plant = plant


async def poll_loop(
    inverters: dict[str, InverterState],
    store: MetricsStore,
    interval: int = 30,
    full_refresh_interval: int = 300,
) -> None:
    """Background loop that polls all inverters periodically."""
    last_full: float = 0.0
    while True:
        now = time.time()
        full = (now - last_full) >= full_refresh_interval
        if full:
            last_full = now
        for state in inverters.values():
            try:
                await poll_once(state, store, full_refresh=full)
            except Exception as e:
                logger.error("Unhandled poll error for %s: %s", state.serial, e)
        await asyncio.sleep(interval)
