"""Controles pequeños usados por el menú inicial."""

from __future__ import annotations

from dataclasses import dataclass

import arcade

from ui import theme
from ui.components import TextRegistry, draw_panel
from ui.layout import Rect


@dataclass
class TextField:
    """Campo de texto sencillo para no mezclar la lógica con Arcade GUI."""

    label: str
    value: str = ""
    placeholder: str = ""
    max_length: int = 40
    numeric: bool = False
    active: bool = False

    def insert(self, text: str) -> None:
        if not self.active:
            return
        clean = "".join(ch for ch in text if ch.isprintable() and ch not in "\r\n\t")
        if self.numeric:
            clean = "".join(ch for ch in clean if ch.isdigit())
        self.value = (self.value + clean)[: self.max_length]

    def backspace(self) -> None:
        if self.active:
            self.value = self.value[:-1]

    def draw(self, texts: TextRegistry, key: str, rect: Rect, cursor_visible: bool) -> None:
        border = theme.PRIMARY if self.active else theme.BORDER
        fill = theme.PANEL_HOVER if self.active else theme.PANEL_ALT
        draw_panel(rect, fill, border, 2 if self.active else 1)

        texts.draw(
            f"{key}-label",
            self.label.upper(),
            rect.left,
            rect.top + 8,
            theme.TEXT_MUTED,
            9,
            bold=True,
        )

        visible = self.value
        if self.active and cursor_visible:
            visible += "|"
        if not visible:
            visible = self.placeholder
            color = theme.TEXT_DIM
        else:
            color = theme.TEXT

        texts.draw(
            f"{key}-value",
            visible,
            rect.left + 14,
            rect.center_y,
            color,
            12,
            anchor_y="center",
            width=max(40, rect.width - 28),
        )
