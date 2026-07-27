"""Cálculo de posiciones para una interfaz adaptable y arena cuadrada."""

from __future__ import annotations

from dataclasses import dataclass

from common.constants import MAP_SIZE


@dataclass(frozen=True)
class Rect:
    left: float
    bottom: float
    width: float
    height: float

    @property
    def right(self) -> float:
        return self.left + self.width

    @property
    def top(self) -> float:
        return self.bottom + self.height

    @property
    def center_x(self) -> float:
        return self.left + self.width / 2

    @property
    def center_y(self) -> float:
        return self.bottom + self.height / 2

    def contains(self, x: float, y: float) -> bool:
        return self.left <= x <= self.right and self.bottom <= y <= self.top

    def inset(self, amount: float) -> "Rect":
        return Rect(
            self.left + amount,
            self.bottom + amount,
            max(0.0, self.width - amount * 2),
            max(0.0, self.height - amount * 2),
        )


@dataclass(frozen=True)
class AppLayout:
    header: Rect
    arena_card: Rect
    arena: Rect
    sidebar: Rect


def calculate_layout(width: float, height: float) -> AppLayout:
    """Crea un área de juego cuadrada y un panel lateral independiente."""

    margin = 18.0
    gap = 18.0
    header_height = 66.0

    header = Rect(0.0, height - header_height, width, header_height)
    content_bottom = margin
    content_top = height - header_height - margin
    content_height = max(260.0, content_top - content_bottom)

    # Panel lateral adaptable. Conserva suficiente espacio para el mapa.
    sidebar_width = min(390.0, max(300.0, width * 0.32))
    arena_column_width = max(260.0, width - margin * 2 - gap - sidebar_width)

    arena_card = Rect(margin, content_bottom, arena_column_width, content_height)
    sidebar = Rect(arena_card.right + gap, content_bottom, sidebar_width, content_height)

    arena_padding = 18.0
    available_width = max(1.0, arena_card.width - arena_padding * 2)
    available_height = max(1.0, arena_card.height - arena_padding * 2)
    arena_size = min(available_width, available_height)

    arena = Rect(
        arena_card.left + (arena_card.width - arena_size) / 2,
        arena_card.bottom + (arena_card.height - arena_size) / 2,
        arena_size,
        arena_size,
    )

    return AppLayout(header, arena_card, arena, sidebar)


def logical_to_screen(x: float, y: float, arena: Rect) -> tuple[float, float]:
    """Convierte coordenadas usando una sola escala en X e Y.

    El uso de una escala uniforme evita que el movimiento horizontal se vea
    más rápido que el vertical cuando la ventana cambia de proporción.
    """

    scale = arena.width / MAP_SIZE
    screen_x = arena.left + x * scale
    screen_y = arena.bottom + (MAP_SIZE - y) * scale
    return screen_x, screen_y


def logical_radius_to_screen(radius: float, arena: Rect) -> float:
    return radius * (arena.width / MAP_SIZE)
