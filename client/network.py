"""Cliente TCP del juego."""

import queue
import socket
import threading
from typing import Any

from common.constants import PROTOCOL_VERSION, RECV_SIZE
from common.protocol import JsonLineBuffer, ProtocolError, send_tcp_message


class CTFClient:
    def __init__(self, host: str, port: int, name: str) -> None:
        self.host, self.port, self.name = host, port, name
        self.sock: socket.socket | None = None
        self.running = threading.Event()
        self.incoming: queue.Queue[dict[str, Any]] = queue.Queue()
        self.send_lock = threading.Lock()

    def connect(self, timeout: float = 5.0) -> None:
        self.sock = socket.create_connection((self.host, self.port), timeout=timeout)
        self.sock.settimeout(1.0)
        self.running.set()
        threading.Thread(target=self._receive_loop, daemon=True).start()
        self.send({"type": "join", "v": PROTOCOL_VERSION, "name": self.name})

    def send(self, message: dict[str, Any]) -> None:
        if self.sock is None:
            raise ConnectionError("El cliente no está conectado")
        with self.send_lock:
            send_tcp_message(self.sock, message)

    def send_input(self, x: int, y: int) -> None:
        self.send({"type": "input", "dir": {"x": x, "y": y}})

    def interact(self) -> None:
        self.send({"type": "interact"})

    def poll_messages(self, limit: int = 100) -> list[dict[str, Any]]:
        messages = []
        for _ in range(limit):
            try:
                messages.append(self.incoming.get_nowait())
            except queue.Empty:
                break
        return messages

    def close(self) -> None:
        self.running.clear()
        sock, self.sock = self.sock, None
        if sock:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                sock.close()
            except OSError:
                pass

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
                    for message in buffer.feed(data):
                        self.incoming.put(message)
                except ProtocolError as error:
                    self.incoming.put({"type": "error", "reason": str(error)})
        except OSError as error:
            if self.running.is_set():
                self.incoming.put({"type": "error", "reason": f"SERVER_DISCONNECTED: {error}"})
        finally:
            connected = self.running.is_set()
            self.running.clear()
            if connected:
                self.incoming.put({"type": "disconnected"})
