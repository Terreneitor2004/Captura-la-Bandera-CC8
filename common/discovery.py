"""Descubrimiento UDP de servidores CTF en la red local."""

from __future__ import annotations

import socket
import time
from typing import Any

from common.constants import DISCOVERY_PORT, PROTOCOL_VERSION
from common.protocol import ProtocolError, decode_udp_message, send_udp_message


def discover_servers(timeout: float = 1.5) -> list[dict[str, Any]]:
    """Envía broadcast UDP y devuelve los servidores encontrados."""

    found: dict[tuple[str, int], dict[str, Any]] = {}

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_socket.settimeout(0.2)

        request = {"type": "discover", "v": PROTOCOL_VERSION}

        # Broadcast de red y loopback para que también funcione en una sola PC.
        targets = [
            ("255.255.255.255", DISCOVERY_PORT),
            ("127.0.0.1", DISCOVERY_PORT),
        ]
        for target in targets:
            try:
                send_udp_message(udp_socket, request, target)
            except OSError:
                pass

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                data, address = udp_socket.recvfrom(65535)
            except socket.timeout:
                continue
            except OSError:
                break

            try:
                message = decode_udp_message(data)
            except ProtocolError:
                continue

            if message.get("type") != "server_info":
                continue
            if message.get("v") != PROTOCOL_VERSION:
                continue
            if not isinstance(message.get("tcp_port"), int):
                continue

            item = dict(message)
            item["ip"] = address[0]
            found[(address[0], message["tcp_port"])] = item

    return list(found.values())
