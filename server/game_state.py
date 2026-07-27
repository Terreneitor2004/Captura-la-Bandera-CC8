"""Estado autoritativo y reglas de la partida."""

import math
import random
import threading
import time
from dataclasses import dataclass
from typing import Any

from common import constants as C


@dataclass
class Player:
    player_id: str
    name: str
    x: float
    y: float
    dir_x: int = 0
    dir_y: int = 0


class GameState:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.players: dict[str, Player] = {}
        self.phase = C.STATE_LOBBY
        self.flag_owner: str | None = None
        self.flag_x, self.flag_y = C.FLAG_START_X, C.FLAG_START_Y
        self.winner: str | None = None
        self.countdown_end: float | None = None
        self.finished_at: float | None = None
        self.start_message_pending = False
        self.game_over_message_pending = False

    def add_player(self, player_id: str, name: str) -> Player:
        with self.lock:
            player = Player(player_id, name, *self._spawn())
            self.players[player_id] = player
            return player

    def remove_player(self, player_id: str) -> None:
        with self.lock:
            self.players.pop(player_id, None)
            if self.flag_owner == player_id:
                self._reset_flag()
            if not self.players:
                self._reset_round()

    def request_start(self) -> tuple[bool, str]:
        with self.lock:
            if self.phase != C.STATE_LOBBY:
                return False, "La partida solo puede iniciarse desde el lobby"
            if len(self.players) < C.MIN_PLAYERS_TO_START:
                return False, f"Se necesitan al menos {C.MIN_PLAYERS_TO_START} jugador(es)"

            self._reset_flag()
            self.winner = self.finished_at = None
            self.countdown_end = time.monotonic() + C.COUNTDOWN_SECONDS
            self.phase = C.STATE_COUNTDOWN
            self.start_message_pending = self.game_over_message_pending = False
            self._stop_players()
            return True, f"Cuenta regresiva iniciada con {len(self.players)} jugador(es)"

    def set_direction(self, player_id: str, x: int, y: int) -> bool:
        with self.lock:
            player = self.players.get(player_id)
            if (
                self.phase != C.STATE_PLAYING
                or player is None
                or x not in C.VALID_DIRECTION_VALUES
                or y not in C.VALID_DIRECTION_VALUES
            ):
                return False
            player.dir_x, player.dir_y = x, y
            return True

    def interact(self, player_id: str) -> bool:
        with self.lock:
            player = self.players.get(player_id)
            if self.phase != C.STATE_PLAYING or player is None:
                return False

            if self.flag_owner is None:
                target = (self.flag_x, self.flag_y)
            elif self.flag_owner == player_id:
                return False
            else:
                owner = self.players.get(self.flag_owner)
                if owner is None:
                    self._reset_flag()
                    return False
                target = (owner.x, owner.y)

            if math.dist((player.x, player.y), target) > C.INTERACT_RADIUS:
                return False
            self.flag_owner = player_id
            self._sync_flag()
            return True

    def update(self, delta_time: float) -> None:
        with self.lock:
            now = time.monotonic()
            if self.phase == C.STATE_COUNTDOWN and self.countdown_end and now >= self.countdown_end:
                self.phase = C.STATE_PLAYING
                self.countdown_end = None
                self.start_message_pending = True
                self._stop_players()
            elif self.phase == C.STATE_PLAYING:
                self._move(delta_time)
                self._sync_flag()
                self._check_victory()
            elif self.phase == C.STATE_FINISHED and self.finished_at and now - self.finished_at >= 5:
                self._next_round()

    def countdown_seconds(self) -> int | None:
        with self.lock:
            if self.phase != C.STATE_COUNTDOWN or self.countdown_end is None:
                return None
            return max(1, math.ceil(self.countdown_end - time.monotonic()))

    def consume_start_message(self) -> bool:
        with self.lock:
            pending = self.start_message_pending
            self.start_message_pending = False
            return pending

    def consume_game_over_message(self) -> str | None:
        with self.lock:
            if not self.game_over_message_pending:
                return None
            self.game_over_message_pending = False
            return self.winner

    def lobby_message(self) -> dict[str, Any]:
        with self.lock:
            return {"type": "lobby", "players": self._player_data(False)}

    def state_message(self) -> dict[str, Any]:
        with self.lock:
            return {
                "type": "state",
                "flag": {
                    "owner": self.flag_owner,
                    "x": round(self.flag_x, 1),
                    "y": round(self.flag_y, 1),
                },
                "players": self._player_data(True, rounded=True),
            }

    def public_snapshot(self) -> dict[str, Any]:
        with self.lock:
            return {
                "phase": self.phase,
                "winner": self.winner,
                "flag_owner": self.flag_owner,
                "flag_x": self.flag_x,
                "flag_y": self.flag_y,
                "players": self._player_data(True),
            }

    def player_name(self, player_id: str | None) -> str | None:
        with self.lock:
            player = self.players.get(player_id or "")
            return player.name if player else None

    def _player_data(self, positions: bool, rounded: bool = False) -> list[dict[str, Any]]:
        data = []
        for player in self.players.values():
            item: dict[str, Any] = {"id": player.player_id, "name": player.name}
            if positions:
                item.update(
                    x=round(player.x, 1) if rounded else player.x,
                    y=round(player.y, 1) if rounded else player.y,
                )
            data.append(item)
        return data

    def _move(self, delta_time: float) -> None:
        step = C.PLAYER_SPEED * max(0.0, min(float(delta_time), 0.1))
        for player in self.players.values():
            length = math.hypot(player.dir_x, player.dir_y)
            if length:
                player.x += player.dir_x / length * step
                player.y += player.dir_y / length * step
            player.x = min(max(player.x, C.PLAYER_RADIUS), C.MAP_SIZE - C.PLAYER_RADIUS)
            player.y = min(max(player.y, C.PLAYER_RADIUS), C.MAP_SIZE - C.PLAYER_RADIUS)

    def _sync_flag(self) -> None:
        if self.flag_owner is None:
            return
        owner = self.players.get(self.flag_owner)
        if owner:
            self.flag_x, self.flag_y = owner.x, owner.y
        else:
            self._reset_flag()

    def _check_victory(self) -> None:
        owner = self.players.get(self.flag_owner or "")
        if owner and math.dist((owner.x, owner.y), (C.MAP_CENTER_X, C.MAP_CENTER_Y)) >= C.CIRCLE_RADIUS + C.PLAYER_RADIUS:
            self.winner = owner.player_id
            self.phase = C.STATE_FINISHED
            self.finished_at = time.monotonic()
            self.game_over_message_pending = True
            self._stop_players()

    def _spawn(self) -> tuple[float, float]:
        margin = C.PLAYER_RADIUS
        for _ in range(1000):
            point = (
                random.uniform(margin, C.MAP_SIZE - margin),
                random.uniform(margin, C.MAP_SIZE - margin),
            )
            if math.dist(point, (C.MAP_CENTER_X, C.MAP_CENTER_Y)) >= C.CIRCLE_RADIUS + C.PLAYER_RADIUS + 30:
                return point
        return margin, margin

    def _stop_players(self) -> None:
        for player in self.players.values():
            player.dir_x = player.dir_y = 0

    def _reset_flag(self) -> None:
        self.flag_owner = None
        self.flag_x, self.flag_y = C.FLAG_START_X, C.FLAG_START_Y

    def _reset_round(self) -> None:
        self.phase = C.STATE_LOBBY
        self._reset_flag()
        self.winner = self.countdown_end = self.finished_at = None
        self.start_message_pending = self.game_over_message_pending = False

    def _next_round(self) -> None:
        self._reset_round()
        for player in self.players.values():
            player.x, player.y = self._spawn()
            player.dir_x = player.dir_y = 0
