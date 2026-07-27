# Captura la Bandera — Python + Arcade

Proyecto multijugador compatible con el protocolo CTF de la clase:

- TCP para toda la partida.
- UDP `8888` para descubrir servidores.
- Mensajes JSON UTF-8 separados por `\n` en TCP.
- Servidor autoritativo.
- Cliente gráfico con Arcade.
- Inicio manual desde la ventana del servidor.
- Hasta 100 conexiones.

## Mejoras de esta versión

- Nueva interfaz oscura tipo panel de juego.
- Arena cuadrada y centrada aunque la ventana cambie de tamaño.
- Panel lateral con fase, jugadores, controles y estado de conexión.
- Servidor con botón de inicio, lobby y eventos de conexión.
- Bandera y jugadores con mejor representación visual.
- Movimiento normalizado para que horizontal, vertical y diagonal recorran la misma distancia por segundo.
- Uso de objetos `arcade.Text` para evitar la advertencia de rendimiento de `draw_text`.

## Organización de la interfaz

```text
ui/
├── theme.py          # Colores y estilo
├── layout.py         # Distribución y escala uniforme del mapa
├── components.py     # Paneles, botones, textos y listas
└── game_scene.py     # Dibujo del mapa, bandera y jugadores

client/
├── app.py            # Eventos, teclado y mensajes del cliente
└── interface.py      # Interfaz del cliente

server/
├── app.py            # Eventos de la ventana del servidor
└── interface.py      # Panel visual del servidor
```

## Instalar

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

## Ejecutar servidor

```powershell
python main.py server
```

Cuando haya al menos un jugador conectado, el host puede iniciar con:

- Clic en **INICIAR PARTIDA**.
- Barra espaciadora.

## Ejecutar cliente local

```powershell
python main.py client --name Fabian --host 127.0.0.1 --port 8889 --no-discovery
```

## Ejecutar cliente con Radmin VPN

```powershell
python main.py client --name Fabian --host 26.X.X.X --port 8889 --no-discovery
```

La IP debe ser la IP de Radmin de la computadora que ejecuta el servidor.

## Controles

- `WASD` o flechas: mover al jugador.
- `E`: tomar o robar la bandera.

## Pruebas

```powershell
python -m unittest discover -s tests -v
```

La suite incluye pruebas de:

- Protocolo TCP/UDP.
- Captura de bandera.
- Inicio manual.
- Igualdad de velocidad horizontal y vertical.
- Normalización de movimiento diagonal.
- Escala visual uniforme en ambos ejes.

`MIN_PLAYERS_TO_START` se encuentra en `common/constants.py` y actualmente vale `1`.
