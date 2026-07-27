"""Funciones pequeñas para convertir coordenadas lógicas a pantalla."""

from __future__ import annotations

from common.constants import MAP_SIZE


def logical_to_screen(
    x: float,
    y: float,
    width: float,
    height: float,
) -> tuple[float, float]:
    """Convierte el eje Y del protocolo (crece hacia abajo) al de Arcade."""

    scale_x = width / MAP_SIZE
    scale_y = height / MAP_SIZE
    return x * scale_x, height - (y * scale_y)


def logical_radius_to_screen(radius: float, width: float, height: float) -> float:
    scale = min(width / MAP_SIZE, height / MAP_SIZE)
    return radius * scale
