"""Tests for network auto-discovery."""

from unittest.mock import MagicMock, patch

from givlocal.discovery import generate_ip_range, scan_for_inverters


def test_generate_ip_range():
    """Test that generate_ip_range produces correct host IPs for a /30 network."""
    hosts = generate_ip_range("192.168.1.0/30")
    assert hosts == ["192.168.1.1", "192.168.1.2"]


def test_scan_finds_open_port():
    """Mock socket.connect_ex returning 0 — host should appear in results."""
    with patch("givlocal.discovery.socket.socket") as mock_sock_cls:
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 0
        mock_sock_cls.return_value.__enter__ = MagicMock(return_value=mock_sock)
        mock_sock_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = scan_for_inverters(["192.168.1.1"])

    assert "192.168.1.1" in result


def test_scan_skips_closed_port():
    """Mock socket.connect_ex returning 1 — results should be empty."""
    with patch("givlocal.discovery.socket.socket") as mock_sock_cls:
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 1
        mock_sock_cls.return_value.__enter__ = MagicMock(return_value=mock_sock)
        mock_sock_cls.return_value.__exit__ = MagicMock(return_value=False)

        result = scan_for_inverters(["192.168.1.1"])

    assert result == []
