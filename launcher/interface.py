"""Dibujo del menú inicial para elegir servidor o cliente."""

from __future__ import annotations

from typing import Any

import arcade

from launcher.widgets import TextField
from ui import theme
from ui.components import TextRegistry, draw_button, draw_divider, draw_panel
from ui.layout import Rect


class LauncherInterface:
    def __init__(self) -> None:
        self.texts = TextRegistry()

    def draw(
        self,
        width: float,
        height: float,
        *,
        screen: str,
        fields: dict[str, TextField],
        servers: list[dict[str, Any]],
        selected_server: int | None,
        server_offset: int,
        hovered: str | None,
        busy: bool,
        status: str,
        error: str,
        cursor_visible: bool,
    ) -> dict[str, Rect]:
        self._background(width, height)
        bounds = self._bounds(width, height, screen, len(servers), server_offset)
        self._header(width, height, screen)

        if screen == "home":
            self._home(bounds, hovered)
        elif screen == "server":
            self._server(bounds, fields, hovered, busy, cursor_visible)
        else:
            self._client(
                bounds, fields, servers, selected_server, server_offset,
                hovered, busy, cursor_visible
            )

        self._status(width, status, error, busy)
        return bounds

    def _background(self, width: float, height: float) -> None:
        arcade.draw_lrbt_rectangle_filled(0, width, 0, height, theme.BACKGROUND)
        # Líneas decorativas sutiles.
        step = 54
        for x in range(0, int(width) + step, step):
            arcade.draw_line(x, 0, x, height, (*theme.ARENA_GRID, 70), 1)
        for y in range(0, int(height) + step, step):
            arcade.draw_line(0, y, width, y, (*theme.ARENA_GRID, 55), 1)

    def _header(self, width: float, height: float, screen: str) -> None:
        arcade.draw_lrbt_rectangle_filled(0, width, height - 88, height, theme.HEADER)
        draw_divider(0, height - 88, width, height - 88)
        self.texts.draw(
            "launcher-title",
            "CAPTURA LA BANDERA",
            28,
            height - 35,
            theme.TEXT,
            21,
            bold=True,
        )
        labels = {
            "home": "MENÚ PRINCIPAL",
            "server": "CONFIGURAR SERVIDOR",
            "client": "UNIRSE A UNA PARTIDA",
        }
        self.texts.draw(
            "launcher-subtitle",
            labels[screen],
            30,
            height - 63,
            theme.TEXT_MUTED,
            10,
        )
        self.texts.draw(
            "launcher-tech",
            "PYTHON  •  SOCKETS  •  ARCADE",
            width - 28,
            height - 50,
            theme.PRIMARY,
            9,
            anchor_x="right",
            bold=True,
        )

    def _home(self, bounds: dict[str, Rect], hovered: str | None) -> None:
        card = bounds["card"]
        draw_panel(card, theme.PANEL, theme.BORDER, 1)
        self.texts.draw(
            "home-heading",
            "¿CÓMO QUIERES ENTRAR?",
            card.center_x,
            card.top - 60,
            theme.TEXT,
            20,
            anchor_x="center",
            bold=True,
        )
        self.texts.draw(
            "home-help",
            "Ejecuta servidor o cliente desde el mismo programa.",
            card.center_x,
            card.top - 92,
            theme.TEXT_MUTED,
            11,
            anchor_x="center",
        )

        self._mode_card(
            bounds["choose_server"],
            "SERVIDOR",
            "Crear una partida, recibir jugadores y decidir cuándo iniciar.",
            "S",
            theme.SUCCESS,
            hovered == "choose_server",
        )
        self._mode_card(
            bounds["choose_client"],
            "CLIENTE",
            "Buscar un servidor o conectarte con la IP de Radmin VPN.",
            "C",
            theme.PRIMARY,
            hovered == "choose_client",
        )

    def _mode_card(
        self,
        rect: Rect,
        title: str,
        description: str,
        letter: str,
        accent: tuple[int, ...],
        hovered: bool,
    ) -> None:
        fill = theme.PANEL_HOVER if hovered else theme.PANEL_ALT
        draw_panel(rect, fill, accent, 2)
        arcade.draw_circle_filled(rect.left + 55, rect.center_y, 28, (*accent[:3], 42))
        arcade.draw_circle_outline(rect.left + 55, rect.center_y, 28, accent, 2)
        self.texts.draw(
            f"mode-{title}-letter",
            letter,
            rect.left + 55,
            rect.center_y + 1,
            accent,
            18,
            anchor_x="center",
            anchor_y="center",
            bold=True,
        )
        self.texts.draw(
            f"mode-{title}-title",
            title,
            rect.left + 102,
            rect.center_y + 22,
            theme.TEXT,
            16,
            bold=True,
        )
        self.texts.draw(
            f"mode-{title}-desc",
            description,
            rect.left + 102,
            rect.center_y - 8,
            theme.TEXT_MUTED,
            10,
            width=rect.width - 125,
            multiline=True,
        )

    def _server(
        self,
        bounds: dict[str, Rect],
        fields: dict[str, TextField],
        hovered: str | None,
        busy: bool,
        cursor_visible: bool,
    ) -> None:
        card = bounds["card"]
        draw_panel(card, theme.PANEL, theme.BORDER, 1)
        self._section_title(card, "NUEVA PARTIDA", "Tu equipo escuchará conexiones de la red y Radmin VPN.")
        fields["server_name"].draw(self.texts, "server-name", bounds["server_name"], cursor_visible)
        fields["server_port"].draw(self.texts, "server-port", bounds["server_port"], cursor_visible)

        info = bounds["server_info"]
        draw_panel(info, (*theme.PRIMARY_DARK, 34), theme.PRIMARY_DARK, 1)
        self.texts.draw(
            "server-info-title",
            "CONFIGURACIÓN DE RED",
            info.left + 16,
            info.top - 25,
            theme.PRIMARY,
            10,
            bold=True,
        )
        self.texts.draw(
            "server-info-body",
            "IP de escucha: 0.0.0.0\nDescubrimiento UDP: puerto 8888\nEl servidor solo observa; los jugadores entran como clientes.",
            info.left + 16,
            info.top - 52,
            theme.TEXT_MUTED,
            10,
            width=info.width - 32,
            multiline=True,
        )
        draw_button(
            self.texts,
            "start-server",
            bounds["start_server"],
            "INICIAR SERVIDOR",
            enabled=not busy,
            hovered=hovered == "start_server",
            accent=theme.SUCCESS,
        )
        draw_button(
            self.texts,
            "back-server",
            bounds["back"],
            "VOLVER",
            enabled=not busy,
            hovered=hovered == "back",
            accent=theme.BORDER,
        )

    def _client(
        self,
        bounds: dict[str, Rect],
        fields: dict[str, TextField],
        servers: list[dict[str, Any]],
        selected_server: int | None,
        server_offset: int,
        hovered: str | None,
        busy: bool,
        cursor_visible: bool,
    ) -> None:
        card = bounds["card"]
        draw_panel(card, theme.PANEL, theme.BORDER, 1)
        self._section_title(card, "CONECTAR COMO CLIENTE", "Ingresa una IP o busca servidores disponibles.")

        fields["client_name"].draw(self.texts, "client-name", bounds["client_name"], cursor_visible)
        fields["client_host"].draw(self.texts, "client-host", bounds["client_host"], cursor_visible)
        fields["client_port"].draw(self.texts, "client-port", bounds["client_port"], cursor_visible)

        draw_button(
            self.texts,
            "connect-client",
            bounds["connect"],
            "CONECTAR",
            enabled=not busy,
            hovered=hovered == "connect",
            accent=theme.SUCCESS,
        )
        draw_button(
            self.texts,
            "search-client",
            bounds["search"],
            "BUSCAR / ACTUALIZAR",
            enabled=not busy,
            hovered=hovered == "search",
            accent=theme.PRIMARY,
        )
        draw_button(
            self.texts,
            "join-selected-client",
            bounds["join_selected"],
            "UNIRSE AL SELECCIONADO",
            enabled=not busy and selected_server is not None,
            hovered=hovered == "join_selected",
            accent=theme.SUCCESS,
        )
        draw_button(
            self.texts,
            "back-client",
            bounds["back"],
            "VOLVER",
            enabled=not busy,
            hovered=hovered == "back",
            accent=theme.BORDER,
        )

        list_rect = bounds["server_list"]
        draw_panel(list_rect, theme.PANEL_ALT, theme.BORDER_SOFT, 1)
        self.texts.draw(
            "servers-title",
            f"SERVIDORES ENCONTRADOS ({len(servers)})",
            list_rect.left + 16,
            list_rect.top - 25,
            theme.TEXT,
            10,
            bold=True,
        )
        draw_divider(list_rect.left + 14, list_rect.top - 42, list_rect.right - 14, list_rect.top - 42)

        if not servers:
            self.texts.draw(
                "servers-empty",
                "Presiona “BUSCAR / ACTUALIZAR” para enviar el broadcast UDP.",
                list_rect.center_x,
                list_rect.center_y - 4,
                theme.TEXT_DIM,
                10,
                anchor_x="center",
            )
            return

        visible = list(enumerate(servers))[server_offset : server_offset + 4]
        for index, server in visible:
            row = bounds[f"server_{index}"]
            selected = selected_server == index
            row_fill = theme.PANEL_HOVER if selected or hovered == f"server_{index}" else theme.PANEL
            border = theme.SUCCESS if selected else (theme.PRIMARY if hovered == f"server_{index}" else theme.BORDER_SOFT)
            draw_panel(row, row_fill, border, 2 if selected else 1)
            name = str(server.get("name", "Servidor CTF"))
            ip = str(server.get("ip", "?"))
            port = server.get("tcp_port", "?")
            players = server.get("players", 0)
            state = str(server.get("state", "?"))
            self.texts.draw(
                f"server-row-name-{index}",
                name,
                row.left + 12,
                row.center_y + 9,
                theme.TEXT,
                10,
                bold=True,
            )
            self.texts.draw(
                f"server-row-info-{index}",
                f"{ip}:{port}  •  {state}  •  {players} jugador(es)",
                row.left + 12,
                row.center_y - 11,
                theme.TEXT_MUTED,
                9,
            )
            self.texts.draw(
                f"server-row-action-{index}",
                "SELECCIONADO" if selected else "SELECCIONAR",
                row.right - 14,
                row.center_y,
                theme.SUCCESS if selected else theme.PRIMARY,
                9,
                anchor_x="right",
                anchor_y="center",
                bold=True,
            )

        shown_from = server_offset + 1
        shown_to = min(len(servers), server_offset + 4)
        self.texts.draw(
            "servers-scroll-hint",
            f"Mostrando {shown_from}-{shown_to} de {len(servers)}  •  Usa la rueda del mouse para desplazarte",
            list_rect.left + 16,
            list_rect.bottom + 10,
            theme.TEXT_DIM,
            8,
        )

    def _section_title(self, card: Rect, title: str, subtitle: str) -> None:
        self.texts.draw(
            f"section-{title}",
            title,
            card.left + 34,
            card.top - 48,
            theme.TEXT,
            18,
            bold=True,
        )
        self.texts.draw(
            f"section-sub-{title}",
            subtitle,
            card.left + 34,
            card.top - 76,
            theme.TEXT_MUTED,
            10,
        )

    def _status(self, width: float, status: str, error: str, busy: bool) -> None:
        if not status and not error and not busy:
            return
        color = theme.DANGER if error else theme.PRIMARY
        text = error or status or "Procesando..."
        rect = Rect(20, 15, max(280, width - 40), 34)
        draw_panel(rect, (*color[:3], 32), color, 1)
        self.texts.draw(
            "launcher-status",
            ("PROCESANDO  •  " if busy else "") + text,
            rect.left + 14,
            rect.center_y,
            color,
            10,
            anchor_y="center",
            bold=True,
        )

    def _bounds(
        self, width: float, height: float, screen: str, server_count: int, server_offset: int
    ) -> dict[str, Rect]:
        card_width = min(870.0, max(700.0, width - 90.0))
        card_height = min(540.0, max(470.0, height - 155.0))
        card = Rect((width - card_width) / 2, 68, card_width, card_height)
        bounds: dict[str, Rect] = {"card": card}

        if screen == "home":
            option_width = (card.width - 92) / 2
            bounds["choose_server"] = Rect(card.left + 34, card.bottom + 105, option_width, 220)
            bounds["choose_client"] = Rect(card.left + 58 + option_width, card.bottom + 105, option_width, 220)
            return bounds

        bounds["back"] = Rect(card.left + 34, card.bottom + 26, 128, 40)
        if screen == "server":
            bounds["server_name"] = Rect(card.left + 34, card.top - 155, card.width - 68, 48)
            bounds["server_port"] = Rect(card.left + 34, card.top - 236, 210, 48)
            bounds["server_info"] = Rect(card.left + 270, card.top - 288, card.width - 304, 100)
            bounds["start_server"] = Rect(card.right - 260, card.bottom + 26, 226, 40)
            return bounds

        left = card.left + 34
        top = card.top
        bounds["client_name"] = Rect(left, top - 145, 250, 44)
        bounds["client_host"] = Rect(left + 270, top - 145, 285, 44)
        bounds["client_port"] = Rect(left + 575, top - 145, card.right - (left + 575) - 34, 44)
        bounds["connect"] = Rect(left, top - 210, 180, 40)
        bounds["search"] = Rect(left + 194, top - 210, 220, 40)
        bounds["join_selected"] = Rect(left + 428, top - 210, 270, 40)
        bounds["server_list"] = Rect(left, card.bottom + 84, card.width - 68, max(135, card.height - 325))

        list_rect = bounds["server_list"]
        row_height = 48
        row_top = list_rect.top - 52
        visible_indices = range(server_offset, min(server_count, server_offset + 4))
        for visual_row, index in enumerate(visible_indices):
            bounds[f"server_{index}"] = Rect(
                list_rect.left + 12,
                row_top - (visual_row + 1) * row_height,
                list_rect.width - 24,
                row_height - 6,
            )
        return bounds
