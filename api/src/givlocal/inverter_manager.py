"""Manages connections to one or more GivEnergy inverters."""

from __future__ import annotations

import logging

from givenergy_modbus_async.client.client import Client

from .config import InverterConfig
from .main import InverterState

logger = logging.getLogger(__name__)


class InverterManager:
    """Connect to, detect, and track one or more GivEnergy inverters."""

    def __init__(self) -> None:
        self.inverters: dict[str, InverterState] = {}
        self._clients: list[Client] = []

    async def connect_all(self, configs: list[InverterConfig]) -> None:
        """Connect to each inverter, run detect_plant, populate self.inverters keyed by serial."""
        for cfg in configs:
            try:
                client = Client(host=cfg.host, port=cfg.port, connect_timeout=10.0)
                await client.connect()
                await client.detect_plant(timeout=5.0, retries=2)
                serial = client.plant.inverter_serial_number
                state = InverterState(
                    serial=serial,
                    host=cfg.host,
                    port=cfg.port,
                    plant=client.plant,
                    client=client,
                )
                self.inverters[serial] = state
                self._clients.append(client)
            except Exception as e:
                logger.error("Failed to connect to %s:%d: %s", cfg.host, cfg.port, e)

    async def close_all(self) -> None:
        """Close all open client connections and clear state."""
        for client in self._clients:
            try:
                await client.close()
            except Exception:
                pass
        self._clients.clear()
        self.inverters.clear()
