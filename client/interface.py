"""Presentación visual del cliente, separada de la lógica de red y controles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import arcade

from ui import theme
from ui.components import (
    TextRegistry,
    draw_badge,
    draw_divider,
    draw_key_hint,
    draw_panel,
    draw_player_list,
)
from ui.game_scene import GameSceneRenderer
from ui.layout import AppLayout, Rect, calculate_layout


@dataclass
class ClientUIState:
    player_id: str | None
    player_name: str
    host: str
    port: int
    phase: str
    players: dict[str, dict[str, Any]]
    flag: dict[str, Any]
    countdown: int | None
    winner: str | None
    error_message: str
    config: dict[str, Any]


class ClientInterface:
    """Dibuja toda la interfaz del cliente."""

    def __init__(self) -> None:
        self.texts = TextRegistry()
        self.scene = GameSceneRenderer()

    def draw(self, width: float, height: float, state: ClientUIState) -> None:
        layout = calculate_layout(width, height)
        self._draw_header(layout, state)
        draw_panel(layout.arena_card, theme.PANEL, theme.BORDER_SOFT, 1)

        players = list(state.players.values())
        self.scene.draw(
            layout.arena,
            players,
            state.flag,
            own_player_id=state.player_id,
            config=state.config,
        )

        self._draw_arena_caption(layout, state)
        self._draw_sidebar(layout, state)
        self._draw_overlay(layout, state)

    def _draw_header(self, layout: AppLayout, state: ClientUIState) -> None:
        arcade.draw_polygon_filled(
            [
                (layout.header.left, layout.header.bottom),
                (layout.header.right, layout.header.bottom),
                (layout.header.right, layout.header.top),
                (layout.header.left, layout.header.top),
            ],
            theme.HEADER,
        )
        draw_divider(
            layout.header.left,
            layout.header.bottom,
            layout.header.right,
            layout.header.bottom,
        )

        self.texts.draw(
            "client-title",
            "CAPTURA LA BANDERA",
            20,
            layout.header.center_y + 8,
            theme.TEXT,
            18,
            anchor_y="center",
            bold=True,
        )
        self.texts.draw(
            "client-subtitle",
            f"Cliente Python Arcade  •  {state.host}:{state.port}",
            20,
            layout.header.center_y - 15,
            theme.TEXT_MUTED,
            10,
            anchor_y="center",
        )

        phase_color = theme.PHASE_COLORS.get(state.phase, theme.TEXT_DIM)
        phase_label = theme.PHASE_LABELS.get(state.phase, state.phase.upper())
        badge_width = max(120.0, len(phase_label) * 7.0 + 24.0)
        draw_badge(
            self.texts,
            "client-phase",
            phase_label,
            layout.header.right - badge_width - 20,
            layout.header.center_y - 14,
            phase_color,
        )

    def _draw_arena_caption(self, layout: AppLayout, state: ClientUIState) -> None:
        self.texts.draw(
            "arena-help",
            "Entra al círculo, toma la bandera y sal completamente para ganar.",
            layout.arena_card.center_x,
            layout.arena_card.bottom + 8,
            theme.TEXT_DIM,
            9,
            anchor_x="center",
        )

    def _draw_sidebar(self, layout: AppLayout, state: ClientUIState) -> None:
        sidebar = layout.sidebar
        gap = 12.0

        identity_height = 112.0
        identity = Rect(sidebar.left, sidebar.top - identity_height, sidebar.width, identity_height)
        draw_panel(identity, theme.PANEL, theme.BORDER_SOFT, 1)
        self.texts.draw(
            "identity-label",
            "TU JUGADOR",
            identity.left + 16,
            identity.top - 25,
            theme.TEXT_DIM,
            9,
            bold=True,
        )
        self.texts.draw(
            "identity-name",
            state.player_name,
            identity.left + 16,
            identity.top - 56,
            theme.TEXT,
            20,
            bold=True,
        )
        status = "Conectado al servidor" if state.phase != "disconnected" else "Sin conexión"
        status_color = theme.SUCCESS if state.phase != "disconnected" else theme.DANGER
        arcade.draw_circle_filled(identity.left + 20, identity.bottom + 21, 5, status_color)
        self.texts.draw(
            "identity-status",
            status,
            identity.left + 34,
            identity.bottom + 16,
            theme.TEXT_MUTED,
            10,
        )

        players_height = min(255.0, max(170.0, sidebar.height * 0.36))
        players_card = Rect(
            sidebar.left,
            identity.bottom - gap - players_height,
            sidebar.width,
            players_height,
        )
        draw_panel(players_card, theme.PANEL, theme.BORDER_SOFT, 1)
        self.texts.draw(
            "players-title",
            f"JUGADORES  ({len(state.players)})",
            players_card.left + 16,
            players_card.top - 25,
            theme.TEXT,
            11,
            bold=True,
        )
        draw_divider(
            players_card.left + 16,
            players_card.top - 40,
            players_card.right - 16,
            players_card.top - 40,
        )
        max_rows = max(2, int((players_card.height - 64) // 30))
        draw_player_list(
            self.texts,
            state.players.values(),
            own_id=state.player_id,
            flag_owner=state.flag.get("owner"),
            x=players_card.left + 18,
            start_y=players_card.top - 66,
            width=players_card.width - 36,
            max_rows=max_rows,
            key_prefix="client-player-list",
        )

        controls_top = players_card.bottom - gap
        controls_height = max(176.0, controls_top - sidebar.bottom)
        controls = Rect(sidebar.left, sidebar.bottom, sidebar.width, controls_height)
        draw_panel(controls, theme.PANEL, theme.BORDER_SOFT, 1)
        self.texts.draw(
            "controls-title",
            "CONTROLES",
            controls.left + 16,
            controls.top - 25,
            theme.TEXT,
            11,
            bold=True,
        )
        draw_key_hint(
            self.texts,
            "move",
            "WASD",
            "Mover al jugador",
            controls.left + 16,
            controls.top - 69,
        )
        draw_key_hint(
            self.texts,
            "interact",
            "E",
            "Tomar o robar bandera",
            controls.left + 16,
            controls.top - 110,
        )

        if state.error_message:
            error_box = Rect(
                controls.left + 14,
                controls.bottom + 14,
                controls.width - 28,
                46,
            )
            draw_panel(error_box, (*theme.DANGER_DARK, 80), theme.DANGER, 1)
            self.texts.draw(
                "client-error",
                state.error_message,
                error_box.center_x,
                error_box.center_y,
                theme.DANGER,
                9,
                anchor_x="center",
                anchor_y="center",
                width=error_box.width - 16,
                multiline=True,
                align="center",
            )

    def _draw_overlay(self, layout: AppLayout, state: ClientUIState) -> None:
        arena = layout.arena
        if state.countdown is not None:
            overlay = Rect(
                arena.center_x - 110,
                arena.center_y - 70,
                220,
                140,
            )
            draw_panel(overlay, (*theme.HEADER, 235), theme.WARNING, 2)
            self.texts.draw(
                "countdown-label",
                "LA PARTIDA INICIA EN",
                overlay.center_x,
                overlay.top - 30,
                theme.TEXT_MUTED,
                10,
                anchor_x="center",
                bold=True,
            )
            self.texts.draw(
                "countdown-number",
                str(state.countdown),
                overlay.center_x,
                overlay.center_y - 12,
                theme.WARNING,
                48,
                anchor_x="center",
                anchor_y="center",
                bold=True,
            )

        if state.winner is not None:
            winner_name = state.players.get(state.winner, {}).get("name", state.winner)
            won = state.winner == state.player_id
            title = "¡GANASTE!" if won else "PARTIDA FINALIZADA"
            subtitle = "Sacaste la bandera del círculo" if won else f"Ganó {winner_name}"
            accent = theme.SUCCESS if won else theme.PURPLE
            overlay = Rect(
                arena.center_x - 175,
                arena.center_y - 70,
                350,
                140,
            )
            draw_panel(overlay, (*theme.HEADER, 240), accent, 2)
            self.texts.draw(
                "winner-title",
                title,
                overlay.center_x,
                overlay.center_y + 20,
                accent,
                24,
                anchor_x="center",
                anchor_y="center",
                bold=True,
            )
            self.texts.draw(
                "winner-subtitle",
                subtitle,
                overlay.center_x,
                overlay.center_y - 22,
                theme.TEXT_MUTED,
                11,
                anchor_x="center",
                anchor_y="center",
            )
