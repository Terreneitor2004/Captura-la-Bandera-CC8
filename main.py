"""Punto de entrada de Captura la Bandera."""

import argparse
import socket

from common.constants import DEFAULT_TCP_PORT, MAX_NAME_LENGTH
from common.discovery import discover_server_at, discover_servers


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Captura la Bandera multijugador")
    modes = root.add_subparsers(dest="mode", required=False)

    server = modes.add_parser("server")
    server.add_argument("--host", default="0.0.0.0")
    server.add_argument("--port", type=int, default=DEFAULT_TCP_PORT)
    server.add_argument("--name", default="Servidor Python Arcade")

    client = modes.add_parser("client")
    client.add_argument("--name", default=socket.gethostname()[:MAX_NAME_LENGTH])
    client.add_argument("--host", help="IP del servidor, por ejemplo 26.x.x.x")
    client.add_argument("--port", type=int, help="Puerto TCP real anunciado por el servidor")
    client.add_argument(
        "--no-discovery",
        action="store_true",
        help="Conectar directamente; requiere --host y --port",
    )
    return root


def choose_server() -> tuple[str, int] | None:
    print("Buscando servidores por UDP 8888...")
    servers = discover_servers()
    if not servers:
        return None

    for i, server in enumerate(servers, 1):
        print(
            f"{i}. {server.get('name', 'Servidor')} - "
            f"{server['ip']}:{server['tcp_port']} "
            f"[{server.get('state', '?')}, {server.get('players', 0)} jugador(es)]"
        )

    option = input("Número [1]: ").strip() or "1"
    try:
        server = servers[int(option) - 1]
    except (ValueError, IndexError):
        print("Opción inválida; se usará el primero.")
        server = servers[0]
    return server["ip"], int(server["tcp_port"])


def resolve_server(args: argparse.Namespace) -> tuple[str, int]:
    """Obtiene IP y puerto sin asumir que todos usan TCP 8889."""
    if args.no_discovery:
        if not args.host or args.port is None:
            raise SystemExit("Con --no-discovery debes indicar --host y --port.")
        return args.host, args.port

    # IP conocida en Radmin: preguntar directamente por UDP 8888.
    if args.host:
        if args.port is not None:
            return args.host, args.port

        print(f"Consultando {args.host}:8888 para conocer su puerto TCP...")
        info = discover_server_at(args.host)
        if not info:
            raise SystemExit(
                "El servidor no respondió al descubrimiento UDP 8888. "
                "Pide a tu compañero su puerto TCP real y usa: "
                "--host IP --port PUERTO --no-discovery"
            )
        print(
            f"Servidor encontrado: {info.get('name', 'Servidor')} | "
            f"TCP {info['tcp_port']} | estado {info.get('state')}"
        )
        return args.host, int(info["tcp_port"])

    selected = choose_server()
    if selected:
        return selected

    host = input("No hubo broadcast. IP Radmin del servidor: ").strip()
    if not host:
        raise SystemExit("Debes indicar una IP de servidor.")

    info = discover_server_at(host)
    if info:
        return host, int(info["tcp_port"])

    raise SystemExit(
        "No respondió por UDP 8888. Pide el puerto TCP real al servidor y ejecuta: "
        f"python main.py client --name NOMBRE --host {host} --port PUERTO --no-discovery"
    )


def run_server(args: argparse.Namespace) -> None:
    from server.app import run_server_window
    from server.network import CTFServer

    server = CTFServer(args.host, args.port, args.name)
    try:
        server.start()
    except OSError as error:
        raise SystemExit(f"No se pudo iniciar el servidor: {error}") from error
    run_server_window(server)


def run_client(args: argparse.Namespace) -> None:
    from client.app import run_client_window
    from client.network import CTFClient

    name = args.name.strip()
    if not name or len(name) > MAX_NAME_LENGTH or "\n" in name:
        raise SystemExit(f"El nombre debe tener entre 1 y {MAX_NAME_LENGTH} caracteres")

    host, port = resolve_server(args)
    client = CTFClient(host, port, name)
    try:
        client.connect()
    except (TimeoutError, socket.timeout):
        raise SystemExit(
            f"Timeout TCP en {host}:{port}. Verifica que el servidor esté abierto, "
            "que ese sea su puerto TCP real y que el firewall permita la conexión."
        )
    except OSError as error:
        raise SystemExit(f"No se pudo conectar a {host}:{port}: {error}") from error

    print(f"Conectado a {host}:{port} como {name}")
    run_client_window(client)


def main() -> None:
    args = parser().parse_args()
    if args.mode is None:
        from launcher.app import run_launcher

        run_launcher()
    elif args.mode == "server":
        run_server(args)
    else:
        run_client(args)


if __name__ == "__main__":
    main()
