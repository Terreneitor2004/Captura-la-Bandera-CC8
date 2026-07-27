"""Compatibilidad para conversión de coordenadas.

Las interfaces nuevas usan ui.layout.Rect y una escala uniforme. Estas funciones
se mantienen para cualquier módulo externo que todavía importe common.rendering.
"""

from __future__ import annotations

from common.constants import MAP_SIZE


def logical_to_screen(
    x: float,
    y: float,
    width: float,
    height: float,
) -> tuple[float, float]:
    """Convierte coordenadas sin deformar el mapa.

    El mapa se centra dentro del espacio disponible y usa la misma escala en
    ambos ejes, evitando diferencias visuales de velocidad.
    """

    size = min(width, height)
    left = (width - size) / 2
    bottom = (height - size) / 2
    scale = size / MAP_SIZE
    return left + x * scale, bottom + (MAP_SIZE - y) * scale


def logical_radius_to_screen(radius: float, width: float, height: float) -> float:
    return radius * (min(width, height) / MAP_SIZE)
