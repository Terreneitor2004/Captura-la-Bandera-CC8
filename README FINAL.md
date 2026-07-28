# Captura la Bandera Multijugador — Python + Arcade

Proyecto **Captura la Bandera multijugador**, desarrollado en Python con sockets TCP/UDP y una interfaz gráfica 2D construida con Arcade.

La aplicación puede funcionar como **servidor** o como **cliente**. Incluye un menú gráfico inicial, descubrimiento de servidores mediante broadcast, conexión manual por IP, lobby, cuenta regresiva, movimiento sincronizado, captura y robo de bandera, condición de victoria, registro de conexiones y compatibilidad con otros proyectos que implementan el protocolo CTF v1.

## Información general

- **Lenguaje:** Python
- **Conexión:** sockets básicos de Python
- **Interfaz gráfica:** Arcade
- **Protocolo:** JSON codificado en UTF-8
- **Transporte de la partida:** TCP
- **Descubrimiento de servidores:** UDP, puerto fijo `8888`
- **Puerto TCP predeterminado:** `8889`
- **Cantidad máxima de jugadores:** `100`
- **Autoridad del juego:** servidor
- **Curso:** CC8 2026

---

## Objetivo del juego

Cada jugador aparece en una posición aleatoria fuera del círculo central. La bandera comienza en el centro del mapa.

Para ganar, un jugador debe:

1. Entrar al círculo central.
2. Acercarse a la bandera.
3. Presionar `E` para tomarla.
4. Evitar que otro jugador se la robe.
5. Salir completamente del círculo mientras todavía lleva la bandera.

Cuando un jugador cumple la condición de victoria, el servidor envía `game_over`, muestra al ganador y finaliza la ronda para todos los clientes.

---

## Funcionalidades implementadas

### Menú principal

La versión final se ejecuta con un solo comando:

```powershell
python main.py
```

El menú permite elegir entre:

- **Crear una partida como servidor.**
- **Unirse a una partida como cliente.**

El cliente y el servidor se abren como procesos independientes para evitar conflictos entre ventanas de Arcade y el contexto gráfico de OpenGL.

### Servidor

El modo servidor incluye:

- Nombre personalizable del servidor.
- Puerto TCP configurable.
- Descubrimiento UDP en el puerto `8888`.
- Soporte para hasta 100 conexiones.
- Ventana gráfica para observar a todos los jugadores.
- Registro visual y en terminal de conexiones y desconexiones.
- Lista de jugadores conectados con sus nombres reales.
- Inicio manual de la partida mediante botón o barra espaciadora.
- Cuenta regresiva de 5 segundos.
- Cálculo oficial de posiciones, bandera, robo y victoria.
- Regreso automático al lobby después de finalizar una ronda.

La computadora que actúa como servidor **solo observa la partida**. Para jugar desde esa misma computadora, también debe abrirse un cliente.

### Cliente

El modo cliente incluye:

- Nombre del jugador de hasta 20 caracteres.
- Búsqueda de servidores activos mediante broadcast UDP.
- Lista de servidores encontrados.
- Selección del servidor al cual se desea entrar.
- Conexión manual mediante IP
- Consulta directa por UDP `8888` cuando se conoce la IP, pero no el puerto TCP.
- Interfaz con mapa, bandera, jugadores, nombres y fase actual.
- Compatibilidad con servidores que envían algunas variantes de estructura JSON.
- Conservación de los nombres recibidos en el lobby durante toda la partida.
- Mensajes visuales para conexión, errores, countdown y ganador.

### Interfaz gráfica

La interfaz final incluye:

- Diseño oscuro tipo panel de videojuego.
- Arena cuadrada y centrada.
- Cuadrícula del mapa.
- Círculo central y bandera.
- Panel lateral de jugadores.
- Estado de conexión y fase de la partida.
- Nombres sobre cada jugador.
- Jugador local resaltado.
- Portador de la bandera identificado visualmente.
- Pantalla de cuenta regresiva.
- Pantalla de fin de partida.
- Registro de eventos en la ventana del servidor.

### Movimiento corregido

El servidor normaliza el vector de movimiento con el objetivo de mantener la misma velocidad en todas las direcciones.

Esto evita que:

- El movimiento horizontal sea más rápido que el vertical.
- El movimiento diagonal tenga ventaja.
- La escala visual de un eje sea diferente a la del otro.

### Compatibilidad del protocolo

El proyecto implementa el flujo principal de CTF v1:

```text
discover -> server_info -> join -> welcome -> lobby
-> countdown -> start -> state -> game_over
```

También se corrigieron reglas importantes de compatibilidad:

