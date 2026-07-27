"""Descubrimiento UDP de servidores CTF."""

import socket
import time
from typing import Any

from common.constants import DISCOVERY_PORT, PROTOCOL_VERSION
from common.protocol import ProtocolError, decode_udp_message, send_udp_message


def discover_servers(timeout: float = 1.5) -> list[dict[str, Any]]:
    found: dict[tuple[str, int], dict[str, Any]] = {}
    request = {"type": "discover", "v": PROTOCOL_VERSION}

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(0.2)

        for ip in ("255.255.255.255", "26.255.255.255", "127.0.0.1"):
            try:
                send_udp_message(sock, request, (ip, DISCOVERY_PORT))
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
                break

            port = message.get("tcp_port")
            if (
                message.get("type") == "server_info"
                and message.get("v") == PROTOCOL_VERSION
                and isinstance(port, int)
            ):
                item = {**message, "ip": address[0]}
                found[(address[0], port)] = item

    return list(found.values())
