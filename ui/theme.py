"""Paleta visual del proyecto CTF."""

from __future__ import annotations

# Fondo general
BACKGROUND = (8, 15, 25)
HEADER = (12, 22, 35)
PANEL = (16, 28, 43)
PANEL_ALT = (22, 37, 55)
PANEL_HOVER = (28, 47, 68)
BORDER = (52, 75, 98)
BORDER_SOFT = (39, 57, 76)

# Texto
TEXT = (240, 246, 252)
TEXT_MUTED = (155, 174, 194)
TEXT_DIM = (111, 132, 153)

# Colores semánticos
PRIMARY = (56, 189, 248)
PRIMARY_DARK = (14, 116, 144)
SUCCESS = (74, 222, 128)
SUCCESS_DARK = (21, 128, 61)
WARNING = (250, 204, 21)
WARNING_DARK = (161, 98, 7)
DANGER = (251, 113, 133)
DANGER_DARK = (159, 18, 57)
PURPLE = (167, 139, 250)

# Arena
ARENA_BACKGROUND = (12, 25, 38)
ARENA_GRID = (31, 54, 72)
ARENA_CIRCLE = (24, 69, 92)
ARENA_CIRCLE_EDGE = (103, 232, 249)
MAP_EDGE = (73, 101, 126)

# Entidades
PLAYER_SELF = SUCCESS
PLAYER_OTHER = PRIMARY
PLAYER_CARRIER = (251, 146, 60)
PLAYER_OUTLINE = (226, 232, 240)
FLAG = WARNING
FLAG_POLE = (203, 213, 225)
SHADOW = (0, 0, 0, 90)

PHASE_COLORS = {
    "connecting": TEXT_DIM,
    "lobby": PRIMARY,
    "countdown": WARNING,
    "playing": SUCCESS,
    "finished": PURPLE,
    "disconnected": DANGER,
}

PHASE_LABELS = {
    "connecting": "CONECTANDO",
    "lobby": "LOBBY",
    "countdown": "CUENTA REGRESIVA",
    "playing": "EN PARTIDA",
    "finished": "FINALIZADA",
    "disconnected": "DESCONECTADO",
}
