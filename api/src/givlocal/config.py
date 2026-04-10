"""Configuration loading for givlocal."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import yaml


@dataclass
class InverterConfig:
    """Configuration for a single GivEnergy inverter."""

    host: str
    port: int = 8899


@dataclass
class StorageConfig:
    """Database storage configuration."""

    app_db: str = "data/app.db"
    metrics_db: str = "data/metrics.db"
    retention_months: int = 0
    compression: bool = True


@dataclass
class ServerConfig:
    """HTTP server configuration."""

    host: str = "0.0.0.0"
    port: int = 8099


@dataclass
class AppConfig:
    """Top-level application configuration."""

    inverters: list[InverterConfig]
    storage: StorageConfig = field(default_factory=StorageConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    auth_required: bool = True
    poll_interval: int = 30
    full_refresh_interval: int = 300


def _load_inverters(raw: list[dict[str, Any]]) -> list[InverterConfig]:
    result = []
    for item in raw:
        result.append(
            InverterConfig(
                host=item["host"],
                port=int(item.get("port", 8899)),
            )
        )
    return result


def _load_storage(raw: dict[str, Any]) -> StorageConfig:
    return StorageConfig(
        app_db=raw.get("app_db", "data/app.db"),
        metrics_db=raw.get("metrics_db", "data/metrics.db"),
        retention_months=int(raw.get("retention_months", 0)),
        compression=bool(raw.get("compression", True)),
    )


def _load_server(raw: dict[str, Any]) -> ServerConfig:
    return ServerConfig(
        host=raw.get("host", "0.0.0.0"),
        port=int(raw.get("port", 8099)),
    )


def load_config(path: str) -> AppConfig:
    """Read a YAML config file and return an AppConfig instance."""
    with open(path, "r") as fh:
        data: dict[str, Any] = yaml.safe_load(fh) or {}

    inverters = _load_inverters(data.get("inverters", []))

    storage_raw = data.get("storage", {})
    storage = _load_storage(storage_raw) if storage_raw else StorageConfig()

    server_raw = data.get("server", {})
    server = _load_server(server_raw) if server_raw else ServerConfig()

    return AppConfig(
        inverters=inverters,
        storage=storage,
        server=server,
        auth_required=bool(data.get("auth_required", True)),
        poll_interval=int(data.get("poll_interval", 30)),
        full_refresh_interval=int(data.get("full_refresh_interval", 300)),
    )
