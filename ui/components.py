"""Componentes de dibujo reutilizables para Arcade."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import arcade

from ui import theme
from ui.layout import Rect


def rectangle_points(rect: Rect) -> list[tuple[float, float]]:
    return [
        (rect.left, rect.bottom),
        (rect.right, rect.bottom),
        (rect.right, rect.top),
        (rect.left, rect.top),
    ]


def draw_panel(
    rect: Rect,
    fill: tuple[int, ...] = theme.PANEL,
    border: tuple[int, ...] = theme.BORDER_SOFT,
    border_width: float = 1.0,
) -> None:
    arcade.draw_polygon_filled(rectangle_points(rect), fill)
    arcade.draw_polygon_outline(rectangle_points(rect), border, border_width)


def draw_divider(x1: float, y1: float, x2: float, y2: float) -> None:
    arcade.draw_line(x1, y1, x2, y2, theme.BORDER_SOFT, 1)


class TextRegistry:
    """Mantiene objetos arcade.Text para evitar recrear texto cada frame."""

    def __init__(self) -> None:
        self._items: dict[str, Any] = {}

    def draw(
        self,
        key: str,
        text: str,
        x: float,
        y: float,
        color: tuple[int, ...] = theme.TEXT,
        font_size: float = 12,
        *,
        anchor_x: str = "left",
        anchor_y: str = "baseline",
        bold: bool = False,
        width: float | None = None,
        multiline: bool = False,
        align: str = "left",
    ) -> None:
        item = self._items.get(key)
        if item is None:
            item = arcade.Text(
                text,
                x,
                y,
                color,
                font_size,
                width=int(width) if width is not None else None,
                align=align,
                bold=bold,
                anchor_x=anchor_x,
                anchor_y=anchor_y,
                multiline=multiline,
                font_name=("Segoe UI", "Arial"),
            )
            self._items[key] = item
        else:
            item.text = text
            item.x = x
            item.y = y
            item.color = color
            item.width = int(width) if width is not None else None
        item.draw()


def draw_badge(
    texts: TextRegistry,
    key: str,
    label: str,
    x: float,
    y: float,
    color: tuple[int, ...],
) -> None:
    width = max(92.0, 18.0 + len(label) * 7.0)
    rect = Rect(x, y, width, 28.0)
    draw_panel(rect, (*color[:3], 45), color, 1)
    texts.draw(
        key,
        label,
        rect.center_x,
        rect.center_y,
        color,
        10,
        anchor_x="center",
        anchor_y="center",
        bold=True,
    )


def draw_button(
    texts: TextRegistry,
    key: str,
    rect: Rect,
    label: str,
    *,
    enabled: bool,
    hovered: bool = False,
    accent: tuple[int, ...] = theme.SUCCESS,
) -> None:
    if enabled:
        fill = theme.PANEL_HOVER if hovered else theme.PANEL_ALT
        border = accent
        text_color = theme.TEXT
    else:
        fill = theme.PANEL
        border = theme.BORDER_SOFT
        text_color = theme.TEXT_DIM

    draw_panel(rect, fill, border, 2)
    texts.draw(
        key,
        label,
        rect.center_x,
        rect.center_y + 1,
        text_color,
        13,
        anchor_x="center",
        anchor_y="center",
        bold=True,
    )


def draw_key_hint(
    texts: TextRegistry,
    key: str,
    key_label: str,
    description: str,
    x: float,
    y: float,
) -> None:
    key_rect = Rect(x, y - 4, 48, 28)
    draw_panel(key_rect, theme.PANEL_ALT, theme.BORDER, 1)
    texts.draw(
        f"{key}-key",
        key_label,
        key_rect.center_x,
        key_rect.center_y,
        theme.PRIMARY,
        11,
        anchor_x="center",
        anchor_y="center",
        bold=True,
    )
    texts.draw(
        f"{key}-description",
        description,
        key_rect.right + 12,
        y + 4,
        theme.TEXT_MUTED,
        11,
    )


def truncate(value: str, max_length: int) -> str:
    if len(value) <= max_length:
        return value
    return value[: max(1, max_length - 3)] + "..."


def draw_player_list(
    texts: TextRegistry,
    players: Iterable[dict[str, Any]],
    *,
    own_id: str | None,
    flag_owner: str | None,
    x: float,
    start_y: float,
    width: float,
    max_rows: int,
    key_prefix: str,
) -> None:
    players_list = list(players)
    row_height = 30.0

    for index, player in enumerate(players_list[:max_rows]):
        player_id = str(player.get("id", ""))
        name = truncate(str(player.get("name", player_id)), 24)
        y = start_y - index * row_height

        if player_id == flag_owner:
            dot_color = theme.PLAYER_CARRIER
            suffix = "  • BANDERA"
        elif player_id == own_id:
            dot_color = theme.PLAYER_SELF
            suffix = "  • TÚ"
        else:
            dot_color = theme.PLAYER_OTHER
            suffix = ""

        arcade.draw_circle_filled(x + 6, y + 5, 5, dot_color)
        texts.draw(
            f"{key_prefix}-{player_id}",
            name + suffix,
            x + 20,
            y,
            theme.TEXT if player_id == own_id else theme.TEXT_MUTED,
            10,
            bold=player_id == own_id,
        )

    remaining = len(players_list) - max_rows
    if remaining > 0:
        texts.draw(
            f"{key_prefix}-remaining",
            f"+ {remaining} jugador(es) más",
            x,
            start_y - max_rows * row_height,
            theme.TEXT_DIM,
            10,
        )
