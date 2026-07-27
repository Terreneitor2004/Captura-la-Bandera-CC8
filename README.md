# Captura la Bandera — Python + Arcade

Proyecto multijugador con:

- TCP para la partida.
- UDP `8888` para descubrir servidores.
- Mensajes JSON UTF-8 separados por `\n` en TCP.
- Servidor autoritativo.
- Cliente gráfico con Arcade.
- Inicio manual de la partida desde la ventana del servidor.

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

Cuando un cliente se conecta, la terminal del servidor muestra eventos como:

```text
[CONEXIÓN] Nueva conexión entrante...
[LOBBY] Jugador 'Fabian' se unió...
[PROTOCOLO] Mensaje 'welcome' enviado...
```

La ventana del servidor también muestra los últimos eventos.

### Iniciar la partida

Cuando haya al menos un jugador conectado, el host puede:

- Hacer clic en **INICIAR PARTIDA**.
- Presionar la barra espaciadora.

Después se envía el countdown de 5 segundos y comienza la partida para todos.

## Ejecutar cliente local

```powershell
python main.py client --name Fabian --host 127.0.0.1 --port 8889 --no-discovery
```

## Ejecutar cliente con Radmin VPN

Usa la IP de Radmin del amigo que ejecuta el servidor:

```powershell
python main.py client --name Fabian --host 26.X.X.X --port 8889 --no-discovery
```

## Controles del cliente

- `WASD` o flechas: movimiento.
- `E`: tomar o robar la bandera.

## Pruebas

```powershell
python -m unittest discover -s tests -v
```

`MIN_PLAYERS_TO_START` está en `1` para permitir pruebas con un solo cliente. Puedes cambiarlo en `common/constants.py`.
