"""Punto de entrada del proyecto Captura la Bandera."""

from __future__ import annotations

import argparse
import socket
import sys

from common.constants import DEFAULT_TCP_PORT, MAX_NAME_LENGTH
from common.discovery import discover_servers


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Captura la Bandera multijugador")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    server_parser = subparsers.add_parser("server", help="Iniciar como servidor")
    server_parser.add_argument("--host", default="0.0.0.0")
    server_parser.add_argument("--port", type=int, default=DEFAULT_TCP_PORT)
    server_parser.add_argument("--name", default="Servidor Python Arcade")

    client_parser = subparsers.add_parser("client", help="Iniciar como cliente")
    client_parser.add_argument("--name", default=socket.gethostname()[:MAX_NAME_LENGTH])
    client_parser.add_argument("--host", help="IP manual del servidor")
    client_parser.add_argument("--port", type=int, default=DEFAULT_TCP_PORT)
    client_parser.add_argument(
        "--no-discovery",
        action="store_true",
        help="No buscar servidores y usar --host directamente",
    )

    return parser


def choose_server() -> tuple[str, int] | None:
    print("Buscando servidores por UDP en el puerto 8888...")
    servers = discover_servers(timeout=1.8)

    if not servers:
        print("No se encontraron servidores automáticamente.")
        return None

    print("\nServidores encontrados:")
    for index, server in enumerate(servers, start=1):
        print(
            f"  {index}. {server.get('name', 'Sin nombre')} "
            f"- {server['ip']}:{server['tcp_port']} "
            f"- estado={server.get('state')} jugadores={server.get('players')}"
        )

    while True:
        option = input("Elige un número o presiona Enter para usar el primero: ").strip()
        if option == "":
            selected = servers[0]
            return selected["ip"], int(selected["tcp_port"])

        try:
            selected = servers[int(option) - 1]
            return selected["ip"], int(selected["tcp_port"])
        except (ValueError, IndexError):
            print("Opción inválida.")


def run_server(args: argparse.Namespace) -> None:
    from server.app import run_server_window
    from server.network import CTFServer

    server = CTFServer(host=args.host, tcp_port=args.port, name=args.name)
    try:
        server.start()
    except OSError as error:
        print(f"No se pudo iniciar el servidor: {error}")
        print("Comprueba que los puertos 8888 UDP y 8889 TCP no estén ocupados.")
        raise SystemExit(1) from error

    print(f"Servidor iniciado. TCP={args.port}, UDP=8888")
    run_server_window(server)


def run_client(args: argparse.Namespace) -> None:
    from client.app import run_client_window
    from client.network import CTFClient

    name = args.name.strip()
    if not name or len(name) > MAX_NAME_LENGTH or "\n" in name:
        print(f"El nombre debe tener entre 1 y {MAX_NAME_LENGTH} caracteres.")
        raise SystemExit(1)

    host = args.host
    port = args.port

    if not args.no_discovery and host is None:
        selected = choose_server()
        if selected is not None:
            host, port = selected

    if host is None:
        host = input("Escribe la IP manual del servidor [127.0.0.1]: ").strip()
        host = host or "127.0.0.1"
        port_text = input(f"Puerto TCP [{port}]: ").strip()
        if port_text:
            try:
                port = int(port_text)
            except ValueError:
                print("El puerto debe ser un número.")
                raise SystemExit(1)

    client = CTFClient(host=host, port=port, name=name)
    try:
        client.connect()
    except OSError as error:
        print(f"No se pudo conectar a {host}:{port}: {error}")
        raise SystemExit(1) from error

    print(f"Conectado a {host}:{port} como {name}")
    run_client_window(client)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.mode == "server":
        run_server(args)
    elif args.mode == "client":
        run_client(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
