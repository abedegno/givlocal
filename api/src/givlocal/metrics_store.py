"""Monthly-partitioned SQLite metrics store for GivEnergy inverter data."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class MetricsStore:
    """SQLite-backed time-series store with monthly partition tables."""

    def __init__(self, db_path: str) -> None:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._known_partitions: set[str] = set()
        self._create_meter_daily_table()
        self._discover_partitions()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _create_meter_daily_table(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS meter_daily (
                id               INTEGER PRIMARY KEY,
                inverter_serial  TEXT    NOT NULL,
                date             TEXT    NOT NULL,
                solar            REAL,
                grid_import      REAL,
                grid_export      REAL,
                consumption      REAL,
                battery_charge   REAL,
                battery_discharge REAL,
                UNIQUE (inverter_serial, date)
            )
            """
        )
        self.conn.commit()

    def _discover_partitions(self) -> None:
        rows = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'data_points_%'"
        ).fetchall()
        for row in rows:
            self._known_partitions.add(row[0])

    @staticmethod
    def _partition_name(unix_ts: int) -> str:
        dt = datetime.fromtimestamp(unix_ts, tz=timezone.utc)
        return f"data_points_{dt.year:04d}_{dt.month:02d}"

    def _ensure_partition(self, table_name: str) -> None:
        if table_name in self._known_partitions:
            return
        self.conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id               INTEGER PRIMARY KEY,
                inverter_serial  TEXT    NOT NULL,
                timestamp        INTEGER NOT NULL,
                data             JSON    NOT NULL
            )
            """
        )
        self.conn.execute(
            f"""
            CREATE INDEX IF NOT EXISTS idx_{table_name}_serial_ts
            ON {table_name} (inverter_serial, timestamp)
            """
        )
        self.conn.commit()
        self._known_partitions.add(table_name)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def write_data_point(self, serial: str, timestamp: int, data: dict) -> None:
        table = self._partition_name(timestamp)
        self._ensure_partition(table)
        self.conn.execute(
            f"INSERT INTO {table} (inverter_serial, timestamp, data) VALUES (?, ?, ?)",
            (serial, timestamp, json.dumps(data, default=str)),
        )
        self.conn.commit()

    def query_data_points(self, serial: str, start_ts: int, end_ts: int) -> list[sqlite3.Row]:
        results: list[sqlite3.Row] = []
        for table in sorted(self._known_partitions):
            rows = self.conn.execute(
                f"""
                SELECT * FROM {table}
                WHERE inverter_serial = ?
                  AND timestamp >= ?
                  AND timestamp <= ?
                ORDER BY timestamp
                """,
                (serial, start_ts, end_ts),
            ).fetchall()
            results.extend(rows)
        # Re-sort across partitions (each partition is already ordered)
        results.sort(key=lambda r: r["timestamp"])
        return results

    def write_meter_daily(self, serial: str, date: str, **kwargs) -> None:
        columns = ["inverter_serial", "date"] + list(kwargs.keys())
        placeholders = ", ".join("?" for _ in columns)
        col_list = ", ".join(columns)
        update_clause = ", ".join(f"{k} = excluded.{k}" for k in kwargs)
        values = [serial, date] + list(kwargs.values())
        self.conn.execute(
            f"""
            INSERT INTO meter_daily ({col_list})
            VALUES ({placeholders})
            ON CONFLICT (inverter_serial, date) DO UPDATE SET {update_clause}
            """,
            values,
        )
        self.conn.commit()

    def list_partitions(self) -> list[str]:
        return sorted(self._known_partitions)

    def apply_retention(self, months: int) -> None:
        if not self._known_partitions:
            return
        # Base the cutoff on the most recent partition, not wall-clock time,
        # so tests with historical data work correctly.
        newest = sorted(self._known_partitions)[-1]
        # Extract year/month from "data_points_YYYY_MM"
        parts = newest.split("_")
        ref_year, ref_month = int(parts[2]), int(parts[3])
        cutoff_month = ref_month - months
        cutoff_year = ref_year
        while cutoff_month <= 0:
            cutoff_month += 12
            cutoff_year -= 1
        cutoff_str = f"data_points_{cutoff_year:04d}_{cutoff_month:02d}"

        to_drop = [t for t in self._known_partitions if t < cutoff_str]
        for table in to_drop:
            self.conn.execute(f"DROP TABLE IF EXISTS {table}")
            self._known_partitions.discard(table)
        if to_drop:
            self.conn.commit()

    def close(self) -> None:
        self.conn.close()
