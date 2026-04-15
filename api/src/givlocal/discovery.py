"""Network auto-discovery for GivEnergy inverters."""

import ipaddress
import socket
from concurrent.futures import ThreadPoolExecutor


def generate_ip_range(cidr: str) -> list[str]:
    """Generate host IPs from CIDR notation."""
    network = ipaddress.ip_network(cidr, strict=False)
    return [str(ip) for ip in network.hosts()]


def _probe(host: str, port: int, timeout: float) -> str | None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        if sock.connect_ex((host, port)) == 0:
            return host
    return None


def scan_for_inverters(
    hosts: list[str],
    port: int = 8899,
    timeout: float = 0.5,
    workers: int = 64,
) -> list[str]:
    """Try connecting to each host on the given port, in parallel.

    Returns a list of IPs where the connection succeeded. With 64 workers
    and a 0.5s timeout, a /24 scan completes in ~2s instead of ~127s.
    """
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = pool.map(lambda h: _probe(h, port, timeout), hosts)
    return [r for r in results if r is not None]


def discover_inverters(network: str = "192.168.1.0/24", port: int = 8899, timeout: float = 0.5) -> list[str]:
    """Discover GivEnergy inverters on the local network.

    Convenience function: generates IP range from CIDR then scans for open ports.
    """
    hosts = generate_ip_range(network)
    return scan_for_inverters(hosts, port=port, timeout=timeout)
