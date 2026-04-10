import json


def test_write_data_point_creates_partition(tmp_path):
    from givlocal.metrics_store import MetricsStore

    store = MetricsStore(str(tmp_path / "metrics.db"))
    ts = 1712678400  # 2024-04-09 16:00:00 UTC
    data = {"p_pv1": 1000, "p_pv2": 500, "battery_percent": 85}
    store.write_data_point("FA2424G403", ts, data)
    rows = store.conn.execute("SELECT * FROM data_points_2024_04").fetchall()
    assert len(rows) == 1
    assert rows[0][1] == "FA2424G403"
    assert rows[0][2] == ts
    assert json.loads(rows[0][3])["p_pv1"] == 1000


def test_query_data_points_across_partitions(tmp_path):
    from givlocal.metrics_store import MetricsStore

    store = MetricsStore(str(tmp_path / "metrics.db"))
    store.write_data_point("FA2424G403", 1709251200, {"p_pv1": 100})  # March
    store.write_data_point("FA2424G403", 1712678400, {"p_pv1": 200})  # April
    rows = store.query_data_points("FA2424G403", 1709200000, 1712700000)
    assert len(rows) == 2
    assert json.loads(rows[0]["data"])["p_pv1"] == 100
    assert json.loads(rows[1]["data"])["p_pv1"] == 200


def test_write_meter_daily_upserts(tmp_path):
    from givlocal.metrics_store import MetricsStore

    store = MetricsStore(str(tmp_path / "metrics.db"))
    store.write_meter_daily("FA2424G403", "2024-04-09", solar=5.2, grid_import=3.1)
    store.write_meter_daily("FA2424G403", "2024-04-09", solar=5.5, grid_import=3.3)
    rows = store.conn.execute("SELECT * FROM meter_daily").fetchall()
    assert len(rows) == 1  # upserted, not duplicated
    assert rows[0][3] == 5.5  # solar updated


def test_retention_drops_old_partitions(tmp_path):
    from givlocal.metrics_store import MetricsStore

    store = MetricsStore(str(tmp_path / "metrics.db"))
    store.write_data_point("FA2424G403", 1609459200, {"old": True})  # 2021-01-01
    store.write_data_point("FA2424G403", 1712678400, {"new": True})  # 2024-04-09
    tables_before = store.list_partitions()
    assert "data_points_2021_01" in tables_before
    store.apply_retention(months=12)
    tables_after = store.list_partitions()
    assert "data_points_2021_01" not in tables_after
    assert "data_points_2024_04" in tables_after
