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


def merge_player_state(
    raw: Any,
    previous: dict[str, dict[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    """Actualiza posiciones sin perder los nombres recibidos en ``lobby``.

    El protocolo CTF envía los nombres en ``lobby.players`` y normalmente
    envía solo ``id``, ``x`` y ``y`` en ``state.players``. Por eso no debemos
    reemplazar por completo los jugadores al recibir cada estado.
    """

    old_players = previous or {}
    current_players = normalize_players(raw)
    merged: dict[str, dict[str, Any]] = {}

    for player_id, state_player in current_players.items():
        player = dict(old_players.get(player_id, {}))
        player.update(state_player)
        player["id"] = player_id

        # Conserva el nombre del lobby. Si el servidor también lo manda en
        # state, se utiliza ese valor; si no existe, se muestra el ID.
        name = player.get("name") or old_players.get(player_id, {}).get("name")
        player["name"] = str(name or player_id)
        merged[player_id] = player

    return merged


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
