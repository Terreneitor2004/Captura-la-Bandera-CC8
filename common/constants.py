"""Constantes compartidas por el cliente y el servidor CTF."""

PROTOCOL_VERSION = 1

# Red
DISCOVERY_PORT = 8888
DEFAULT_TCP_PORT = 8889
RECV_SIZE = 4096
MAX_PLAYERS = 100
MAX_NAME_LENGTH = 20
MAX_MESSAGE_SIZE = 64 * 1024

# Fases de la partida
STATE_LOBBY = "lobby"
STATE_COUNTDOWN = "countdown"
STATE_PLAYING = "playing"
STATE_FINISHED = "finished"

# Juego (valores sugeridos por el estándar)
MAP_SIZE = 1000.0
CIRCLE_RADIUS = 300.0
PLAYER_RADIUS = 15.0
INTERACT_RADIUS = 40.0
PLAYER_SPEED = 200.0
TICK_RATE = 20
COUNTDOWN_SECONDS = 5

# Para probar de inmediato con una sola computadora.
# Para exigir al menos dos personas, cambia este valor a 2.
MIN_PLAYERS_TO_START = 1

MAP_CENTER_X = MAP_SIZE / 2
MAP_CENTER_Y = MAP_SIZE / 2
FLAG_START_X = MAP_CENTER_X
FLAG_START_Y = MAP_CENTER_Y

VALID_DIRECTION_VALUES = {-1, 0, 1}
