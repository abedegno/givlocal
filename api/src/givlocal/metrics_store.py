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
        # WAL + busy_timeout: concurrent readers during the poller's writes
        # no longer raise "database is locked".
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA busy_timeout=5000")
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

    def _partitions_in_range(self, start_ts: int, end_ts: int) -> list[str]:
        """Return partitions whose YYYY_MM label overlaps [start_ts, end_ts]."""
        lo = self._partition_name(start_ts)
        hi = self._partition_name(end_ts)
        return sorted(t for t in self._known_partitions if lo <= t <= hi)

    def query_data_points(
        self,
        serial: str,
        start_ts: int,
        end_ts: int,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[sqlite3.Row]:
        """Return ordered rows in the range, optionally paginated in SQL."""
        partitions = self._partitions_in_range(start_ts, end_ts)
        if not partitions:
            return []
        # UNION ALL the relevant partitions and let SQLite do the LIMIT/OFFSET,
        # so we don't load the whole range into Python just to slice it.
        union = "\n  UNION ALL\n".join(
            f"SELECT timestamp, data FROM {t} WHERE inverter_serial = ? AND timestamp BETWEEN ? AND ?"
            for t in partitions
        )
        sql = f"{union}\nORDER BY timestamp"
        params: list = []
        for _ in partitions:
            params += [serial, start_ts, end_ts]
        if limit is not None:
            sql += " LIMIT ? OFFSET ?"
            params += [limit, offset]
        return self.conn.execute(sql, params).fetchall()

    def count_data_points(self, serial: str, start_ts: int, end_ts: int) -> int:
        partitions = self._partitions_in_range(start_ts, end_ts)
        total = 0
        for t in partitions:
            row = self.conn.execute(
                f"SELECT COUNT(*) FROM {t} WHERE inverter_serial = ? AND timestamp BETWEEN ? AND ?",
                (serial, start_ts, end_ts),
            ).fetchone()
            total += row[0]
        return total

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

    def apply_retention(self, months: int, reference: datetime | None = None) -> None:
        """Drop partitions older than `months` before the reference point.

        `reference` defaults to the newest partition (useful for tests with
        historical fixture data); production callers should pass
        `datetime.now(tz=timezone.utc)` so retention tracks wall-clock time.
        """
        if not self._known_partitions:
            return
        if reference is not None:
            ref_year, ref_month = reference.year, reference.month
        else:
            newest = sorted(self._known_partitions)[-1]
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
