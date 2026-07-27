"""Cliente TCP con recepción en segundo plano."""

from __future__ import annotations

import queue
import socket
import threading
from typing import Any

from common.constants import PROTOCOL_VERSION, RECV_SIZE
from common.protocol import JsonLineBuffer, ProtocolError, send_tcp_message


class CTFClient:
    def __init__(self, host: str, port: int, name: str) -> None:
        self.host = host
        self.port = port
        self.name = name
        self.sock: socket.socket | None = None
        self.running = threading.Event()
        self.incoming: queue.Queue[dict[str, Any]] = queue.Queue()
        self.send_lock = threading.Lock()
        self.receiver_thread: threading.Thread | None = None

    def connect(self, timeout: float = 5.0) -> None:
        self.sock = socket.create_connection((self.host, self.port), timeout=timeout)
        self.sock.settimeout(1.0)
        self.running.set()

        self.receiver_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receiver_thread.start()

        self.send(
            {
                "type": "join",
                "v": PROTOCOL_VERSION,
                "name": self.name,
            }
        )

    def send(self, message: dict[str, Any]) -> None:
        if self.sock is None:
            raise ConnectionError("El cliente no está conectado")

        with self.send_lock:
            send_tcp_message(self.sock, message)

    def send_input(self, dir_x: int, dir_y: int) -> None:
        self.send({"type": "input", "dir": {"x": dir_x, "y": dir_y}})

    def interact(self) -> None:
        self.send({"type": "interact"})

    def close(self) -> None:
        if not self.running.is_set() and self.sock is None:
            return

        self.running.clear()
        if self.sock is not None:
            try:
                self.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None

    def poll_messages(self, limit: int = 100) -> list[dict[str, Any]]:
        messages: list[dict[str, Any]] = []
        for _ in range(limit):
            try:
                messages.append(self.incoming.get_nowait())
            except queue.Empty:
                break
        return messages

    def _receive_loop(self) -> None:
        assert self.sock is not None
        buffer = JsonLineBuffer()

        try:
            while self.running.is_set():
                try:
                    data = self.sock.recv(RECV_SIZE)
                except socket.timeout:
                    continue

                if not data:
                    break

                try:
                    messages = buffer.feed(data)
                except ProtocolError as error:
                    self.incoming.put({"type": "error", "reason": str(error)})
                    continue

                for message in messages:
                    self.incoming.put(message)

        except (ConnectionError, OSError) as error:
            if self.running.is_set():
                self.incoming.put(
                    {"type": "error", "reason": f"SERVER_DISCONNECTED: {error}"}
                )
        finally:
            was_running = self.running.is_set()
            self.running.clear()
            if was_running:
                self.incoming.put({"type": "disconnected"})
