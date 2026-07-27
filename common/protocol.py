"""Codificación, envío y lectura de mensajes JSON del protocolo CTF."""

from __future__ import annotations

import json
import socket
from typing import Any

from common.constants import MAX_MESSAGE_SIZE


class ProtocolError(Exception):
    """Error producido por un mensaje que incumple el protocolo."""


def validate_basic_message(message: dict[str, Any]) -> None:
    if not isinstance(message, dict):
        raise ProtocolError("INVALID_JSON")

    if "type" not in message:
        raise ProtocolError("MISSING_FIELD")

    if not isinstance(message["type"], str) or not message["type"].strip():
        raise ProtocolError("INVALID_FIELD")


def encode_tcp_message(message: dict[str, Any]) -> bytes:
    validate_basic_message(message)

    try:
        text = json.dumps(message, ensure_ascii=False, separators=(",", ":"))
    except (TypeError, ValueError) as error:
        raise ProtocolError("INVALID_JSON") from error

    encoded = (text + "\n").encode("utf-8")
    if len(encoded) > MAX_MESSAGE_SIZE:
        raise ProtocolError("MESSAGE_TOO_LARGE")
    return encoded


def encode_udp_message(message: dict[str, Any]) -> bytes:
    validate_basic_message(message)

    try:
        encoded = json.dumps(
            message,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ProtocolError("INVALID_JSON") from error

    if len(encoded) > MAX_MESSAGE_SIZE:
        raise ProtocolError("MESSAGE_TOO_LARGE")
    return encoded


def decode_udp_message(data: bytes) -> dict[str, Any]:
    if len(data) > MAX_MESSAGE_SIZE:
        raise ProtocolError("MESSAGE_TOO_LARGE")

    try:
        text = data.decode("utf-8")
        message = json.loads(text)
    except UnicodeDecodeError as error:
        raise ProtocolError("INVALID_UTF8") from error
    except json.JSONDecodeError as error:
        raise ProtocolError("INVALID_JSON") from error

    validate_basic_message(message)
    return message


def send_tcp_message(sock: socket.socket, message: dict[str, Any]) -> None:
    sock.sendall(encode_tcp_message(message))


def send_udp_message(
    sock: socket.socket,
    message: dict[str, Any],
    address: tuple[str, int],
) -> None:
    sock.sendto(encode_udp_message(message), address)


class JsonLineBuffer:
    """Reconstruye mensajes TCP separados por saltos de línea."""

    def __init__(self) -> None:
        self._buffer = bytearray()

    def feed(self, data: bytes) -> list[dict[str, Any]]:
        if not isinstance(data, bytes):
            raise TypeError("data debe ser bytes")

        self._buffer.extend(data)
        messages: list[dict[str, Any]] = []

        while b"\n" in self._buffer:
            line, _, remaining = self._buffer.partition(b"\n")
            self._buffer = bytearray(remaining)

            if not line:
                raise ProtocolError("INVALID_JSON")
            if len(line) > MAX_MESSAGE_SIZE:
                raise ProtocolError("MESSAGE_TOO_LARGE")

            try:
                text = line.decode("utf-8")
                message = json.loads(text)
            except UnicodeDecodeError as error:
                raise ProtocolError("INVALID_UTF8") from error
            except json.JSONDecodeError as error:
                raise ProtocolError("INVALID_JSON") from error

            validate_basic_message(message)
            messages.append(message)

        if len(self._buffer) > MAX_MESSAGE_SIZE:
            raise ProtocolError("MESSAGE_TOO_LARGE")

        return messages

    @property
    def pending_bytes(self) -> int:
        return len(self._buffer)
