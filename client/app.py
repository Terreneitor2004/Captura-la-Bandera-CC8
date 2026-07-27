"""Ventana Arcade del cliente CTF.

La lógica visual se encuentra en client/interface.py para mantener este archivo
centrado en eventos, entrada del teclado y mensajes del protocolo.
"""

from __future__ import annotations

from typing import Any

import arcade

from client.interface import ClientInterface, ClientUIState
from client.message_adapter import normalize_flag, normalize_players
from client.network import CTFClient
from ui import theme

WINDOW_WIDTH = 1180
WINDOW_HEIGHT = 760
WINDOW_TITLE = "CTF - Cliente Python"


class ClientWindow(arcade.Window):
    def __init__(self, client: CTFClient) -> None:
        super().__init__(
            WINDOW_WIDTH,
            WINDOW_HEIGHT,
            WINDOW_TITLE,
            resizable=True,
        )
        self.client = client
        self.interface = ClientInterface()
        arcade.set_background_color(theme.BACKGROUND)

        self.player_id: str | None = None
        self.players: dict[str, dict[str, Any]] = {}
        self.flag: dict[str, Any] = {"owner": None, "x": 500.0, "y": 500.0}
        self.phase = "connecting"
        self.countdown: int | None = None
        self.winner: str | None = None
        self.error_message = ""
        self.game_config: dict[str, Any] = {}

        self.keys_down: set[int] = set()
        self.last_direction = (0, 0)

    def on_update(self, delta_time: float) -> None:
        del delta_time
        for message in self.client.poll_messages():
            self._handle_message(message)

    def on_draw(self) -> None:
        self.clear()
        state = ClientUIState(
            player_id=self.player_id,
            player_name=self.client.name,
            host=self.client.host,
            port=self.client.port,
            phase=self.phase,
            players=self.players,
            flag=self.flag,
            countdown=self.countdown,
            winner=self.winner,
            error_message=self.error_message,
            config=self.game_config,
        )
        self.interface.draw(self.width, self.height, state)

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        del modifiers
        self.keys_down.add(symbol)

        if symbol == arcade.key.E:
            try:
                self.client.interact()
            except OSError as error:
                self.error_message = str(error)
            return

        self._send_direction_if_changed()

    def on_key_release(self, symbol: int, modifiers: int) -> None:
        del modifiers
        self.keys_down.discard(symbol)
        self._send_direction_if_changed()

    def on_deactivate(self) -> None:
        """Detiene el movimiento si la ventana pierde el foco."""

        if self.keys_down:
            self.keys_down.clear()
            self._send_direction_if_changed()

    def on_close(self) -> None:
        self.client.close()
        super().on_close()

    def _send_direction_if_changed(self) -> None:
        left = arcade.key.A in self.keys_down or arcade.key.LEFT in self.keys_down
        right = arcade.key.D in self.keys_down or arcade.key.RIGHT in self.keys_down
        up = arcade.key.W in self.keys_down or arcade.key.UP in self.keys_down
        down = arcade.key.S in self.keys_down or arcade.key.DOWN in self.keys_down

        dir_x = int(right) - int(left)
        # En el protocolo, y=-1 es arriba y y=1 es abajo.
        dir_y = int(down) - int(up)
        direction = (dir_x, dir_y)

        if direction == self.last_direction:
            return

        self.last_direction = direction
        try:
            self.client.send_input(dir_x, dir_y)
        except OSError as error:
            self.error_message = str(error)

    def _handle_message(self, message: dict[str, Any]) -> None:
        message_type = message.get("type")

        if message_type == "welcome":
            self.player_id = message.get("player_id")
            self.game_config = message.get("config", {})
            self.phase = "lobby"
            self.error_message = ""

        elif message_type == "lobby":
            lobby_players = normalize_players(message.get("players", []))

            if self.phase in {"connecting", "lobby", "finished"}:
                self.phase = "lobby"
                self.countdown = None
                self.winner = None

            for player_id, player in lobby_players.items():
                current = self.players.get(player_id, {})
                current.update(player)
                current.setdefault("x", 500.0)
                current.setdefault("y", 500.0)
                self.players[player_id] = current

            valid_ids = set(lobby_players)
            self.players = {
                player_id: player
                for player_id, player in self.players.items()
                if player_id in valid_ids
            }

        elif message_type == "countdown":
            self.phase = "countdown"
            self.countdown = message.get("seconds")

        elif message_type == "start":
            self.phase = "playing"
            self.countdown = None
            self.winner = None
            self.error_message = ""

        elif message_type == "state":
            # El estándar usa players como lista y flag.owner. Algunos proyectos
            # de la clase envían players como diccionario indexado por ID y
            # flag.carrier_id. Normalizamos ambos formatos para interoperar.
            self.flag = normalize_flag(message.get("flag", self.flag), self.flag)
            self.players = normalize_players(message.get("players", []))

            # Según el protocolo, un mensaje state solo se envía durante playing.
            # Esto también permite conectarse a servidores que omiten start.
            if self.phase != "finished":
                self.phase = "playing"
                self.countdown = None

        elif message_type == "game_over":
            self.phase = "finished"
            self.winner = message.get("winner")

        elif message_type == "error":
            reason = str(message.get("reason", "ERROR"))
            if reason != "INVALID_ACTION":
                self.error_message = reason

        elif message_type == "disconnected":
            self.phase = "disconnected"
            self.error_message = "El servidor se desconectó"




def run_client_window(client: CTFClient) -> None:
    ClientWindow(client)
    arcade.run()
