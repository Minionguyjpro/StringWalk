import asyncio
import contextlib
import socket
import json


LOBBY_PORT = 50555


class LobbyManager:
    def __init__(self):
        self.server = None
        self.server_task = None
        self.reader_task = None
        self.client_writer = None
        self.client_reader = None
        self.peer_writer = None
        self.is_host = False
        self.players = []
        self.status = "No active lobby."
        self.host_address = ""
        self.listeners = set()
        self.closing = False

        self.game_widget = None

    def register_listener(self, callback):
        self.listeners.add(callback)

    def unregister_listener(self, callback):
        self.listeners.discard(callback)

    def snapshot(self):
        return {
            "is_host": self.is_host,
            "players": list(self.players),
            "status": self.status,
            "host_address": self.host_address,
            "has_lobby": self.server is not None or self.client_writer is not None,
        }

    def _notify(self):
        state = self.snapshot()
        for callback in list(self.listeners):
            callback(state)

    def _get_local_ip(self):
        try:
            probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            probe.connect(("8.8.8.8", 80))
            return probe.getsockname()[0]
        except OSError:
            return "127.0.0.1"
        finally:
            if "probe" in locals():
                probe.close()

    def _normalize_join_host(self, host: str):

        local_ip = self._get_local_ip()
        if host in {"localhost", "127.0.0.1", local_ip}:
            return "127.0.0.1"
        return host

    async def host_lobby(self, port=LOBBY_PORT):
        await self.close_lobby()

        self.closing = False
        self.is_host = True
        self.players = ["Player 1"]
        self.host_address = self._get_local_ip()
        self.status = f"Lobby created at {self.host_address}:{port}"
        self.server = await asyncio.start_server(self._handle_client, "0.0.0.0", port)
        self.server_task = asyncio.create_task(self.server.serve_forever())
        self._notify()

    async def join_lobby(self, host, port=LOBBY_PORT):
        await self.close_lobby()

        self.closing = False
        connect_host = self._normalize_join_host(host)
        self.client_reader, self.client_writer = await asyncio.open_connection(connect_host, port)
        self.is_host = False
        self.host_address = host
        self.players = ["Player 1", "Player 2"]
        self.status = f"Joined lobby at {host}:{port}"
        self.reader_task = asyncio.create_task(self._watch_host())
        self._notify()

    async def close_lobby(self):
        self.closing = True

        if self.reader_task is not None:
            self.reader_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.reader_task
            self.reader_task = None

        if self.server_task is not None:
            self.server_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.server_task
            self.server_task = None

        if self.client_writer is not None:
            self.client_writer.close()
            with contextlib.suppress(Exception):
                await self.client_writer.wait_closed()
            self.client_writer = None
            self.client_reader = None

        if self.peer_writer is not None:
            self.peer_writer.close()
            with contextlib.suppress(Exception):
                await self.peer_writer.wait_closed()
            self.peer_writer = None

        if self.server is not None:
            self.server.close()
            with contextlib.suppress(Exception):
                await self.server.wait_closed()
            self.server = None

        self.is_host = False
        self.players = []
        self.host_address = ""
        self.status = "No active lobby."
        self._notify()
        self.closing = False

    async def _handle_client(self, reader, writer):
        self.peer_writer = writer

        try:
            while True:
                line = await reader.readline()
                if not line:
                    break

                msg = json.loads(line.decode())
                self._on_network_message(msg)

                if self.peer_writer:
                    self.peer_writer.write(line)
                    await self.peer_writer.drain()

        except Exception:
            pass

    async def _watch_host(self):
        try:
            while True:
                line = await self.client_reader.readline()
                if not line:
                    break

                try:
                    msg = json.loads(line.decode())
                    self._dispatch_message(msg)
                except Exception as e:
                    print("Bad message:", e)

        except Exception as e:
            print("Lobby connection error:", e)

    def _dispatch_message(self, msg):
        player_id = msg.get("id")
        if not player_id:
            return

        x = msg.get("x", 0)
        y = msg.get("y", 0)
        vx = msg.get("vx", 0)
        vy = msg.get("vy", 0)

        if self.game_widget:
            self.game_widget.set_remote_player(player_id, x, y, vx, vy)

    def _on_network_message(self, msg: dict):
        try:
            player_id = msg.get("id", "remote")
            x = float(msg["x"])
            y = float(msg["y"])

            if self.game_widget:
                self.game_widget.set_remote_player(player_id, x, y)

        except Exception:
            pass

    async def send(self, data):
        if not self.peer_writer:
            return

        try:
            msg = json.dumps(data) + "\n"
            self.peer_writer.write(msg.encode())
        except (ConnectionResetError, BrokenPipeError):
            print("Lobby connection lost")
            return

    async def receive(self):
        if self.client_reader:
            line = await self.client_reader.readline()
            if not line:
                return None
            return json.loads(line.decode())
        return None

lobby_manager = LobbyManager()