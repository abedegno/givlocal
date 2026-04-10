"""Tests for InverterManager."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_connect_and_detect_populates_state():
    from givlocal.config import InverterConfig
    from givlocal.inverter_manager import InverterManager

    mock_client = AsyncMock()
    mock_plant = MagicMock()
    mock_plant.inverter_serial_number = "FA2424G403"
    mock_plant.inverter.serial_number = "FA2424G403"
    mock_plant.inverter.model = "20g3"
    mock_plant.number_batteries = 1
    mock_client.plant = mock_plant

    with patch("givlocal.inverter_manager.Client", return_value=mock_client):
        manager = InverterManager()
        configs = [InverterConfig(host="192.168.86.44")]
        await manager.connect_all(configs)

    assert "FA2424G403" in manager.inverters
    state = manager.inverters["FA2424G403"]
    assert state.serial == "FA2424G403"
    assert state.client is mock_client


@pytest.mark.asyncio
async def test_connect_handles_unreachable_inverter():
    from givlocal.config import InverterConfig
    from givlocal.inverter_manager import InverterManager

    mock_client = AsyncMock()
    mock_client.connect.side_effect = OSError("Connection refused")

    with patch("givlocal.inverter_manager.Client", return_value=mock_client):
        manager = InverterManager()
        configs = [InverterConfig(host="10.0.0.99")]
        await manager.connect_all(configs)

    assert len(manager.inverters) == 0


@pytest.mark.asyncio
async def test_close_all_clears_state():
    from givlocal.config import InverterConfig
    from givlocal.inverter_manager import InverterManager

    mock_client = AsyncMock()
    mock_plant = MagicMock()
    mock_plant.inverter_serial_number = "SERIAL001"
    mock_plant.number_batteries = 0
    mock_client.plant = mock_plant

    with patch("givlocal.inverter_manager.Client", return_value=mock_client):
        manager = InverterManager()
        await manager.connect_all([InverterConfig(host="192.168.1.1")])

    assert len(manager.inverters) == 1
    await manager.close_all()
    assert len(manager.inverters) == 0
    assert len(manager._clients) == 0


@pytest.mark.asyncio
async def test_connect_multiple_inverters():
    from givlocal.config import InverterConfig
    from givlocal.inverter_manager import InverterManager

    def make_client(serial: str) -> AsyncMock:
        client = AsyncMock()
        plant = MagicMock()
        plant.inverter_serial_number = serial
        plant.number_batteries = 0
        client.plant = plant
        return client

    clients = [make_client("AAA001"), make_client("BBB002")]
    client_iter = iter(clients)

    with patch(
        "givlocal.inverter_manager.Client",
        side_effect=lambda **kwargs: next(client_iter),
    ):
        manager = InverterManager()
        configs = [
            InverterConfig(host="192.168.1.1"),
            InverterConfig(host="192.168.1.2"),
        ]
        await manager.connect_all(configs)

    assert set(manager.inverters.keys()) == {"AAA001", "BBB002"}
