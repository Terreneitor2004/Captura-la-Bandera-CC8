"""Servidor TCP multicliente y descubrimiento UDP."""

from __future__ import annotations

import socket
import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from common.constants import (
    CIRCLE_RADIUS,
    DEFAULT_TCP_PORT,
    DISCOVERY_PORT,
    INTERACT_RADIUS,
    MAP_SIZE,
    MAX_NAME_LENGTH,
    MAX_PLAYERS,
    MIN_PLAYERS_TO_START,
    PLAYER_RADIUS,
    PLAYER_SPEED,
    PROTOCOL_VERSION,
    RECV_SIZE,
    STATE_COUNTDOWN,
    STATE_FINISHED,
    STATE_LOBBY,
    STATE_PLAYING,
    TICK_RATE,
)
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
    send_lock: threading.Lock = field(default_factory=threading.Lock)

    def send(self, message: dict[str, Any]) -> None:
        with self.send_lock:
            send_tcp_message(self.sock, message)


class CTFServer:
    """Servidor autoritativo de Captura la Bandera."""

    def __init__(
        self,
        host: str = "0.0.0.0",
        tcp_port: int = DEFAULT_TCP_PORT,
        name: str = "Servidor Python Arcade",
    ) -> None:
        self.host = host
        self.tcp_port = tcp_port
        self.name = name
        self.game = GameState()

        self.running = threading.Event()
        self.running.set()

        self.tcp_socket: socket.socket | None = None
        self.udp_socket: socket.socket | None = None
        self.sessions: dict[socket.socket, ClientSession] = {}
        self.sessions_lock = threading.RLock()
        self.threads: list[threading.Thread] = []
        self._last_countdown_value: int | None = None

        # Historial corto para mostrar eventos tanto en la terminal como en
        # la ventana gráfica del servidor.
        self._events: deque[str] = deque(maxlen=30)
        self._events_lock = threading.Lock()

    def start(self) -> None:
        self._start_tcp_listener()
        self._start_udp_discovery()
        self._start_game_loop()
        self.log_event(
            f"[SERVIDOR] Listo para recibir jugadores en TCP {self.host}:{self.tcp_port}"
        )
        self.log_event(f"[DESCUBRIMIENTO] UDP activo en el puerto {DISCOVERY_PORT}")
        self.log_event("[CONTROL] Presiona ESPACIO o el botón para iniciar la partida")

    def stop(self) -> None:
        if not self.running.is_set():
            return

        self.log_event("[SERVIDOR] Cerrando conexiones...")
        self.running.clear()

        if self.tcp_socket is not None:
            try:
                self.tcp_socket.close()
            except OSError:
                pass

        if self.udp_socket is not None:
            try:
                self.udp_socket.close()
            except OSError:
                pass

        with self.sessions_lock:
            sessions = list(self.sessions.values())

        for session in sessions:
            try:
                session.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                session.sock.close()
            except OSError:
                pass

    def log_event(self, message: str) -> None:
        """Imprime un evento y lo guarda para mostrarlo en Arcade."""

        timestamp = time.strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}"
        print(line, flush=True)
        with self._events_lock:
            self._events.append(line)

    def recent_events(self, limit: int = 6) -> list[str]:
        with self._events_lock:
            return list(self._events)[-max(1, limit) :]

    def can_start_game(self) -> bool:
        snapshot = self.game.public_snapshot()
        return (
            snapshot["phase"] == STATE_LOBBY
            and len(snapshot["players"]) >= MIN_PLAYERS_TO_START
        )

    def start_game(self) -> tuple[bool, str]:
        """Solicita el inicio manual de la partida desde el host."""

        started, message = self.game.request_start()
        if started:
            self.log_event(f"[PARTIDA] {message}")
        else:
            self.log_event(f"[AVISO] No se pudo iniciar: {message}")
        return started, message

    def _start_tcp_listener(self) -> None:
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_socket.bind((self.host, self.tcp_port))
        self.tcp_socket.listen(MAX_PLAYERS)
        self.tcp_socket.settimeout(0.5)

        thread = threading.Thread(target=self._accept_loop, daemon=True)
        thread.start()
        self.threads.append(thread)

    def _start_udp_discovery(self) -> None:
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.bind(("", DISCOVERY_PORT))
        self.udp_socket.settimeout(0.5)

        thread = threading.Thread(target=self._discovery_loop, daemon=True)
        thread.start()
        self.threads.append(thread)

    def _start_game_loop(self) -> None:
        thread = threading.Thread(target=self._game_loop, daemon=True)
        thread.start()
        self.threads.append(thread)

    def _accept_loop(self) -> None:
        assert self.tcp_socket is not None

        while self.running.is_set():
            try:
                client_socket, address = self.tcp_socket.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            self.log_event(
                f"[CONEXIÓN] Nueva conexión entrante desde {address[0]}:{address[1]}"
            )

            client_socket.settimeout(1.0)
            session = ClientSession(client_socket, address)

            with self.sessions_lock:
                self.sessions[client_socket] = session

            thread = threading.Thread(
                target=self._client_loop,
                args=(session,),
                daemon=True,
            )
            thread.start()
            self.threads.append(thread)

    def _client_loop(self, session: ClientSession) -> None:
        buffer = JsonLineBuffer()

        try:
            while self.running.is_set():
                try:
                    data = session.sock.recv(RECV_SIZE)
                except socket.timeout:
                    continue

                if not data:
                    break

                try:
                    messages = buffer.feed(data)
                except ProtocolError as error:
                    self.log_event(
                        f"[PROTOCOLO] Mensaje inválido desde {session.address[0]}: {error}"
                    )
                    self._safe_send(session, {"type": "error", "reason": str(error)})
                    if str(error) == "MESSAGE_TOO_LARGE":
                        break
                    continue

                for message in messages:
                    self._handle_message(session, message)

        except (ConnectionError, OSError):
            pass
        finally:
            self._disconnect(session)

    def _handle_message(self, session: ClientSession, message: dict[str, Any]) -> None:
        message_type = message.get("type")

        if message_type == "join":
            self._handle_join(session, message)
            return

        if not session.joined or session.player_id is None:
            self._safe_send(session, {"type": "error", "reason": "NOT_JOINED"})
            return

        if message_type == "input":
            direction = message.get("dir")
            if not isinstance(direction, dict):
                self._safe_send(session, {"type": "error", "reason": "MISSING_FIELD"})
                return

            dir_x = direction.get("x")
            dir_y = direction.get("y")
            if not isinstance(dir_x, int) or not isinstance(dir_y, int):
                self._safe_send(session, {"type": "error", "reason": "INVALID_FIELD"})
                return

            if not self.game.set_direction(session.player_id, dir_x, dir_y):
                self._safe_send(session, {"type": "error", "reason": "INVALID_PHASE"})
            return

        if message_type == "interact":
            if not self.game.interact(session.player_id):
                # No estar cerca no rompe la conexión ni necesita mutar estado.
                self._safe_send(session, {"type": "error", "reason": "INVALID_ACTION"})
            return

        self._safe_send(session, {"type": "error", "reason": "UNKNOWN_TYPE"})

    def _handle_join(self, session: ClientSession, message: dict[str, Any]) -> None:
        if session.joined:
            self._safe_send(session, {"type": "error", "reason": "ALREADY_JOINED"})
            return

        version = message.get("v")
        if version != PROTOCOL_VERSION:
            self.log_event(
                f"[RECHAZADO] {session.address[0]} usa una versión incompatible"
            )
            self._safe_send(session, {"type": "error", "reason": "VERSION_MISMATCH"})
            self._close_session_socket(session)
            return

        name = message.get("name")
        if not isinstance(name, str):
            self._safe_send(session, {"type": "error", "reason": "NAME_INVALID"})
            return

        name = name.strip()
        if not name or len(name) > MAX_NAME_LENGTH or "\n" in name:
            self._safe_send(session, {"type": "error", "reason": "NAME_INVALID"})
            return

        with self.game.lock:
            if self.game.phase != STATE_LOBBY:
                self.log_event(
                    f"[RECHAZADO] '{name}' intentó entrar con la partida iniciada"
                )
                self._safe_send(session, {"type": "error", "reason": "GAME_STARTED"})
                return
            if len(self.game.players) >= MAX_PLAYERS:
                self._safe_send(session, {"type": "error", "reason": "LOBBY_FULL"})
                self._close_session_socket(session)
                return

        player_id = uuid.uuid4().hex[:8]
        player = self.game.add_player(player_id, name)
        session.player_id = player_id
        session.joined = True

        self.log_event(
            f"[LOBBY] Jugador '{name}' se unió | id={player_id} | "
            f"spawn=({player.x:.0f},{player.y:.0f})"
        )

        welcome = {
            "type": "welcome",
            "player_id": player_id,
            "config": {
                "map_size": MAP_SIZE,
                "circle_radius": CIRCLE_RADIUS,
                "player_radius": PLAYER_RADIUS,
                "interact_radius": INTERACT_RADIUS,
                "speed": PLAYER_SPEED,
                "tick_rate": TICK_RATE,
            },
        }
        self._safe_send(session, welcome)
        self.log_event(f"[PROTOCOLO] Mensaje 'welcome' enviado a '{name}'")

        self.broadcast(self.game.lobby_message())
        player_count = len(self.game.public_snapshot()["players"])
        self.log_event(f"[LOBBY] Lista actualizada: {player_count} jugador(es)")

    def _discovery_loop(self) -> None:
        assert self.udp_socket is not None

        while self.running.is_set():
            try:
                data, address = self.udp_socket.recvfrom(65535)
            except socket.timeout:
                continue
            except OSError:
                break

            try:
                message = decode_udp_message(data)
            except ProtocolError:
                continue

            if message.get("type") != "discover":
                continue
            if message.get("v") != PROTOCOL_VERSION:
                continue

            snapshot = self.game.public_snapshot()
            response = {
                "type": "server_info",
                "v": PROTOCOL_VERSION,
                "name": self.name,
                "tcp_port": self.tcp_port,
                "state": snapshot["phase"],
                "players": len(snapshot["players"]),
            }

            try:
                send_udp_message(self.udp_socket, response, address)
            except OSError:
                continue

    def _game_loop(self) -> None:
        tick_interval = 1.0 / TICK_RATE
        previous_time = time.monotonic()
        previous_phase = self.game.public_snapshot()["phase"]

        while self.running.is_set():
            tick_started = time.monotonic()
            delta_time = min(tick_started - previous_time, 0.1)
            previous_time = tick_started

            self.game.update(delta_time)

            countdown = self.game.countdown_seconds()
            if countdown is not None and countdown != self._last_countdown_value:
                self._last_countdown_value = countdown
                self.broadcast({"type": "countdown", "seconds": countdown})
                self.log_event(f"[COUNTDOWN] La partida inicia en {countdown}")
            elif countdown is None:
                self._last_countdown_value = None

            if self.game.consume_start_message():
                self.broadcast({"type": "start"})
                self.log_event("[PARTIDA] Inicio enviado a todos los clientes")

            winner = self.game.consume_game_over_message()
            if winner is not None:
                self.broadcast({"type": "game_over", "winner": winner})
                winner_name = self.game.player_name(winner) or winner
                self.log_event(f"[FIN] Ganador: '{winner_name}' ({winner})")

            snapshot = self.game.public_snapshot()
            current_phase = snapshot["phase"]

            if current_phase in {STATE_PLAYING, STATE_FINISHED}:
                self.broadcast(self.game.state_message())

            # Al terminar una ronda, el servidor vuelve al lobby y permite
            # que el host inicie manualmente la siguiente.
            if previous_phase != current_phase and current_phase == STATE_LOBBY:
                self.broadcast(self.game.lobby_message())
                self.log_event("[LOBBY] Nueva ronda lista. Esperando al host")

            previous_phase = current_phase

            elapsed = time.monotonic() - tick_started
            time.sleep(max(0.0, tick_interval - elapsed))

    def broadcast(self, message: dict[str, Any]) -> None:
        with self.sessions_lock:
            sessions = [session for session in self.sessions.values() if session.joined]

        disconnected: list[ClientSession] = []
        for session in sessions:
            try:
                session.send(message)
            except OSError:
                disconnected.append(session)

        for session in disconnected:
            self._disconnect(session)

    def _safe_send(self, session: ClientSession, message: dict[str, Any]) -> None:
        try:
            session.send(message)
        except OSError:
            pass

    def _disconnect(self, session: ClientSession) -> None:
        removed = False
        with self.sessions_lock:
            if session.sock in self.sessions:
                self.sessions.pop(session.sock, None)
                removed = True

        player_name = self.game.player_name(session.player_id)
        if session.player_id is not None:
            self.game.remove_player(session.player_id)

        self._close_session_socket(session)

        if removed:
            if player_name is not None:
                self.log_event(
                    f"[DESCONEXIÓN] Jugador '{player_name}' salió "
                    f"({session.address[0]}:{session.address[1]})"
                )
            else:
                self.log_event(
                    f"[DESCONEXIÓN] Cliente sin registrar salió "
                    f"({session.address[0]}:{session.address[1]})"
                )

            phase = self.game.public_snapshot()["phase"]
            if phase in {STATE_LOBBY, STATE_COUNTDOWN}:
                self.broadcast(self.game.lobby_message())

    @staticmethod
    def _close_session_socket(session: ClientSession) -> None:
        try:
            session.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            session.sock.close()
        except OSError:
            pass