- `state` solo se envía durante la fase `playing`.
- `start` se envía antes del primer `state`.
- No se envía otro `state` después de `game_over`.
- `server_info.state` solo anuncia `lobby` o `playing`.
- Las constantes de `welcome.config` se envían como enteros JSON.
- El segundo intento de interacción con `E` se ignora de forma segura.
- Cada mensaje TCP termina con `\n`.
- Los mensajes se reconstruyen mediante un buffer, aunque lleguen divididos o unidos.

---

## Requisitos

Antes de ejecutar el proyecto se necesita:

- Python 3 instalado.
- `pip` disponible.
- Acceso de red local o una VPN virtual, por ejemplo Radmin VPN, para jugar desde computadoras diferentes.

La única dependencia externa del proyecto es Arcade:

```text
arcade>=3.0,<4.0
```

---

## Instalación

### Opción rápida

Abre PowerShell dentro de la carpeta del proyecto e instala las dependencias una sola vez:

```powershell
python -m pip install -r requirements.txt
```

Después de esa instalación, la ejecución normal será únicamente:

```powershell
python main.py
```
---

## Ejecución principal

Desde la carpeta raíz del proyecto:

```powershell
python main.py
```

Se abrirá el menú principal.

### Crear un servidor desde el menú

1. Selecciona **SERVIDOR**.
2. Escribe el nombre del servidor.
3. Escribe el puerto TCP o conserva `8889`.
4. Presiona **INICIAR SERVIDOR**.
5. Espera a que los jugadores se conecten.
6. Presiona **INICIAR PARTIDA** en la ventana del servidor o usa la barra espaciadora.

### Entrar como cliente desde el menú

1. Selecciona **CLIENTE**.
2. Escribe el nombre del jugador.
3. Presiona **BUSCAR / ACTUALIZAR**.
4. Selecciona un servidor de la lista.
5. Presiona **UNIRSE AL SELECCIONADO**.

También se puede escribir manualmente:

- La IP del servidor.
- El puerto TCP, cuando se conoce.

Si se escribe una IP y se deja vacío el puerto, el cliente consultará esa IP mediante UDP `8888` para obtener el puerto TCP anunciado.

---
## Ejecución por terminal

El menú es la forma principal, pero los modos directos todavía están disponibles.

### Servidor

```powershell
python main.py server
```
---

## Controles

| Tecla | Acción |
|---|---|
| `W` o flecha arriba | Moverse hacia arriba |
| `S` o flecha abajo | Moverse hacia abajo |
| `A` o flecha izquierda | Moverse hacia la izquierda |
| `D` o flecha derecha | Moverse hacia la derecha |
| `E` | Tomar o robar la bandera |
| `Espacio` en el servidor | Iniciar la partida |
| `Esc` en el menú | Regresar o cerrar |

La tecla `E` tiene una pequeña protección contra repetición para evitar enviar varias interacciones por mantenerla presionada.

---

## Constantes del juego

Las constantes se encuentran en:

```text
common/constants.py
```

| Constante | Valor final | Descripción |
|---|---:|---|
| `PROTOCOL_VERSION` | `1` | Versión del protocolo |
| `DISCOVERY_PORT` | `8888` | Puerto UDP fijo |
| `DEFAULT_TCP_PORT` | `8889` | Puerto TCP predeterminado |
| `MAX_PLAYERS` | `100` | Máximo de jugadores |
| `MAX_NAME_LENGTH` | `20` | Longitud máxima del nombre |
| `MAP_SIZE` | `1000` | Tamaño lógico del mapa |
| `CIRCLE_RADIUS` | `300` | Radio del círculo central |
| `PLAYER_RADIUS` | `15` | Radio del jugador |
| `INTERACT_RADIUS` | `40` | Distancia máxima para interactuar |
| `PLAYER_SPEED` | `200` | Velocidad lógica por segundo |
| `TICK_RATE` | `20` | Estados enviados por segundo |
| `COUNTDOWN_SECONDS` | `5` | Duración de la cuenta regresiva |
| `MIN_PLAYERS_TO_START` | `1` | Mínimo actual para iniciar |

Para exigir al menos dos jugadores:

```python
MIN_PLAYERS_TO_START = 2
```

---

## Arquitectura del proyecto

```text
CTF/
├── main.py
├── requirements.txt
│
├── launcher/
│   ├── app.py
│   ├── interface.py
│   └── widgets.py
│
├── common/
│   ├── constants.py
│   ├── discovery.py
│   ├── protocol.py
│   └── rendering.py
│
├── server/
│   ├── app.py
│   ├── interface.py
│   ├── network.py
│   └── game_state.py
│
├── client/
│   ├── app.py
│   ├── interface.py
│   ├── network.py
│   └── message_adapter.py
│
├── ui/
│   ├── theme.py
│   ├── layout.py
│   ├── components.py
│   └── game_scene.py
│
└── tests/
    ├── test_discovery.py
    ├── test_game_state.py
    ├── test_launcher_entry.py
    ├── test_layout.py
    ├── test_message_adapter.py
    ├── test_protocol.py
    └── test_strict_protocol.py
```

