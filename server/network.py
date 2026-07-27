"""Servidor TCP multicliente y descubrimiento UDP."""

import socket
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from common import constants as C
from common.protocol import (
    JsonLineBuffer,
    ProtocolError,
    decode_udp_message,
    send_tcp_message,
    send_udp_message,
)
from server.game_state import GameState


@dataclass
class ClientSession:
    sock: socket.socket
    address: tuple[str, int]
    player_id: str | None = None
    joined: bool = False
    lock: threading.Lock = field(default_factory=threading.Lock)

    def send(self, message: dict[str, Any]) -> None:
        with self.lock:
            send_tcp_message(self.sock, message)

    def close(self) -> None:
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            self.sock.close()
        except OSError:
            pass


class CTFServer:
    def __init__(
        self,
        host: str = "0.0.0.0",
        tcp_port: int = C.DEFAULT_TCP_PORT,
        name: str = "Servidor Python Arcade",
    ) -> None:
        self.host, self.tcp_port, self.name = host, tcp_port, name
        self.game = GameState()
        self.running = threading.Event()
        self.running.set()
        self.tcp_socket: socket.socket | None = None
        self.udp_socket: socket.socket | None = None
        self.sessions: dict[socket.socket, ClientSession] = {}
        self.sessions_lock = threading.RLock()
        self.events: deque[str] = deque(maxlen=30)
        self.events_lock = threading.Lock()
        self.last_countdown: int | None = None

    def start(self) -> None:
        self.tcp_socket = self._make_socket(socket.SOCK_STREAM, (self.host, self.tcp_port))
        self.tcp_socket.listen(C.MAX_PLAYERS)
        self.udp_socket = self._make_socket(socket.SOCK_DGRAM, ("", C.DISCOVERY_PORT))
        self._thread(self._accept_loop)
        self._thread(self._discovery_loop)
        self._thread(self._game_loop)
        self.log_event(f"[SERVIDOR] TCP activo en {self.host}:{self.tcp_port}")
        self.log_event(f"[DESCUBRIMIENTO] UDP activo en {C.DISCOVERY_PORT}")
        self.log_event("[CONTROL] Presiona ESPACIO o el botón para iniciar")

    def stop(self) -> None:
        if not self.running.is_set():
            return
        self.log_event("[SERVIDOR] Cerrando conexiones...")
        self.running.clear()
        for sock in (self.tcp_socket, self.udp_socket):
            if sock:
                try:
                    sock.close()
                except OSError:
                    pass
        with self.sessions_lock:
            sessions = list(self.sessions.values())
            self.sessions.clear()
        for session in sessions:
            session.close()

    def log_event(self, message: str) -> None:
        line = f"[{time.strftime('%H:%M:%S')}] {message}"
        print(line, flush=True)
        with self.events_lock:
            self.events.append(line)

    def recent_events(self, limit: int = 6) -> list[str]:
        with self.events_lock:
            return list(self.events)[-max(1, limit):]

    def can_start_game(self) -> bool:
        snapshot = self.game.public_snapshot()
        return snapshot["phase"] == C.STATE_LOBBY and len(snapshot["players"]) >= C.MIN_PLAYERS_TO_START

    def start_game(self) -> tuple[bool, str]:
        started, message = self.game.request_start()
        self.log_event(f"[PARTIDA] {message}" if started else f"[AVISO] {message}")
        return started, message

    @staticmethod
    def _make_socket(kind: int, address: tuple[str, int]) -> socket.socket:
        sock = socket.socket(socket.AF_INET, kind)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(address)
        sock.settimeout(0.5)
        return sock

    @staticmethod
    def _thread(target: Any, *args: Any) -> None:
        threading.Thread(target=target, args=args, daemon=True).start()

    def _accept_loop(self) -> None:
        assert self.tcp_socket is not None
        while self.running.is_set():
            try:
                client, address = self.tcp_socket.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            client.settimeout(1.0)
            session = ClientSession(client, address)
            with self.sessions_lock:
                self.sessions[client] = session
            self.log_event(f"[CONEXIÓN] Nueva conexión desde {address[0]}:{address[1]}")
            self._thread(self._client_loop, session)

    def _client_loop(self, session: ClientSession) -> None:
        buffer = JsonLineBuffer()
        try:
            while self.running.is_set():
                try:
                    data = session.sock.recv(C.RECV_SIZE)
                except socket.timeout:
                    continue
                if not data:
                    break
                try:
                    for message in buffer.feed(data):
                        self._handle(session, message)
                except ProtocolError as error:
                    self.log_event(f"[PROTOCOLO] Mensaje inválido de {session.address[0]}: {error}")
                    self._send(session, {"type": "error", "reason": str(error)})
                    if str(error) == "MESSAGE_TOO_LARGE":
                        break
        except OSError:
            pass
        finally:
            self._disconnect(session)

    def _handle(self, session: ClientSession, message: dict[str, Any]) -> None:
        kind = message.get("type")
        if kind == "join":
            self._join(session, message)
            return
        if not session.joined or session.player_id is None:
            self._error(session, "NOT_JOINED")
            return

        if kind == "input":
            direction = message.get("dir")
            if not isinstance(direction, dict):
                self._error(session, "MISSING_FIELD")
                return
            x, y = direction.get("x"), direction.get("y")
            if not isinstance(x, int) or not isinstance(y, int):
                self._error(session, "INVALID_FIELD")
            elif not self.game.set_direction(session.player_id, x, y):
                self._error(session, "INVALID_PHASE")
        elif kind == "interact":
            # "interact" no lleva campos. Si el jugador está lejos, ya posee
            # la bandera o pulsa E dos veces, la segunda acción es un no-op.
            # No enviamos INVALID_ACTION porque no forma parte del catálogo
            # común de errores y algunos clientes estrictos cierran la sesión.
            self.game.interact(session.player_id)
        else:
            self._error(session, "UNKNOWN_TYPE")

    def _join(self, session: ClientSession, message: dict[str, Any]) -> None:
        if session.joined:
            self._error(session, "INVALID_PHASE")
            return
        if message.get("v") != C.PROTOCOL_VERSION:
            self._error(session, "VERSION_MISMATCH")
            session.close()
            return

        name = message.get("name")
        name = name.strip() if isinstance(name, str) else ""
        if not name or len(name) > C.MAX_NAME_LENGTH or "\n" in name:
            self._error(session, "NAME_INVALID")
            return

        with self.game.lock:
            if self.game.phase != C.STATE_LOBBY:
                self._error(session, "INVALID_PHASE")
                return
            if len(self.game.players) >= C.MAX_PLAYERS:
                self._error(session, "LOBBY_FULL")
                session.close()
                return

        player_id = uuid.uuid4().hex[:8]
        player = self.game.add_player(player_id, name)
        session.player_id, session.joined = player_id, True
        self.log_event(
            f"[LOBBY] Jugador '{name}' se unió | id={player_id} | "
            f"spawn=({player.x:.0f},{player.y:.0f})"
        )

        config = {
            "map_size": C.MAP_SIZE,
            "circle_radius": C.CIRCLE_RADIUS,
            "player_radius": C.PLAYER_RADIUS,
            "interact_radius": C.INTERACT_RADIUS,
            "speed": C.PLAYER_SPEED,
            "tick_rate": C.TICK_RATE,
        }
        self._send(session, {"type": "welcome", "player_id": player_id, "config": config})
        self.log_event(f"[PROTOCOLO] 'welcome' enviado a '{name}'")
        self.broadcast(self.game.lobby_message())
        self.log_event(f"[LOBBY] Lista actualizada: {len(self.game.players)} jugador(es)")

    def _discovery_loop(self) -> None:
        assert self.udp_socket is not None
        while self.running.is_set():
            try:
                data, address = self.udp_socket.recvfrom(65535)
                message = decode_udp_message(data)
            except socket.timeout:
                continue
            except (OSError, ProtocolError):
                continue

            if message.get("type") == "discover" and message.get("v") == C.PROTOCOL_VERSION:
                try:
                    send_udp_message(self.udp_socket, self._server_info_message(), address)
                except OSError:
                    pass

    def _server_info_message(self) -> dict[str, Any]:
        snapshot = self.game.public_snapshot()
        # CTF v1 solo permite "lobby" o "playing" en server_info.
        state = C.STATE_LOBBY if snapshot["phase"] == C.STATE_LOBBY else C.STATE_PLAYING
        return {
            "type": "server_info",
            "v": C.PROTOCOL_VERSION,
            "name": self.name,
            "tcp_port": self.tcp_port,
            "state": state,
            "players": len(snapshot["players"]),
        }

    def _publish_protocol_messages(self, previous_phase: str) -> str:
        countdown = self.game.countdown_seconds()
        if countdown != self.last_countdown:
            self.last_countdown = countdown
            if countdown is not None:
                self.broadcast({"type": "countdown", "seconds": countdown})
                self.log_event(f"[COUNTDOWN] La partida inicia en {countdown}")

        if self.game.consume_start_message():
            self.broadcast({"type": "start"})
            self.log_event("[PARTIDA] Inicio enviado a los clientes")

        winner = self.game.consume_game_over_message()
        if winner:
            self.broadcast({"type": "game_over", "winner": winner})
            self.log_event(f"[FIN] Ganador: '{self.game.player_name(winner) or winner}'")

        phase = self.game.phase
        # state pertenece únicamente a la fase playing. Después de game_over
        # no debe enviarse otro state, porque la sesión ya está finalizada.
        if phase == C.STATE_PLAYING:
            self.broadcast(self.game.state_message())
        if phase == C.STATE_LOBBY and phase != previous_phase:
            self.broadcast(self.game.lobby_message())
            self.log_event("[LOBBY] Nueva ronda lista")
        return phase

    def _game_loop(self) -> None:
        interval = 1 / C.TICK_RATE
        previous = time.monotonic()
        previous_phase = self.game.phase

        while self.running.is_set():
            started = time.monotonic()
            self.game.update(min(started - previous, 0.1))
            previous = started
            previous_phase = self._publish_protocol_messages(previous_phase)
            time.sleep(max(0, interval - (time.monotonic() - started)))

    def broadcast(self, message: dict[str, Any]) -> None:
        with self.sessions_lock:
            sessions = [s for s in self.sessions.values() if s.joined]
        for session in sessions:
            try:
                session.send(message)
            except OSError:
                self._disconnect(session)

    def _send(self, session: ClientSession, message: dict[str, Any]) -> None:
        try:
            session.send(message)
        except OSError:
            pass

    def _error(self, session: ClientSession, reason: str) -> None:
        self._send(session, {"type": "error", "reason": reason})

    def _disconnect(self, session: ClientSession) -> None:
        with self.sessions_lock:
            removed = self.sessions.pop(session.sock, None)
        session.close()
        if removed is None:
            return

        name = self.game.player_name(session.player_id)
        if session.player_id:
            self.game.remove_player(session.player_id)
        label = f"Jugador '{name}'" if name else "Cliente sin registrar"
        self.log_event(f"[DESCONEXIÓN] {label} salió ({session.address[0]}:{session.address[1]})")
        if self.game.phase in {C.STATE_LOBBY, C.STATE_COUNTDOWN}:
            self.broadcast(self.game.lobby_message())
