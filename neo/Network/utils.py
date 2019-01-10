import socket
import ipaddress


def hostname_to_ip(hostname):
    return socket.gethostbyname(hostname)


def is_ip_address(hostname):
    host = hostname.split(':')[0]
    try:
        ip = ipaddress.ip_address(host)
        return True
    except ValueError:
        return False