### Responsabilidad de cada módulo

- `main.py`: punto de entrada y modos de ejecución.
- `launcher/`: menú gráfico, búsqueda y selección de servidores.
- `common/protocol.py`: codificación JSON, framing TCP y validación básica.
- `common/discovery.py`: broadcast UDP y consulta directa de servidores.
- `server/network.py`: conexiones TCP/UDP, sesiones y difusión de mensajes.
- `server/game_state.py`: reglas autoritativas de movimiento, bandera y victoria.
- `client/network.py`: conexión TCP y envío de acciones.
- `client/message_adapter.py`: adaptación de mensajes de otros proyectos.
- `ui/`: componentes gráficos reutilizables.
- `tests/`: pruebas automáticas del protocolo y de las reglas.

---

## Mensajes del protocolo

### UDP

```text
discover
server_info
```

Ejemplo de búsqueda:

```json
{"type":"discover","v":1}
```

Ejemplo de respuesta:

```json
{"type":"server_info","v":1,"name":"Servidor Python Arcade","tcp_port":8889,"state":"lobby","players":1}
```

### Cliente a servidor por TCP

```text
join
input
interact
```

### Servidor a cliente por TCP

```text
welcome
lobby
countdown
start
state
game_over
error
```

Cada mensaje TCP se envía como un JSON completo seguido por un salto de línea:

```text
{"type":"interact"}\n
```

---

## Pruebas automáticas

Ejecuta:

```powershell
python -m unittest discover -s tests -v
```

La versión final contiene **26 pruebas automáticas** para verificar:

- Descubrimiento UDP.
- Validación de `server_info`.
- Mensajes TCP divididos o unidos.
- Codificación y delimitación JSON.
- Spawn fuera del círculo.
- Captura de bandera.
- Interacción repetida segura.
- Inicio manual del servidor.
- Velocidad horizontal y vertical equivalente.
- Normalización del movimiento diagonal.
- Escala gráfica uniforme.
- Adaptación de jugadores como lista o diccionario.
- Conservación de nombres del lobby.
- Compatibilidad de `carrier_id` con `owner`.
- Envío de `start` antes de `state`.
- Ausencia de `state` después de `game_over`.
- Constantes de `welcome` como enteros.

---

## Problemas comunes

### `ModuleNotFoundError: No module named 'arcade'`

Instala las dependencias con el mismo Python que usas para ejecutar:

```powershell
python -m pip install -r requirements.txt
```

### `Timed out`

Verifica:

- Que el servidor esté abierto.
- Que la IP sea correcta.
- Que el puerto TCP sea el real.
- Que ambos estén en la misma red de Radmin.
- Que el firewall permita TCP y UDP.

### El servidor no aparece en la búsqueda

Usa conexión manual. El broadcast puede ser bloqueado por una VPN, un router o el firewall.

### La ventana se cierra al conectar

Revisa la terminal. La versión final abre el cliente y el servidor en procesos separados; cualquier error real aparecerá como un `Traceback` en PowerShell.

### El servidor observa, pero no puede jugar

Es el comportamiento requerido. Abre otro cliente en la misma computadora y conecta a:

```text
127.0.0.1
```

---

## Limitaciones conocidas

- El broadcast no está garantizado en todas las redes o VPN.
- La reconexión durante una partida no forma parte de esta versión.
- No hay migración automática de host si el servidor se desconecta.
- La compatibilidad con otros proyectos depende de que respeten los mensajes obligatorios del protocolo CTF v1.
- El servidor no controla un jugador directamente; únicamente administra y observa.

---

## Documentación adicional

El repositorio incluye documentos sobre las principales etapas y correcciones:

- `BROADCAST_SERVIDORES.md`
- `CAMBIOS_INTERFAZ.md`
- `COMPATIBILIDAD_CSHARP.md`
- `CONEXION_RADMIN.md`
- `CORRECCION_CAMBIO_VENTANA.md`
- `CORRECCION_INTERACT.md`
- `CORRECCION_MENU.md`
- `MENU_INICIO.md`
- `NOMBRES_JUGADORES.md`
- `REDUCCION_CODIGO.md`

El historial completo del desarrollo debe mantenerse mediante commits de Git y una bitácora que relacione cada versión con su commit correspondiente.

---

## Uso de inteligencia artificial

Durante el desarrollo se utilizó inteligencia artificial como apoyo para:

- Diseñar la estructura inicial del proyecto.
- Implementar sockets TCP y UDP.
- Crear el protocolo JSON con framing por salto de línea.
- Separar la interfaz gráfica de la lógica.
- Detectar incompatibilidades entre implementaciones.
- Corregir errores de Arcade y del cambio de ventanas.

Los prompts utilizados, los archivos afectados y la validación de cada cambio deben documentarse en el archivo correspondiente de uso de IA.

---