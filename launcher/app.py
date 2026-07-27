"""Lógica del menú gráfico inicial."""

from __future__ import annotations

import queue
import socket
import threading
from typing import Any, Callable

import arcade

from common.constants import DEFAULT_TCP_PORT, MAX_NAME_LENGTH
from common.discovery import discover_server_at, discover_servers
from launcher.interface import LauncherInterface
from launcher.widgets import TextField
from ui import theme

WINDOW_WIDTH = 1040
WINDOW_HEIGHT = 710
WINDOW_TITLE = "CTF - Menú principal"


class LauncherWindow(arcade.Window):
    def __init__(self) -> None:
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE, resizable=True)
        arcade.set_background_color(theme.BACKGROUND)
        self.interface = LauncherInterface()
        self.screen = "home"
        self.fields = {
            "server_name": TextField("Nombre del servidor", "Servidor Python Arcade", max_length=40),
            "server_port": TextField("Puerto TCP", str(DEFAULT_TCP_PORT), "8889", 5, numeric=True),
            "client_name": TextField(
                "Nombre del jugador",
                socket.gethostname()[:MAX_NAME_LENGTH],
                "Jugador",
                MAX_NAME_LENGTH,
            ),
            "client_host": TextField("IP del servidor", "", "Ejemplo: 26.59.6.162", 45),
            "client_port": TextField("Puerto TCP (opcional)", "", "Automático", 5, numeric=True),
        }
        self.active_field: str | None = None
        self.hovered: str | None = None
        self.mouse_x = -1.0
        self.mouse_y = -1.0
        self.bounds: dict[str, Any] = {}
        self.servers: list[dict[str, Any]] = []
        self.status = ""
        self.error = ""
        self.busy = False
        self.results: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.elapsed = 0.0

    def on_draw(self) -> None:
        self.clear()
        self.bounds = self.interface.draw(
            self.width,
            self.height,
            screen=self.screen,
            fields=self.fields,
            servers=self.servers,
            hovered=self.hovered,
            busy=self.busy,
            status=self.status,
            error=self.error,
            cursor_visible=int(self.elapsed * 2) % 2 == 0,
        )

    def on_update(self, delta_time: float) -> None:
        self.elapsed += delta_time
        while True:
            try:
                kind, value = self.results.get_nowait()
            except queue.Empty:
                break
            self.busy = False
            if kind == "error":
                self.status = ""
                self.error = str(value)
            elif kind == "servers":
                self.servers = value
                self.status = f"Se encontraron {len(value)} servidor(es)." if value else "No se encontraron servidores."
                self.error = ""
            elif kind == "server":
                self._open_server(value)
                return
            elif kind == "client":
                self._open_client(value)
                return

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        del dx, dy
        self.mouse_x, self.mouse_y = x, y
        self.hovered = next(
            (key for key, rect in self.bounds.items() if key != "card" and rect.contains(x, y)),
            None,
        )

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int) -> None:
        del button, modifiers
        if self.busy:
            return

        clicked = next(
            (key for key, rect in self.bounds.items() if key != "card" and rect.contains(x, y)),
            None,
        )
        field_names = self._field_order()
        if clicked in field_names:
            self._activate_field(clicked)
            return
        self._activate_field(None)

        if clicked == "choose_server":
            self._change_screen("server")
        elif clicked == "choose_client":
            self._change_screen("client")
        elif clicked == "back":
            self._change_screen("home")
        elif clicked == "start_server":
            self._start_server()
        elif clicked == "connect":
            self._connect_from_form()
        elif clicked == "search":
            self._search_servers()
        elif clicked and clicked.startswith("server_"):
            try:
                index = int(clicked.split("_", 1)[1])
                self._connect_to_server(self.servers[index])
            except (ValueError, IndexError):
                pass

    def on_text(self, text: str) -> None:
        if self.active_field:
            self.fields[self.active_field].insert(text)

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        del modifiers
        if symbol == arcade.key.ESCAPE:
            if self.screen == "home":
                self.close()
            elif not self.busy:
                self._change_screen("home")
            return
        if self.busy:
            return
        if symbol == arcade.key.BACKSPACE and self.active_field:
            self.fields[self.active_field].backspace()
        elif symbol == arcade.key.TAB:
            self._cycle_field()
        elif symbol in (arcade.key.ENTER, arcade.key.RETURN):
            if self.screen == "server":
                self._start_server()
            elif self.screen == "client":
                self._connect_from_form()

    def _field_order(self) -> list[str]:
        if self.screen == "server":
            return ["server_name", "server_port"]
        if self.screen == "client":
            return ["client_name", "client_host", "client_port"]
        return []

    def _activate_field(self, name: str | None) -> None:
        self.active_field = name
        for key, field in self.fields.items():
            field.active = key == name

    def _cycle_field(self) -> None:
        order = self._field_order()
        if not order:
            return
        if self.active_field not in order:
            self._activate_field(order[0])
        else:
            self._activate_field(order[(order.index(self.active_field) + 1) % len(order)])

    def _change_screen(self, screen: str) -> None:
        self.screen = screen
        self.status = ""
        self.error = ""
        self.hovered = None
        self._activate_field(None)

    def _start_server(self) -> None:
        name = self.fields["server_name"].value.strip()
        port_text = self.fields["server_port"].value.strip()
        if not name:
            self.error = "Escribe un nombre para el servidor."
            return
        try:
            port = int(port_text)
        except ValueError:
            self.error = "El puerto TCP debe ser un número."
            return
        if not 1 <= port <= 65535:
            self.error = "El puerto TCP debe estar entre 1 y 65535."
            return

        def job() -> Any:
            from server.network import CTFServer

            server = CTFServer("0.0.0.0", port, name)
            server.start()
            return server

        self._async("server", "Iniciando servidor...", job)

    def _connect_from_form(self) -> None:
        name = self.fields["client_name"].value.strip()
        host = self.fields["client_host"].value.strip()
        port_text = self.fields["client_port"].value.strip()
        if not name or len(name) > MAX_NAME_LENGTH or "\n" in name:
            self.error = f"El nombre debe tener entre 1 y {MAX_NAME_LENGTH} caracteres."
            return
        if not host:
            self.error = "Escribe la IP del servidor o usa BUSCAR SERVIDORES."
            return
        if port_text:
            try:
                port = int(port_text)
            except ValueError:
                self.error = "El puerto TCP debe ser un número."
                return
            if not 1 <= port <= 65535:
                self.error = "El puerto TCP debe estar entre 1 y 65535."
                return
            self._connect(name, host, port)
            return

        def resolve_and_connect() -> Any:
            info = discover_server_at(host)
            if not info:
                raise ConnectionError(
                    "El servidor no respondió por UDP 8888. Escribe su puerto TCP manualmente."
                )
            return self._build_client(name, host, int(info["tcp_port"]))

        self._async("client", f"Consultando {host}:8888...", resolve_and_connect)

    def _search_servers(self) -> None:
        self._async("servers", "Buscando servidores por UDP 8888...", discover_servers)

    def _connect_to_server(self, server: dict[str, Any]) -> None:
        name = self.fields["client_name"].value.strip()
        if not name or len(name) > MAX_NAME_LENGTH:
            self.error = f"El nombre debe tener entre 1 y {MAX_NAME_LENGTH} caracteres."
            return
        self._connect(name, str(server["ip"]), int(server["tcp_port"]))

    def _connect(self, name: str, host: str, port: int) -> None:
        self._async(
            "client",
            f"Conectando a {host}:{port}...",
            lambda: self._build_client(name, host, port),
        )

    @staticmethod
    def _build_client(name: str, host: str, port: int) -> Any:
        from client.network import CTFClient

        client = CTFClient(host, port, name)
        try:
            client.connect()
        except Exception:
            client.close()
            raise
        return client

    def _async(self, kind: str, status: str, function: Callable[[], Any]) -> None:
        self.busy = True
        self.status = status
        self.error = ""

        def worker() -> None:
            try:
                self.results.put((kind, function()))
            except (TimeoutError, socket.timeout):
                self.results.put(("error", "La conexión agotó el tiempo de espera. Revisa IP, puerto y firewall."))
            except OSError as error:
                self.results.put(("error", f"No se pudo completar la conexión: {error}"))
            except Exception as error:
                self.results.put(("error", str(error)))

        threading.Thread(target=worker, daemon=True).start()

    def _open_server(self, server: Any) -> None:
        from server.app import ServerWindow

        ServerWindow(server)
        self.close()

    def _open_client(self, client: Any) -> None:
        from client.app import ClientWindow

        ClientWindow(client)
        self.close()


def run_launcher() -> None:
    LauncherWindow()
    arcade.run()
