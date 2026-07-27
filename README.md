# Captura la Bandera — Python + sockets + Arcade

Proyecto completo de prueba para ejecutar como servidor o cliente.

## 1. Instalar

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

En Linux/macOS la activación es:

```bash
source .venv/bin/activate
```

## 2. Ejecutar el servidor

```bash
python main.py server
```

## 3. Ejecutar un cliente

En otra terminal:

```bash
python main.py client --name Fabian
```

El cliente busca el servidor mediante UDP. Para conectarse manualmente en la misma computadora:

```bash
python main.py client --name Fabian --host 127.0.0.1 --port 8889 --no-discovery
```

Puedes abrir más terminales y crear más clientes:

```bash
python main.py client --name Ana --host 127.0.0.1 --port 8889 --no-discovery
```

## Controles

- WASD o flechas: mover.
- E: tomar o robar la bandera.

## Reglas implementadas

- La bandera inicia en `(500, 500)`.
- Los jugadores aparecen aleatoriamente fuera del círculo.
- El servidor calcula todas las posiciones.
- El cliente solo envía dirección e interacción.
- La bandera se captura o roba a una distancia máxima de 40 unidades.
- Gana quien tenga la bandera y salga completamente del círculo.
- TCP usa JSON UTF-8 terminado en `\n`.
- UDP 8888 se usa solo para descubrimiento.

## Pruebas

```bash
python -m unittest discover -s tests -v
```

## Nota para pruebas rápidas

`MIN_PLAYERS_TO_START` está en `1` para poder probar con un solo cliente. Está en `common/constants.py`. Cámbialo a `2` cuando quieras exigir dos jugadores.
