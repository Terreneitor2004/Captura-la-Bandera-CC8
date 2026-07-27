"""Adaptadores de mensajes para compatibilidad entre proyectos CTF.

El estándar define players como una lista y flag.owner. Algunos servidores de
la clase usan un diccionario indexado por ID y flag.carrier_id. Este módulo
convierte ambos formatos al formato interno utilizado por la interfaz.
"""

from __future__ import annotations

from typing import Any


def normalize_players(raw_players: Any) -> dict[str, dict[str, Any]]:
    """Acepta players como lista estándar o diccionario indexado por ID."""

    normalized: dict[str, dict[str, Any]] = {}

    if isinstance(raw_players, dict):
        for player_id, player_data in raw_players.items():
            if not isinstance(player_id, str) or not isinstance(player_data, dict):
                continue
            player = dict(player_data)
            player["id"] = player_id
            normalized[player_id] = player
        return normalized

    if isinstance(raw_players, list):
        for player_data in raw_players:
            if not isinstance(player_data, dict):
                continue
            player_id = player_data.get("id")
            if not isinstance(player_id, str):
                continue
            normalized[player_id] = dict(player_data)

    return normalized


def normalize_flag(
    raw_flag: Any,
    previous_flag: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Acepta flag.owner (estándar) o flag.carrier_id (compatibilidad)."""

    previous = previous_flag or {"owner": None, "x": 500.0, "y": 500.0}
    if not isinstance(raw_flag, dict):
        return dict(previous)

    owner = raw_flag.get("owner")
    if owner is None:
        owner = raw_flag.get("carrier_id")

    return {
        "owner": owner,
        "x": raw_flag.get("x", previous.get("x", 500.0)),
        "y": raw_flag.get("y", previous.get("y", 500.0)),
    }
