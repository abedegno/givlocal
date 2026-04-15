"""Background polling service for GivEnergy inverters."""

from __future__ import annotations

import asyncio
import logging
import time

from .metrics_store import MetricsStore
from .state import InverterState

logger = logging.getLogger(__name__)


async def poll_once(
    state: InverterState,
    store: MetricsStore,
    full_refresh: bool = False,
    reconnect=None,
) -> None:
    """Poll a single inverter and store the resulting data point.

    If the refresh raises, mark the state as failed and (when `reconnect` is
    provided) attempt to re-establish the session. A failed reconnect is
    logged but not fatal — the next tick will try again.
    """
    client = state.client
    try:
        plant = await client.refresh_plant(
            full_refresh=full_refresh,
            number_batteries=client.plant.number_batteries,
            timeout=3.0,
            retries=1,
        )
    except Exception as e:
        state.consecutive_failures += 1
        logger.warning(
            "Poll failed for %s (failure %d): %s",
            state.serial,
            state.consecutive_failures,
            e,
        )
        if reconnect is not None:
            try:
                await reconnect(state)
            except Exception as rex:
                logger.warning("Reconnect raised for %s: %s", state.serial, rex)
        return

    inv = plant.inverter
    if inv is None:
        return

    data = inv.getall()
    ts = int(time.time())
    store.write_data_point(state.serial, ts, data)
    state.plant = plant
    state.last_poll_ok_at = time.time()
    state.consecutive_failures = 0


async def poll_loop(
    inverters: dict[str, InverterState],
    store: MetricsStore,
    interval: int = 30,
    full_refresh_interval: int = 300,
    reconnect=None,
) -> None:
    """Background loop that polls all inverters concurrently."""
    last_full: float = 0.0
    while True:
        now = time.time()
        full = (now - last_full) >= full_refresh_interval
        if full:
            last_full = now
        # Concurrent per-inverter polls so one slow/hung device doesn't
        # stall the others.
        await asyncio.gather(
            *(poll_once(s, store, full_refresh=full, reconnect=reconnect) for s in inverters.values()),
            return_exceptions=True,
        )
        await asyncio.sleep(interval)
