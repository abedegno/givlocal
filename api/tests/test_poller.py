"""Tests for the poller service."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_poll_once_stores_data_point(tmp_path):
    from givlocal.main import InverterState
    from givlocal.metrics_store import MetricsStore
    from givlocal.poller import poll_once

    mock_client = AsyncMock()
    mock_plant = MagicMock()
    mock_inv = MagicMock()
    mock_inv.getall.return_value = {
        "p_pv1": 500,
        "p_pv2": 300,
        "battery_percent": 80,
    }
    mock_plant.inverter = mock_inv
    mock_plant.number_batteries = 0
    mock_client.plant = mock_plant
    mock_client.refresh_plant = AsyncMock(return_value=mock_plant)

    state = InverterState(
        serial="TEST001",
        host="127.0.0.1",
        port=8899,
        plant=mock_plant,
        client=mock_client,
    )
    store = MetricsStore(str(tmp_path / "metrics.db"))
    await poll_once(state, store, full_refresh=False)

    partitions = store.list_partitions()
    assert len(partitions) == 1
    rows = store.conn.execute(f"SELECT data FROM {partitions[0]}").fetchall()
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_poll_once_handles_refresh_failure(tmp_path):
    from givlocal.main import InverterState
    from givlocal.metrics_store import MetricsStore
    from givlocal.poller import poll_once

    mock_client = AsyncMock()
    mock_plant = MagicMock()
    mock_plant.number_batteries = 0
    mock_client.plant = mock_plant
    mock_client.refresh_plant = AsyncMock(side_effect=OSError("timeout"))

    state = InverterState(
        serial="TEST002",
        host="127.0.0.1",
        port=8899,
        plant=mock_plant,
        client=mock_client,
    )
    store = MetricsStore(str(tmp_path / "metrics.db"))
    # Should not raise
    await poll_once(state, store, full_refresh=False)
    assert store.list_partitions() == []


@pytest.mark.asyncio
async def test_poll_once_skips_none_inverter(tmp_path):
    from givlocal.main import InverterState
    from givlocal.metrics_store import MetricsStore
    from givlocal.poller import poll_once

    mock_client = AsyncMock()
    mock_plant = MagicMock()
    mock_plant.inverter = None
    mock_plant.number_batteries = 0
    mock_client.plant = mock_plant
    mock_client.refresh_plant = AsyncMock(return_value=mock_plant)

    state = InverterState(
        serial="TEST003",
        host="127.0.0.1",
        port=8899,
        plant=mock_plant,
        client=mock_client,
    )
    store = MetricsStore(str(tmp_path / "metrics.db"))
    await poll_once(state, store, full_refresh=False)
    assert store.list_partitions() == []


@pytest.mark.asyncio
async def test_poll_once_updates_state_plant(tmp_path):
    from givlocal.main import InverterState
    from givlocal.metrics_store import MetricsStore
    from givlocal.poller import poll_once

    mock_client = AsyncMock()
    old_plant = MagicMock()
    old_plant.number_batteries = 0
    new_plant = MagicMock()
    mock_inv = MagicMock()
    mock_inv.getall.return_value = {"battery_percent": 50}
    new_plant.inverter = mock_inv
    mock_client.plant = old_plant
    mock_client.refresh_plant = AsyncMock(return_value=new_plant)

    state = InverterState(
        serial="TEST004",
        host="127.0.0.1",
        port=8899,
        plant=old_plant,
        client=mock_client,
    )
    store = MetricsStore(str(tmp_path / "metrics.db"))
    await poll_once(state, store, full_refresh=True)
    assert state.plant is new_plant


@pytest.mark.asyncio
async def test_poll_loop_runs_and_stops(tmp_path):
    """poll_loop calls poll_once for each inverter and iterates."""
    from givlocal.main import InverterState
    from givlocal.metrics_store import MetricsStore
    from givlocal.poller import poll_loop

    call_count = 0

    async def fake_sleep(seconds):
        nonlocal call_count
        call_count += 1
        if call_count >= 2:
            raise asyncio.CancelledError

    mock_client = AsyncMock()
    mock_plant = MagicMock()
    mock_inv = MagicMock()
    mock_inv.getall.return_value = {"battery_percent": 70}
    mock_plant.inverter = mock_inv
    mock_plant.number_batteries = 0
    mock_client.plant = mock_plant
    mock_client.refresh_plant = AsyncMock(return_value=mock_plant)

    state = InverterState(
        serial="LOOP001",
        host="127.0.0.1",
        port=8899,
        plant=mock_plant,
        client=mock_client,
    )
    store = MetricsStore(str(tmp_path / "metrics.db"))

    with patch("givlocal.poller.asyncio.sleep", side_effect=fake_sleep):
        with pytest.raises(asyncio.CancelledError):
            await poll_loop({"LOOP001": state}, store, interval=1, full_refresh_interval=300)

    partitions = store.list_partitions()
    assert len(partitions) == 1
