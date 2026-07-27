"""Panel visual del servidor, separado de la lógica de sockets y del juego."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import arcade

from common.constants import (
    DISCOVERY_PORT,
    MIN_PLAYERS_TO_START,
    STATE_COUNTDOWN,
    STATE_FINISHED,
    STATE_LOBBY,
    STATE_PLAYING,
)
from ui import theme
from ui.components import (
    TextRegistry,
    draw_badge,
    draw_button,
    draw_divider,
    draw_panel,
    draw_player_list,
    truncate,
)
from ui.game_scene import GameSceneRenderer
from ui.layout import AppLayout, Rect, calculate_layout


@dataclass
class ServerUIState:
    server_name: str
    host: str
    tcp_port: int
    phase: str
    players: list[dict[str, Any]]
    flag_owner: str | None
    flag_x: float
    flag_y: float
    winner: str | None
    countdown: int | None
    events: list[str]
    feedback: str


class ServerInterface:
    def __init__(self) -> None:
        self.texts = TextRegistry()
        self.scene = GameSceneRenderer()

    def start_button_bounds(self, width: float, height: float) -> Rect:
        layout = calculate_layout(width, height)
        return Rect(layout.sidebar.left, layout.sidebar.top - 64, layout.sidebar.width, 64)

    def draw(
        self,
        width: float,
        height: float,
        state: ServerUIState,
        *,
        button_hovered: bool,
    ) -> None:
        layout = calculate_layout(width, height)
        self._draw_header(layout, state)
        draw_panel(layout.arena_card, theme.PANEL, theme.BORDER_SOFT, 1)

        flag = {
            "owner": state.flag_owner,
            "x": state.flag_x,
            "y": state.flag_y,
        }
        self.scene.draw(
            layout.arena,
            state.players,
            flag,
            own_player_id=None,
        )
        self.texts.draw(
            "server-arena-caption",
            "Vista autoritativa del servidor • El host observa y valida la partida.",
            layout.arena_card.center_x,
            layout.arena_card.bottom + 8,
            theme.TEXT_DIM,
            9,
            anchor_x="center",
        )

        self._draw_sidebar(layout, state, button_hovered)
        self._draw_winner_overlay(layout, state)

    def _draw_header(self, layout: AppLayout, state: ServerUIState) -> None:
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
            "server-title",
            "SERVIDOR CTF",
            20,
            layout.header.center_y + 8,
            theme.TEXT,
            18,
            anchor_y="center",
            bold=True,
        )
        self.texts.draw(
            "server-subtitle",
            f"{state.server_name}  •  TCP {state.host}:{state.tcp_port}  •  UDP {DISCOVERY_PORT}",
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
            "server-phase",
            phase_label,
            layout.header.right - badge_width - 20,
            layout.header.center_y - 14,
            phase_color,
        )

    def _draw_sidebar(
        self,
        layout: AppLayout,
        state: ServerUIState,
        button_hovered: bool,
    ) -> None:
        sidebar = layout.sidebar
        gap = 12.0
        player_count = len(state.players)

        button = Rect(sidebar.left, sidebar.top - 64, sidebar.width, 64)

        enabled = state.phase == STATE_LOBBY and player_count >= MIN_PLAYERS_TO_START
        if state.phase == STATE_LOBBY and enabled:
            button_label = "INICIAR PARTIDA"
        elif state.phase == STATE_LOBBY:
            button_label = f"ESPERANDO ({player_count}/{MIN_PLAYERS_TO_START})"
        elif state.phase == STATE_COUNTDOWN:
            button_label = f"INICIANDO EN {state.countdown or 1}"
        elif state.phase == STATE_PLAYING:
            button_label = "PARTIDA EN CURSO"
        elif state.phase == STATE_FINISHED:
            button_label = "PARTIDA FINALIZADA"
        else:
            button_label = state.phase.upper()

        draw_button(
            self.texts,
            "server-start-button",
            button,
            button_label,
            enabled=enabled,
            hovered=button_hovered,
            accent=theme.SUCCESS,
        )
        self.texts.draw(
            "server-start-help",
            "Haz clic o presiona ESPACIO",
            button.center_x,
            button.bottom - 17,
            theme.TEXT_DIM,
            9,
            anchor_x="center",
        )

        status_top = button.bottom - 34
        status_height = 94.0
        status = Rect(sidebar.left, status_top - status_height, sidebar.width, status_height)
        draw_panel(status, theme.PANEL, theme.BORDER_SOFT, 1)
        self.texts.draw(
            "server-status-title",
            "ESTADO DEL SERVIDOR",
            status.left + 16,
            status.top - 24,
            theme.TEXT,
            10,
            bold=True,
        )
        arcade.draw_circle_filled(status.left + 20, status.top - 52, 5, theme.SUCCESS)
        self.texts.draw(
            "server-online",
            "Servidor en línea",
            status.left + 34,
            status.top - 57,
            theme.TEXT_MUTED,
            10,
        )
        self.texts.draw(
            "server-count",
            f"{player_count} / 100 jugadores conectados",
            status.left + 16,
            status.bottom + 13,
            theme.TEXT_DIM,
            9,
        )

        players_height = min(205.0, max(140.0, sidebar.height * 0.29))
        players_card = Rect(
            sidebar.left,
            status.bottom - gap - players_height,
            sidebar.width,
            players_height,
        )
        draw_panel(players_card, theme.PANEL, theme.BORDER_SOFT, 1)
        self.texts.draw(
            "server-players-title",
            f"LOBBY  ({player_count})",
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
            state.players,
            own_id=None,
            flag_owner=state.flag_owner,
            x=players_card.left + 18,
            start_y=players_card.top - 66,
            width=players_card.width - 36,
            max_rows=max_rows,
            key_prefix="server-player-list",
        )

        event_top = players_card.bottom - gap
        events = Rect(sidebar.left, sidebar.bottom, sidebar.width, max(110.0, event_top - sidebar.bottom))
        draw_panel(events, theme.PANEL, theme.BORDER_SOFT, 1)
        self.texts.draw(
            "events-title",
            "EVENTOS DEL SERVIDOR",
            events.left + 16,
            events.top - 24,
            theme.TEXT,
            10,
            bold=True,
        )
        draw_divider(
            events.left + 16,
            events.top - 39,
            events.right - 16,
            events.top - 39,
        )

        max_events = max(2, int((events.height - 55) // 22))
        visible_events = state.events[-max_events:]
        start_y = events.top - 61
        for index, event in enumerate(visible_events):
            cleaned = event
            # La hora ocupa espacio pero ayuda a seguir el orden.
            self.texts.draw(
                f"server-event-{index}",
                truncate(cleaned, 56),
                events.left + 16,
                start_y - index * 22,
                theme.TEXT_MUTED,
                8,
            )

        if state.feedback:
            self.texts.draw(
                "server-feedback",
                truncate(state.feedback, 52),
                events.left + 16,
                events.bottom + 10,
                theme.PRIMARY,
                8,
                bold=True,
            )

    def _draw_winner_overlay(self, layout: AppLayout, state: ServerUIState) -> None:
        if state.winner is None:
            return

        winner_name = state.winner
        for player in state.players:
            if player.get("id") == state.winner:
                winner_name = str(player.get("name", state.winner))
                break

        overlay = Rect(
            layout.arena.center_x - 175,
            layout.arena.center_y - 65,
            350,
            130,
        )
        draw_panel(overlay, (*theme.HEADER, 240), theme.WARNING, 2)
        self.texts.draw(
            "server-winner-title",
            "GANADOR",
            overlay.center_x,
            overlay.center_y + 20,
            theme.WARNING,
            14,
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )
        self.texts.draw(
            "server-winner-name",
            winner_name,
            overlay.center_x,
            overlay.center_y - 18,
            theme.TEXT,
            24,
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )
