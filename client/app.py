"""Interfaz gráfica Arcade del cliente CTF."""

from __future__ import annotations

from typing import Any

import arcade

from common.constants import CIRCLE_RADIUS, MAP_CENTER_X, MAP_CENTER_Y, PLAYER_RADIUS
from common.rendering import logical_radius_to_screen, logical_to_screen
from client.network import CTFClient

WINDOW_SIZE = 820
WINDOW_TITLE = "CTF - Cliente Python"


class ClientWindow(arcade.Window):
    def __init__(self, client: CTFClient) -> None:
        super().__init__(WINDOW_SIZE, WINDOW_SIZE, WINDOW_TITLE, resizable=True)
        self.client = client
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

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
        width = self.width
        height = self.height

        circle_radius_logical = float(self.game_config.get("circle_radius", CIRCLE_RADIUS))
        player_radius_logical = float(self.game_config.get("player_radius", PLAYER_RADIUS))

        center_x, center_y = logical_to_screen(
            MAP_CENTER_X,
            MAP_CENTER_Y,
            width,
            height,
        )
        circle_radius = logical_radius_to_screen(circle_radius_logical, width, height)
        player_radius = logical_radius_to_screen(player_radius_logical, width, height)

        arcade.draw_circle_filled(
            center_x,
            center_y,
            circle_radius,
            arcade.color.DARK_BLUE_GRAY,
        )
        arcade.draw_circle_outline(
            center_x,
            center_y,
            circle_radius,
            arcade.color.WHITE,
            3,
        )

        flag_x, flag_y = logical_to_screen(
            float(self.flag.get("x", 500.0)),
            float(self.flag.get("y", 500.0)),
            width,
            height,
        )
        arcade.draw_circle_filled(flag_x, flag_y, max(7, player_radius * 0.65), arcade.color.GOLD)

        for player in self.players.values():
            x, y = logical_to_screen(
                float(player["x"]),
                float(player["y"]),
                width,
                height,
            )
            is_me = player["id"] == self.player_id
            carrying = player["id"] == self.flag.get("owner")

            if carrying:
                color = arcade.color.ORANGE
            elif is_me:
                color = arcade.color.LIME_GREEN
            else:
                color = arcade.color.SKY_BLUE

            arcade.draw_circle_filled(x, y, player_radius, color)
            arcade.draw_text(
                player.get("name", player["id"]),
                x,
                y + player_radius + 5,
                arcade.color.WHITE,
                11,
                anchor_x="center",
            )

        arcade.draw_text(
            f"CLIENTE | fase: {self.phase} | jugadores: {len(self.players)}",
            12,
            self.height - 28,
            arcade.color.WHITE,
            16,
        )
        arcade.draw_text(
            "Movimiento: WASD o flechas | Tomar/robar bandera: E",
            12,
            12,
            arcade.color.LIGHT_GRAY,
            12,
        )

        if self.countdown is not None:
            arcade.draw_text(
                str(self.countdown),
                self.width / 2,
                self.height / 2,
                arcade.color.YELLOW,
                56,
                anchor_x="center",
                anchor_y="center",
            )

        if self.winner is not None:
            winner_name = self.players.get(self.winner, {}).get("name", self.winner)
            text = "¡Ganaste!" if self.winner == self.player_id else f"Ganó {winner_name}"
            arcade.draw_text(
                text,
                self.width / 2,
                self.height / 2,
                arcade.color.YELLOW,
                36,
                anchor_x="center",
                anchor_y="center",
            )

        if self.error_message:
            arcade.draw_text(
                self.error_message,
                self.width / 2,
                42,
                arcade.color.LIGHT_CORAL,
                12,
                anchor_x="center",
            )

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
            lobby_players = message.get("players", [])
            for player in lobby_players:
                player_id = player.get("id")
                if isinstance(player_id, str):
                    current = self.players.get(player_id, {})
                    current.update(player)
                    current.setdefault("x", 500.0)
                    current.setdefault("y", 500.0)
                    self.players[player_id] = current

            valid_ids = {p.get("id") for p in lobby_players}
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
            self.flag = message.get("flag", self.flag)
            state_players = message.get("players", [])
            self.players = {
                player["id"]: player
                for player in state_players
                if isinstance(player, dict) and isinstance(player.get("id"), str)
            }

        elif message_type == "game_over":
            self.phase = "finished"
            self.winner = message.get("winner")

        elif message_type == "error":
            reason = str(message.get("reason", "ERROR"))
            # INVALID_ACTION puede aparecer al pulsar E lejos de la bandera.
            if reason != "INVALID_ACTION":
                self.error_message = reason

        elif message_type == "disconnected":
            self.phase = "disconnected"
            self.error_message = "El servidor se desconectó"


def run_client_window(client: CTFClient) -> None:
    ClientWindow(client)
    arcade.run()
