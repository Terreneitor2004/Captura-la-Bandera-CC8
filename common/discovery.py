"""Descubrimiento UDP de servidores CTF disponibles."""

from __future__ import annotations

import socket
import time
from typing import Any

from common.constants import DISCOVERY_PORT, PROTOCOL_VERSION
from common.protocol import ProtocolError, decode_udp_message, send_udp_message

_DISCOVER = {"type": "discover", "v": PROTOCOL_VERSION}


def _valid_server_info(message: dict[str, Any]) -> bool:
    """Comprueba que la respuesta tenga el formato CTF v1."""
    port = message.get("tcp_port")
    return (
        message.get("type") == "server_info"
        and message.get("v") == PROTOCOL_VERSION
        and isinstance(message.get("name"), str)
        and isinstance(port, int)
        and 1 <= port <= 65535
        and message.get("state") in {"lobby", "playing"}
        and isinstance(message.get("players"), int)
    )


def _local_ipv4_addresses() -> set[str]:
    """Obtiene direcciones IPv4 del equipo sin usar librerías externas."""
    addresses: set[str] = set()
    try:
        for item in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            addresses.add(item[4][0])
    except OSError:
        pass

    # Esta conexión UDP no envía datos; solo permite conocer la interfaz de salida.
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(("8.8.8.8", 80))
            addresses.add(probe.getsockname()[0])
    except OSError:
        pass
    return {ip for ip in addresses if ip and not ip.startswith("127.")}


def broadcast_targets() -> list[str]:
    """Direcciones a las que se enviará el mensaje discover.

    Incluye broadcast general, broadcast de Radmin VPN, localhost y una
    aproximación /24 para cada interfaz local. Se eliminan duplicados.
    """
    targets = {"255.255.255.255", "26.255.255.255", "127.0.0.1"}
    for ip in _local_ipv4_addresses():
        parts = ip.split(".")
        if len(parts) == 4:
            targets.add(".".join((*parts[:3], "255")))
    return sorted(targets)


def discover_server_at(host: str, timeout: float = 2.0) -> dict[str, Any] | None:
    """Pregunta directamente a una IP por UDP 8888 y obtiene su puerto TCP."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(0.25)
        end = time.monotonic() + timeout

        # Repetimos la consulta para tolerar pérdida de paquetes en una VPN.
        next_send = 0.0
        while time.monotonic() < end:
            now = time.monotonic()
            if now >= next_send:
                try:
                    send_udp_message(sock, _DISCOVER, (host, DISCOVERY_PORT))
                except OSError:
                    return None
                next_send = now + 0.45

            try:
                data, address = sock.recvfrom(65535)
                message = decode_udp_message(data)
            except socket.timeout:
                continue
            except (OSError, ProtocolError):
                continue

            if _valid_server_info(message):
                return {**message, "ip": address[0]}
    return None


def discover_servers(timeout: float = 2.6) -> list[dict[str, Any]]:
    """Busca servidores activos mediante broadcast UDP en el puerto 8888.

    Se envían varias rondas para funcionar mejor en Wi-Fi y Radmin VPN. Cada
    servidor válido se conserva una sola vez usando su IP y puerto TCP.
    """
    found: dict[tuple[str, int], dict[str, Any]] = {}
    targets = broadcast_targets()

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(0.12)

        end = time.monotonic() + timeout
        next_broadcast = 0.0
        rounds = 0

        while time.monotonic() < end:
            now = time.monotonic()
            if rounds < 4 and now >= next_broadcast:
                for ip in targets:
                    try:
                        send_udp_message(sock, _DISCOVER, (ip, DISCOVERY_PORT))
                    except OSError:
                        pass
                rounds += 1
                next_broadcast = now + 0.45

            try:
                data, address = sock.recvfrom(65535)
                message = decode_udp_message(data)
            except socket.timeout:
                continue
            except (OSError, ProtocolError):
                continue

            if _valid_server_info(message):
                port = int(message["tcp_port"])
                found[(address[0], port)] = {
                    **message,
                    "ip": address[0],
                    "found_by": "broadcast",
                }

    # Primero muestra partidas disponibles en lobby y luego ordena por nombre/IP.
    return sorted(
        found.values(),
        key=lambda server: (
            server.get("state") != "lobby",
            str(server.get("name", "")).lower(),
            str(server.get("ip", "")),
            int(server.get("tcp_port", 0)),
        ),
    )
