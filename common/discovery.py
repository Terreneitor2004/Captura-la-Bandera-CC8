"""Descubrimiento UDP de servidores CTF."""

import socket
import time
from typing import Any

from common.constants import DISCOVERY_PORT, PROTOCOL_VERSION
from common.protocol import ProtocolError, decode_udp_message, send_udp_message

_DISCOVER = {"type": "discover", "v": PROTOCOL_VERSION}


def _valid_server_info(message: dict[str, Any]) -> bool:
    port = message.get("tcp_port")
    return (
        message.get("type") == "server_info"
        and message.get("v") == PROTOCOL_VERSION
        and isinstance(port, int)
        and 1 <= port <= 65535
        and message.get("state") in {"lobby", "playing"}
        and isinstance(message.get("players"), int)
    )


def discover_server_at(host: str, timeout: float = 2.0) -> dict[str, Any] | None:
    """Pregunta directamente a una IP por UDP 8888 y obtiene su puerto TCP.

    Es la opción recomendada para Radmin VPN, donde el broadcast puede fallar.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(timeout)
        send_udp_message(sock, _DISCOVER, (host, DISCOVERY_PORT))
        end = time.monotonic() + timeout

        while time.monotonic() < end:
            try:
                data, address = sock.recvfrom(65535)
                message = decode_udp_message(data)
            except socket.timeout:
                return None
            except (OSError, ProtocolError):
                return None

            if _valid_server_info(message):
                return {**message, "ip": address[0]}
    return None


def discover_servers(timeout: float = 1.8) -> list[dict[str, Any]]:
    """Busca servidores mediante broadcast local/Radmin."""
    found: dict[tuple[str, int], dict[str, Any]] = {}

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(0.2)

        # Broadcast general, broadcast típico de Radmin y equipo local.
        for ip in ("255.255.255.255", "26.255.255.255", "127.0.0.1"):
            try:
                send_udp_message(sock, _DISCOVER, (ip, DISCOVERY_PORT))
            except OSError:
                pass

        end = time.monotonic() + timeout
        while time.monotonic() < end:
            try:
                data, address = sock.recvfrom(65535)
                message = decode_udp_message(data)
            except socket.timeout:
                continue
            except (OSError, ProtocolError):
                continue

            if _valid_server_info(message):
                port = int(message["tcp_port"])
                found[(address[0], port)] = {**message, "ip": address[0]}

    return list(found.values())
