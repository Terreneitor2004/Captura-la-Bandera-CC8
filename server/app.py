"""Ventana Arcade del modo servidor.

La interfaz se encuentra en server/interface.py. Este archivo solo conecta los
eventos de la ventana con las acciones del servidor.
"""

from __future__ import annotations

import arcade

from server.interface import ServerInterface, ServerUIState
from server.network import CTFServer
from ui import theme

WINDOW_WIDTH = 1180
WINDOW_HEIGHT = 760
WINDOW_TITLE = "CTF - Servidor Python"


class ServerWindow(arcade.Window):
    def __init__(self, server: CTFServer) -> None:
        super().__init__(
            WINDOW_WIDTH,
            WINDOW_HEIGHT,
            WINDOW_TITLE,
            resizable=True,
        )
        self.server = server
        self.interface = ServerInterface()
        self.feedback_message = "Esperando jugadores..."
        self.mouse_x = -1.0
        self.mouse_y = -1.0
        arcade.set_background_color(theme.BACKGROUND)

    def on_draw(self) -> None:
        self.clear()
        snapshot = self.server.game.public_snapshot()
        button = self.interface.start_button_bounds(self.width, self.height)
        state = ServerUIState(
            server_name=self.server.name,
            host=self.server.host,
            tcp_port=self.server.tcp_port,
            phase=snapshot["phase"],
            players=snapshot["players"],
            flag_owner=snapshot["flag_owner"],
            flag_x=snapshot["flag_x"],
            flag_y=snapshot["flag_y"],
            winner=snapshot["winner"],
            countdown=self.server.game.countdown_seconds(),
            events=self.server.recent_events(limit=20),
            feedback=self.feedback_message,
        )
        self.interface.draw(
            self.width,
            self.height,
            state,
            button_hovered=button.contains(self.mouse_x, self.mouse_y),
        )

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        del modifiers
        if symbol == arcade.key.SPACE:
            self._try_start_game()

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        del dx, dy
        self.mouse_x = x
        self.mouse_y = y

    def on_mouse_press(
        self,
        x: float,
        y: float,
        button: int,
        modifiers: int,
    ) -> None:
        del button, modifiers
        bounds = self.interface.start_button_bounds(self.width, self.height)
        if bounds.contains(x, y):
            self._try_start_game()

    def on_close(self) -> None:
        self.server.stop()
        super().on_close()

    def _try_start_game(self) -> None:
        started, message = self.server.start_game()
        self.feedback_message = message if started else f"No se pudo iniciar: {message}"


def run_server_window(server: CTFServer) -> None:
    ServerWindow(server)
    arcade.run()
