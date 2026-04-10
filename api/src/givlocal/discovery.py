"""Network auto-discovery for GivEnergy inverters."""

import ipaddress
import socket


def generate_ip_range(cidr: str) -> list[str]:
    """Generate host IPs from CIDR notation."""
    network = ipaddress.ip_network(cidr, strict=False)
    return [str(ip) for ip in network.hosts()]


def scan_for_inverters(hosts: list[str], port: int = 8899, timeout: float = 0.5) -> list[str]:
    """Try connecting to each host on the given port.

    Returns a list of IPs where the connection succeeded.
    """
    found = []
    for host in hosts:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            if result == 0:
                found.append(host)
    return found


def discover_inverters(network: str = "192.168.1.0/24", port: int = 8899, timeout: float = 0.5) -> list[str]:
    """Discover GivEnergy inverters on the local network.

    Convenience function: generates IP range from CIDR then scans for open ports.
    """
    hosts = generate_ip_range(network)
    return scan_for_inverters(hosts, port=port, timeout=timeout)
