"""Tests for config loading."""

import os
import tempfile
import textwrap

from givlocal.config import AppConfig, load_config


def test_config_loads_from_yaml():
    """Load a full config from YAML and assert all values match."""
    yaml_content = textwrap.dedent("""\
        inverters:
          - host: 192.168.1.100
            port: 8899
          - host: 192.168.1.101
            port: 9000
        storage:
          app_db: data/myapp.db
          metrics_db: data/mymetrics.db
          retention_months: 6
          compression: false
        server:
          host: 127.0.0.1
          port: 8080
        auth_required: false
        poll_interval: 60
        full_refresh_interval: 600
    """)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        tmp_path = f.name

    try:
        config = load_config(tmp_path)

        assert isinstance(config, AppConfig)

        assert len(config.inverters) == 2
        assert config.inverters[0].host == "192.168.1.100"
        assert config.inverters[0].port == 8899
        assert config.inverters[1].host == "192.168.1.101"
        assert config.inverters[1].port == 9000

        assert config.storage.app_db == "data/myapp.db"
        assert config.storage.metrics_db == "data/mymetrics.db"
        assert config.storage.retention_months == 6
        assert config.storage.compression is False

        assert config.server.host == "127.0.0.1"
        assert config.server.port == 8080

        assert config.auth_required is False
        assert config.poll_interval == 60
        assert config.full_refresh_interval == 600
    finally:
        os.unlink(tmp_path)


def test_config_defaults():
    """Minimal config (just inverters with host) should yield expected defaults."""
    yaml_content = textwrap.dedent("""\
        inverters:
          - host: 10.0.0.1
    """)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(yaml_content)
        tmp_path = f.name

    try:
        config = load_config(tmp_path)

        assert len(config.inverters) == 1
        assert config.inverters[0].host == "10.0.0.1"
        assert config.inverters[0].port == 8899

        assert config.storage.retention_months == 0
        assert config.storage.compression is True
        assert config.storage.app_db == "data/app.db"
        assert config.storage.metrics_db == "data/metrics.db"

        assert config.server.host == "0.0.0.0"
        assert config.server.port == 8099

        assert config.auth_required is True
        assert config.poll_interval == 30
        assert config.full_refresh_interval == 300
    finally:
        os.unlink(tmp_path)
