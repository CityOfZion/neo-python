import socket
import ipaddress


def hostname_to_ip(hostname: str) -> str:
    """
    Args:
        hostname: e.g. seed1.ngd.network

    Raises:
        socket.gaierror if hostname could not be resolved
    Returns: host e.g. 10.1.1.3

    """
    return socket.gethostbyname(hostname)


def is_ip_address(hostname: str) -> bool:
    host = hostname.split(':')[0]
    try:
        ip = ipaddress.ip_address(host)
        return True
    except ValueError:
        return False
