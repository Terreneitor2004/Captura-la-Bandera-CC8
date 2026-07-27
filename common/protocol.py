"""Mensajes JSON del protocolo CTF."""

import json
import socket
from typing import Any

from common.constants import MAX_MESSAGE_SIZE


class ProtocolError(Exception):
    pass


def _validate(message: Any) -> dict[str, Any]:
    if not isinstance(message, dict):
        raise ProtocolError("INVALID_JSON")
    if "type" not in message:
        raise ProtocolError("MISSING_FIELD")
    if not isinstance(message["type"], str) or not message["type"].strip():
        raise ProtocolError("INVALID_FIELD")
    return message


def _encode(message: dict[str, Any], newline: bool = False) -> bytes:
    _validate(message)
    try:
        text = json.dumps(message, ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError) as error:
        raise ProtocolError("INVALID_JSON") from error
    data = (text + ("\n" if newline else "")).encode("utf-8")
    if len(data) > MAX_MESSAGE_SIZE:
        raise ProtocolError("MESSAGE_TOO_LARGE")
    return data


def _decode(data: bytes) -> dict[str, Any]:
    if len(data) > MAX_MESSAGE_SIZE:
        raise ProtocolError("MESSAGE_TOO_LARGE")
    try:
        return _validate(json.loads(data.decode("utf-8")))
    except UnicodeDecodeError as error:
        raise ProtocolError("INVALID_JSON") from error
    except json.JSONDecodeError as error:
        raise ProtocolError("INVALID_JSON") from error


def encode_tcp_message(message: dict[str, Any]) -> bytes:
    return _encode(message, newline=True)


def encode_udp_message(message: dict[str, Any]) -> bytes:
    return _encode(message)


def decode_udp_message(data: bytes) -> dict[str, Any]:
    return _decode(data)


def send_tcp_message(sock: socket.socket, message: dict[str, Any]) -> None:
    sock.sendall(encode_tcp_message(message))


def send_udp_message(
    sock: socket.socket,
    message: dict[str, Any],
    address: tuple[str, int],
) -> None:
    sock.sendto(encode_udp_message(message), address)


class JsonLineBuffer:
    """Une fragmentos TCP y extrae cada JSON terminado en ``\n``."""

    def __init__(self) -> None:
        self._buffer = bytearray()

    def feed(self, data: bytes) -> list[dict[str, Any]]:
        if not isinstance(data, bytes):
            raise TypeError("data debe ser bytes")
        self._buffer.extend(data)
        messages = []

        while True:
            position = self._buffer.find(b"\n")
            if position < 0:
                break
            line = bytes(self._buffer[:position])
            del self._buffer[: position + 1]
            if not line:
                raise ProtocolError("INVALID_JSON")
            messages.append(_decode(line))

        if len(self._buffer) > MAX_MESSAGE_SIZE:
            raise ProtocolError("MESSAGE_TOO_LARGE")
        return messages

    @property
    def pending_bytes(self) -> int:
        return len(self._buffer)
