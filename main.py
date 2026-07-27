"""Punto de entrada de Captura la Bandera."""

import argparse
import socket

from common.constants import DEFAULT_TCP_PORT, MAX_NAME_LENGTH
from common.discovery import discover_servers


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Captura la Bandera multijugador")
    modes = root.add_subparsers(dest="mode", required=True)

    server = modes.add_parser("server")
    server.add_argument("--host", default="0.0.0.0")
    server.add_argument("--port", type=int, default=DEFAULT_TCP_PORT)
    server.add_argument("--name", default="Servidor Python Arcade")

    client = modes.add_parser("client")
    client.add_argument("--name", default=socket.gethostname()[:MAX_NAME_LENGTH])
    client.add_argument("--host")
    client.add_argument("--port", type=int, default=DEFAULT_TCP_PORT)
    client.add_argument("--no-discovery", action="store_true")
    return root


def choose_server() -> tuple[str, int] | None:
    print("Buscando servidores por UDP...")
    servers = discover_servers(1.8)
    if not servers:
        return None

    for i, server in enumerate(servers, 1):
        print(f"{i}. {server.get('name', 'Servidor')} - {server['ip']}:{server['tcp_port']}")

    option = input("Número [1]: ").strip() or "1"
    try:
        server = servers[int(option) - 1]
        return server["ip"], int(server["tcp_port"])
    except (ValueError, IndexError):
        print("Opción inválida; se usará el primero.")
        server = servers[0]
        return server["ip"], int(server["tcp_port"])


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

    host, port = args.host, args.port
    if not args.no_discovery and host is None:
        selected = choose_server()
        if selected:
            host, port = selected
    if host is None:
        host = input("IP del servidor [127.0.0.1]: ").strip() or "127.0.0.1"

    client = CTFClient(host, port, name)
    try:
        client.connect()
    except OSError as error:
        raise SystemExit(f"No se pudo conectar a {host}:{port}: {error}") from error

    print(f"Conectado a {host}:{port} como {name}")
    run_client_window(client)


def main() -> None:
    args = parser().parse_args()
    run_server(args) if args.mode == "server" else run_client(args)


if __name__ == "__main__":
    main()
