"""Ventana Arcade del modo servidor: observa, pero no controla jugadores."""

from __future__ import annotations

import arcade

from common.constants import CIRCLE_RADIUS, MAP_CENTER_X, MAP_CENTER_Y, PLAYER_RADIUS
from common.rendering import logical_radius_to_screen, logical_to_screen
from server.network import CTFServer

WINDOW_SIZE = 820
WINDOW_TITLE = "CTF - Servidor Python"


class ServerWindow(arcade.Window):
    def __init__(self, server: CTFServer) -> None:
        super().__init__(WINDOW_SIZE, WINDOW_SIZE, WINDOW_TITLE, resizable=True)
        self.server = server
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
        arcade.draw_circle_filled(flag_x, flag_y, max(7, player_radius * 0.65), arcade.color.GOLD)

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
        arcade.draw_text(
            "Esta ventana solo observa. Los movimientos se hacen desde clientes.",
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

    def on_close(self) -> None:
        self.server.stop()
        super().on_close()


def run_server_window(server: CTFServer) -> None:
    ServerWindow(server)
    arcade.run()
