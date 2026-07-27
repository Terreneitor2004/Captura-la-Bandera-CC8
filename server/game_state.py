"""Estado autoritativo y reglas del juego ejecutadas por el servidor."""

from __future__ import annotations

import math
import random
import threading
import time
from dataclasses import dataclass, field
from typing import Any

from common.constants import (
    CIRCLE_RADIUS,
    COUNTDOWN_SECONDS,
    FLAG_START_X,
    FLAG_START_Y,
    INTERACT_RADIUS,
    MAP_CENTER_X,
    MAP_CENTER_Y,
    MAP_SIZE,
    MIN_PLAYERS_TO_START,
    PLAYER_RADIUS,
    PLAYER_SPEED,
    STATE_COUNTDOWN,
    STATE_FINISHED,
    STATE_LOBBY,
    STATE_PLAYING,
    VALID_DIRECTION_VALUES,
)


@dataclass
class Player:
    player_id: str
    name: str
    x: float
    y: float
    dir_x: int = 0
    dir_y: int = 0
    joined_at: float = field(default_factory=time.monotonic)


class GameState:
    """Contiene la única versión oficial del mundo del juego."""

    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.players: dict[str, Player] = {}
        self.phase = STATE_LOBBY
        self.flag_owner: str | None = None
        self.flag_x = FLAG_START_X
        self.flag_y = FLAG_START_Y
        self.winner: str | None = None
        self.countdown_end: float | None = None
        self.finished_at: float | None = None
        self.start_message_pending = False
        self.game_over_message_pending = False

    def add_player(self, player_id: str, name: str) -> Player:
        with self.lock:
            x, y = self._random_spawn_outside_circle()
            player = Player(player_id=player_id, name=name, x=x, y=y)
            self.players[player_id] = player
            return player

    def remove_player(self, player_id: str) -> None:
        with self.lock:
            self.players.pop(player_id, None)

            if self.flag_owner == player_id:
                self.flag_owner = None
                self.flag_x = FLAG_START_X
                self.flag_y = FLAG_START_Y

            if not self.players:
                self._reset_to_lobby()

    def request_start(self) -> tuple[bool, str]:
        """Inicia manualmente la cuenta regresiva desde la ventana del servidor."""

        with self.lock:
            if self.phase != STATE_LOBBY:
                return False, "La partida solo puede iniciarse desde el lobby"

            if len(self.players) < MIN_PLAYERS_TO_START:
                return (
                    False,
                    f"Se necesitan al menos {MIN_PLAYERS_TO_START} jugador(es)",
                )

            self.winner = None
            self.flag_owner = None
            self.flag_x = FLAG_START_X
            self.flag_y = FLAG_START_Y
            self.finished_at = None
            self.countdown_end = time.monotonic() + COUNTDOWN_SECONDS
            self.phase = STATE_COUNTDOWN
            self.start_message_pending = False
            self.game_over_message_pending = False

            for player in self.players.values():
                player.dir_x = 0
                player.dir_y = 0

            return True, f"Cuenta regresiva iniciada con {len(self.players)} jugador(es)"

    def set_direction(self, player_id: str, dir_x: int, dir_y: int) -> bool:
        with self.lock:
            if self.phase != STATE_PLAYING:
                return False
            if dir_x not in VALID_DIRECTION_VALUES or dir_y not in VALID_DIRECTION_VALUES:
                return False

            player = self.players.get(player_id)
            if player is None:
                return False

            player.dir_x = dir_x
            player.dir_y = dir_y
            return True

    def interact(self, player_id: str) -> bool:
        with self.lock:
            if self.phase != STATE_PLAYING:
                return False

            player = self.players.get(player_id)
            if player is None:
                return False

            if self.flag_owner is None:
                distance = math.dist((player.x, player.y), (self.flag_x, self.flag_y))
                if distance <= INTERACT_RADIUS:
                    self.flag_owner = player_id
                    self._sync_flag_to_owner()
                    return True
                return False

            if self.flag_owner == player_id:
                return False

            owner = self.players.get(self.flag_owner)
            if owner is None:
                self.flag_owner = None
                self.flag_x = FLAG_START_X
                self.flag_y = FLAG_START_Y
                return False

            distance = math.dist((player.x, player.y), (owner.x, owner.y))
            if distance <= INTERACT_RADIUS:
                self.flag_owner = player_id
                self._sync_flag_to_owner()
                return True

            return False

    def update(self, delta_time: float) -> None:
        with self.lock:
            now = time.monotonic()

            # El servidor inicia manualmente la partida. En lobby no hay
            # transición automática.
            if self.phase == STATE_LOBBY:
                return

            if self.phase == STATE_COUNTDOWN:
                # Si todos se desconectan, remove_player() ya vuelve al lobby.
                if self.countdown_end is not None and now >= self.countdown_end:
                    self.phase = STATE_PLAYING
                    self.start_message_pending = True
                    self.countdown_end = None
                    for player in self.players.values():
                        player.dir_x = 0
                        player.dir_y = 0

            elif self.phase == STATE_PLAYING:
                self._move_players(delta_time)
                self._sync_flag_to_owner()
                self._check_victory()

            elif self.phase == STATE_FINISHED:
                if self.finished_at is not None and now - self.finished_at >= 5.0:
                    self._prepare_next_round()

    def countdown_seconds(self) -> int | None:
        with self.lock:
            if self.phase != STATE_COUNTDOWN or self.countdown_end is None:
                return None
            return max(1, math.ceil(self.countdown_end - time.monotonic()))

    def consume_start_message(self) -> bool:
        with self.lock:
            value = self.start_message_pending
            self.start_message_pending = False
            return value

    def consume_game_over_message(self) -> str | None:
        with self.lock:
            if not self.game_over_message_pending:
                return None
            self.game_over_message_pending = False
            return self.winner

    def lobby_message(self) -> dict[str, Any]:
        with self.lock:
            players = [
                {"id": player.player_id, "name": player.name}
                for player in self.players.values()
            ]
            return {"type": "lobby", "players": players}

    def state_message(self) -> dict[str, Any]:
        with self.lock:
            return {
                "type": "state",
                "flag": {
                    "owner": self.flag_owner,
                    "x": round(self.flag_x, 1),
                    "y": round(self.flag_y, 1),
                },
                "players": [
                    {
                        "id": player.player_id,
                        "name": player.name,
                        "x": round(player.x, 1),
                        "y": round(player.y, 1),
                    }
                    for player in self.players.values()
                ],
            }

    def public_snapshot(self) -> dict[str, Any]:
        with self.lock:
            return {
                "phase": self.phase,
                "winner": self.winner,
                "flag_owner": self.flag_owner,
                "flag_x": self.flag_x,
                "flag_y": self.flag_y,
                "players": [
                    {
                        "id": player.player_id,
                        "name": player.name,
                        "x": player.x,
                        "y": player.y,
                    }
                    for player in self.players.values()
                ],
            }

    def player_name(self, player_id: str | None) -> str | None:
        if player_id is None:
            return None
        with self.lock:
            player = self.players.get(player_id)
            return player.name if player is not None else None

    def _move_players(self, delta_time: float) -> None:
        for player in self.players.values():
            dx = float(player.dir_x)
            dy = float(player.dir_y)

            if dx != 0.0 and dy != 0.0:
                diagonal_factor = 1.0 / math.sqrt(2.0)
                dx *= diagonal_factor
                dy *= diagonal_factor

            player.x += dx * PLAYER_SPEED * delta_time
            player.y += dy * PLAYER_SPEED * delta_time

            player.x = min(max(player.x, PLAYER_RADIUS), MAP_SIZE - PLAYER_RADIUS)
            player.y = min(max(player.y, PLAYER_RADIUS), MAP_SIZE - PLAYER_RADIUS)

    def _sync_flag_to_owner(self) -> None:
        if self.flag_owner is None:
            return

        owner = self.players.get(self.flag_owner)
        if owner is None:
            self.flag_owner = None
            self.flag_x = FLAG_START_X
            self.flag_y = FLAG_START_Y
            return

        self.flag_x = owner.x
        self.flag_y = owner.y

    def _check_victory(self) -> None:
        if self.flag_owner is None:
            return

        owner = self.players.get(self.flag_owner)
        if owner is None:
            return

        distance_from_center = math.dist(
            (owner.x, owner.y),
            (MAP_CENTER_X, MAP_CENTER_Y),
        )

        # Debe salir completamente: centro del jugador fuera del radio
        # más el radio del propio jugador.
        if distance_from_center >= CIRCLE_RADIUS + PLAYER_RADIUS:
            self.winner = owner.player_id
            self.phase = STATE_FINISHED
            self.finished_at = time.monotonic()
            self.game_over_message_pending = True
            for player in self.players.values():
                player.dir_x = 0
                player.dir_y = 0

    def _random_spawn_outside_circle(self) -> tuple[float, float]:
        margin = PLAYER_RADIUS
        for _ in range(1000):
            x = random.uniform(margin, MAP_SIZE - margin)
            y = random.uniform(margin, MAP_SIZE - margin)
            distance = math.dist((x, y), (MAP_CENTER_X, MAP_CENTER_Y))
            if distance >= CIRCLE_RADIUS + PLAYER_RADIUS + 30:
                return x, y

        return margin, margin

    def _prepare_next_round(self) -> None:
        self.phase = STATE_LOBBY
        self.flag_owner = None
        self.flag_x = FLAG_START_X
        self.flag_y = FLAG_START_Y
        self.winner = None
        self.finished_at = None
        self.countdown_end = None
        self.start_message_pending = False
        self.game_over_message_pending = False

        for player in self.players.values():
            player.x, player.y = self._random_spawn_outside_circle()
            player.dir_x = 0
            player.dir_y = 0

    def _reset_to_lobby(self) -> None:
        self.phase = STATE_LOBBY
        self.flag_owner = None
        self.flag_x = FLAG_START_X
        self.flag_y = FLAG_START_Y
        self.winner = None
        self.countdown_end = None
        self.finished_at = None
        self.start_message_pending = False
        self.game_over_message_pending = False
