"""Ventana Arcade del modo servidor: observa y controla el inicio."""

from __future__ import annotations

import arcade

from common.constants import (
    CIRCLE_RADIUS,
    MAP_CENTER_X,
    MAP_CENTER_Y,
    MIN_PLAYERS_TO_START,
    PLAYER_RADIUS,
    STATE_COUNTDOWN,
    STATE_FINISHED,
    STATE_LOBBY,
    STATE_PLAYING,
)
from common.rendering import logical_radius_to_screen, logical_to_screen
from server.network import CTFServer

WINDOW_SIZE = 820
WINDOW_TITLE = "CTF - Servidor Python"


class ServerWindow(arcade.Window):
    def __init__(self, server: CTFServer) -> None:
        super().__init__(WINDOW_SIZE, WINDOW_SIZE, WINDOW_TITLE, resizable=True)
        self.server = server
        self.feedback_message = ""
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

    def on_draw(self) -> None:
        self.clear()
        width = self.width
        height = self.height
        snapshot = self.server.game.public_snapshot()

        center_x, center_y = logical_to_screen(
            MAP_CENTER_X,
            MAP_CENTER_Y,
            width,
            height,
        )
        circle_radius = logical_radius_to_screen(CIRCLE_RADIUS, width, height)
        player_radius = logical_radius_to_screen(PLAYER_RADIUS, width, height)

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
            snapshot["flag_x"],
            snapshot["flag_y"],
            width,
            height,
        )
        arcade.draw_circle_filled(
            flag_x,
            flag_y,
            max(7, player_radius * 0.65),
            arcade.color.GOLD,
        )

        for player in snapshot["players"]:
            x, y = logical_to_screen(player["x"], player["y"], width, height)
            carrying = player["id"] == snapshot["flag_owner"]
            color = arcade.color.ORANGE if carrying else arcade.color.SKY_BLUE
            arcade.draw_circle_filled(x, y, player_radius, color)
            arcade.draw_text(
                player["name"],
                x,
                y + player_radius + 5,
                arcade.color.WHITE,
                11,
                anchor_x="center",
            )

        arcade.draw_text(
            f"SERVIDOR | fase: {snapshot['phase']} | jugadores: {len(snapshot['players'])}",
            12,
            self.height - 28,
            arcade.color.WHITE,
            16,
        )
        arcade.draw_text(
            f"TCP: {self.server.tcp_port} | Descubrimiento UDP: 8888",
            12,
            self.height - 52,
            arcade.color.LIGHT_GRAY,
            12,
        )

        self._draw_start_button(snapshot)
        self._draw_event_panel()

        arcade.draw_text(
            "Servidor: observa el mapa. Clientes: controlan jugadores con WASD y E.",
            12,
            12,
            arcade.color.LIGHT_GRAY,
            12,
        )

        if snapshot["winner"]:
            winner_name = snapshot["winner"]
            for player in snapshot["players"]:
                if player["id"] == snapshot["winner"]:
                    winner_name = player["name"]
                    break
            arcade.draw_text(
                f"Ganador: {winner_name}",
                self.width / 2,
                self.height / 2,
                arcade.color.YELLOW,
                32,
                anchor_x="center",
                anchor_y="center",
            )

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        del modifiers
        if symbol == arcade.key.SPACE:
            self._try_start_game()

    def on_mouse_press(
        self,
        x: float,
        y: float,
        button: int,
        modifiers: int,
    ) -> None:
        del button, modifiers
        left, right, bottom, top = self._start_button_bounds()
        if left <= x <= right and bottom <= y <= top:
            self._try_start_game()

    def on_close(self) -> None:
        self.server.stop()
        super().on_close()

    def _try_start_game(self) -> None:
        started, message = self.server.start_game()
        self.feedback_message = message if started else f"No se pudo iniciar: {message}"

    def _start_button_bounds(self) -> tuple[float, float, float, float]:
        right = self.width - 12
        left = max(12, right - 225)
        top = self.height - 12
        bottom = top - 42
        return left, right, bottom, top

    def _draw_start_button(self, snapshot: dict) -> None:
        left, right, bottom, top = self._start_button_bounds()
        phase = snapshot["phase"]
        player_count = len(snapshot["players"])

        if phase == STATE_LOBBY and player_count >= MIN_PLAYERS_TO_START:
            label = "INICIAR PARTIDA"
            color = (47, 125, 62)
        elif phase == STATE_LOBBY:
            label = f"ESPERANDO JUGADORES ({player_count}/{MIN_PLAYERS_TO_START})"
            color = (90, 96, 100)
        elif phase == STATE_COUNTDOWN:
            seconds = self.server.game.countdown_seconds()
            label = f"INICIANDO EN {seconds or 1}"
            color = (180, 130, 35)
        elif phase == STATE_PLAYING:
            label = "PARTIDA EN CURSO"
            color = (45, 82, 120)
        elif phase == STATE_FINISHED:
            label = "PARTIDA FINALIZADA"
            color = (120, 65, 65)
        else:
            label = str(phase).upper()
            color = (90, 96, 100)

        arcade.draw_polygon_filled(
            [(left, bottom), (right, bottom), (right, top), (left, top)],
            color,
        )
        arcade.draw_text(
            label,
            (left + right) / 2,
            (bottom + top) / 2,
            arcade.color.WHITE,
            12,
            anchor_x="center",
            anchor_y="center",
        )

        arcade.draw_text(
            "Clic o ESPACIO",
            (left + right) / 2,
            bottom - 17,
            arcade.color.LIGHT_GRAY,
            10,
            anchor_x="center",
        )

    def _draw_event_panel(self) -> None:
        events = self.server.recent_events(limit=5)
        panel_left = 8
        panel_right = self.width - 8
        panel_bottom = 36
        panel_top = 154

        arcade.draw_polygon_filled(
            [
                (panel_left, panel_bottom),
                (panel_right, panel_bottom),
                (panel_right, panel_top),
                (panel_left, panel_top),
            ],
            (20, 24, 26, 210),
        )
        arcade.draw_text(
            "Eventos del servidor:",
            16,
            panel_top - 20,
            arcade.color.WHITE,
            12,
        )

        y = panel_top - 42
        for event in events:
            # Recortamos únicamente la representación visual. La terminal
            # conserva el mensaje completo.
            visible = event if len(event) <= 115 else event[:112] + "..."
            arcade.draw_text(
                visible,
                16,
                y,
                arcade.color.LIGHT_GRAY,
                10,
            )
            y -= 17


def run_server_window(server: CTFServer) -> None:
    ServerWindow(server)
    arcade.run()
