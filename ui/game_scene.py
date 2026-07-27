"""Dibujo compartido del mapa, jugadores y bandera."""

from __future__ import annotations

from typing import Any

import arcade

from common.constants import (
    CIRCLE_RADIUS,
    MAP_CENTER_X,
    MAP_CENTER_Y,
    MAP_SIZE,
    PLAYER_RADIUS,
)
from ui import theme
from ui.components import TextRegistry, draw_panel
from ui.layout import Rect, logical_radius_to_screen, logical_to_screen


class GameSceneRenderer:
    def __init__(self) -> None:
        self.texts = TextRegistry()

    def draw(
        self,
        arena: Rect,
        players: list[dict[str, Any]],
        flag: dict[str, Any],
        *,
        own_player_id: str | None,
        config: dict[str, Any] | None = None,
    ) -> None:
        config = config or {}
        circle_radius_logical = float(config.get("circle_radius", CIRCLE_RADIUS))
        player_radius_logical = float(config.get("player_radius", PLAYER_RADIUS))

        draw_panel(arena, theme.ARENA_BACKGROUND, theme.MAP_EDGE, 2)
        self._draw_grid(arena)

        center_x, center_y = logical_to_screen(
            MAP_CENTER_X,
            MAP_CENTER_Y,
            arena,
        )
        circle_radius = logical_radius_to_screen(circle_radius_logical, arena)
        player_radius = max(7.0, logical_radius_to_screen(player_radius_logical, arena))

        arcade.draw_circle_filled(
            center_x,
            center_y,
            circle_radius,
            theme.ARENA_CIRCLE,
        )
        arcade.draw_circle_outline(
            center_x,
            center_y,
            circle_radius,
            theme.ARENA_CIRCLE_EDGE,
            3,
        )
        arcade.draw_line(
            center_x - 10,
            center_y,
            center_x + 10,
            center_y,
            theme.ARENA_CIRCLE_EDGE,
            1,
        )
        arcade.draw_line(
            center_x,
            center_y - 10,
            center_x,
            center_y + 10,
            theme.ARENA_CIRCLE_EDGE,
            1,
        )

        flag_owner = flag.get("owner")
        flag_x, flag_y = logical_to_screen(
            float(flag.get("x", MAP_CENTER_X)),
            float(flag.get("y", MAP_CENTER_Y)),
            arena,
        )
        self._draw_flag(flag_x, flag_y, player_radius, carried=flag_owner is not None)

        # Primero se dibujan los demás y al final el jugador local para que
        # su contorno siempre sea visible.
        ordered_players = sorted(
            players,
            key=lambda player: player.get("id") == own_player_id,
        )
        visible_ids: set[str] = set()

        for player in ordered_players:
            player_id = str(player.get("id", ""))
            visible_ids.add(player_id)
            x, y = logical_to_screen(
                float(player.get("x", MAP_CENTER_X)),
                float(player.get("y", MAP_CENTER_Y)),
                arena,
            )
            carrying = player_id == flag_owner
            is_me = player_id == own_player_id

            if carrying:
                color = theme.PLAYER_CARRIER
            elif is_me:
                color = theme.PLAYER_SELF
            else:
                color = theme.PLAYER_OTHER

            arcade.draw_circle_filled(x + 3, y - 4, player_radius + 2, theme.SHADOW)
            arcade.draw_circle_filled(x, y, player_radius, color)
            arcade.draw_circle_outline(
                x,
                y,
                player_radius,
                theme.PLAYER_OUTLINE if is_me else theme.BORDER,
                3 if is_me else 1,
            )

            if carrying:
                arcade.draw_circle_outline(
                    x,
                    y,
                    player_radius + 5,
                    theme.WARNING,
                    2,
                )

            name = str(player.get("name", player_id))
            self.texts.draw(
                f"arena-name-{player_id}",
                name,
                x,
                y + player_radius + 9,
                theme.TEXT,
                10,
                anchor_x="center",
                bold=is_me,
            )

    def _draw_grid(self, arena: Rect) -> None:
        for logical_value in range(100, int(MAP_SIZE), 100):
            x1, y_bottom = logical_to_screen(logical_value, MAP_SIZE, arena)
            x2, y_top = logical_to_screen(logical_value, 0, arena)
            arcade.draw_line(x1, y_bottom, x2, y_top, theme.ARENA_GRID, 1)

            x_left, y1 = logical_to_screen(0, logical_value, arena)
            x_right, y2 = logical_to_screen(MAP_SIZE, logical_value, arena)
            arcade.draw_line(x_left, y1, x_right, y2, theme.ARENA_GRID, 1)

    @staticmethod
    def _draw_flag(
        x: float,
        y: float,
        player_radius: float,
        *,
        carried: bool,
    ) -> None:
        pole_height = max(20.0, player_radius * 2.3)
        pole_x = x - player_radius * 0.45
        pole_bottom = y - pole_height * 0.45
        pole_top = pole_bottom + pole_height

        arcade.draw_line(
            pole_x + 2,
            pole_bottom - 2,
            pole_x + 2,
            pole_top - 2,
            theme.SHADOW,
            4,
        )
        arcade.draw_line(
            pole_x,
            pole_bottom,
            pole_x,
            pole_top,
            theme.FLAG_POLE,
            3,
        )

        flag_width = max(16.0, player_radius * 1.35)
        flag_height = max(10.0, player_radius * 0.8)
        flag_points = [
            (pole_x, pole_top),
            (pole_x + flag_width, pole_top - flag_height * 0.25),
            (pole_x + flag_width * 0.82, pole_top - flag_height),
            (pole_x, pole_top - flag_height * 0.78),
        ]
        arcade.draw_polygon_filled(flag_points, theme.FLAG)
        arcade.draw_polygon_outline(flag_points, theme.WARNING_DARK, 1)

        if carried:
            arcade.draw_circle_outline(x, y, player_radius + 9, theme.WARNING, 1)
