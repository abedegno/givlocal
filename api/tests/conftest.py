"""Shared pytest fixtures for givlocal tests."""

import textwrap

import pytest


@pytest.fixture
def tmp_config(tmp_path):
    """Create a temporary config YAML file and return its path."""
    yaml_content = textwrap.dedent("""\
        inverters:
          - host: 192.168.1.100
            port: 8899
        storage:
          app_db: data/app.db
          metrics_db: data/metrics.db
          retention_months: 0
          compression: true
        server:
          host: "0.0.0.0"
          port: 8099
        auth_required: true
        poll_interval: 30
        full_refresh_interval: 300
    """)
    config_file = tmp_path / "config.yaml"
    config_file.write_text(yaml_content)
    return str(config_file)
