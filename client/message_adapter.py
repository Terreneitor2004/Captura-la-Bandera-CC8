"""Compatibilidad con variantes usadas por otros proyectos CTF."""

from typing import Any


def normalize_players(raw: Any) -> dict[str, dict[str, Any]]:
    if isinstance(raw, dict):
        items = raw.items()
    elif isinstance(raw, list):
        items = ((player.get("id"), player) for player in raw if isinstance(player, dict))
    else:
        return {}

    return {
        player_id: {**data, "id": player_id}
        for player_id, data in items
        if isinstance(player_id, str) and isinstance(data, dict)
    }


def normalize_flag(
    raw: Any,
    previous: dict[str, Any] | None = None,
) -> dict[str, Any]:
    old = previous or {"owner": None, "x": 500.0, "y": 500.0}
    if not isinstance(raw, dict):
        return dict(old)
    return {
        "owner": raw.get("owner", raw.get("carrier_id")),
        "x": raw.get("x", old["x"]),
        "y": raw.get("y", old["y"]),
    }
