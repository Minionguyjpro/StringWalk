import asyncio

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QLineEdit, QPushButton

from ..network.lobbyManager import LOBBY_PORT, lobby_manager
from ..utility.data.projectNameHandler import getProjectNameLower
from ..utility.data.textHandler import getText
from .backgroundWidget import BackgroundWidget
from ..utility.ui.menuHandler import addMenuWidget, finalizeMenuLayout, makeMenuLayout


def createLobbyMenu(navigate, parent=None, background=None) -> QWidget:
    class LobbyMenu(BackgroundWidget):
        def __init__(self, navigate, parent=None, background=None):
            super().__init__(parent)
            self.navigate = navigate
            self.parent_window = parent
            self.background = background

            self.texts = {}

            outer, inner = makeMenuLayout()
            self.layout_ref = inner
            self.setLayout(outer)

            lobby_manager.register_listener(self._on_lobby_update)
            self._reload_texts()

        def _reload_texts(self):
            keys = [
                "create_lobby",
                "join_lobby",
                "back",
                "lobby_title",
                "lobby_ip",
                "player_one",
                "player_two_waiting",
                "start"
            ]
            self.run_task(getText(keys), self._build_layout)

        def _build_layout(self, task):
            values = task.result()
            keys = [
                "create_lobby",
                "join_lobby",
                "back",
                "lobby_title",
                "lobby_ip",
                "player_one",
                "player_two_waiting",
                "start"
            ]
            self.texts = dict(zip(keys, values))

            for i in reversed(range(self.layout_ref.count())):
                item = self.layout_ref.itemAt(i)
                widget = item.widget()
                if widget:
                    widget.setParent(None)
                else:
                    self.layout_ref.removeItem(item)

            title = QLabel(self.texts["lobby_title"])
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            addMenuWidget(self.layout_ref, title)

            self.ip_input = QLineEdit()
            self.ip_input.setPlaceholderText(f"{self.texts['lobby_ip']} 192.168.1.10")
            addMenuWidget(self.layout_ref, self.ip_input)

            self.create_button = QPushButton(self.texts["create_lobby"])
            self.create_button.clicked.connect(lambda: asyncio.create_task(self.create_lobby()))
            addMenuWidget(self.layout_ref, self.create_button)

            self.join_button = QPushButton(self.texts["join_lobby"])
            self.join_button.clicked.connect(lambda: asyncio.create_task(self.join_lobby()))
            addMenuWidget(self.layout_ref, self.join_button)

            self.status_label = QLabel("")
            self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.status_label.setWordWrap(True)
            addMenuWidget(self.layout_ref, self.status_label)

            self.player_one_label = QLabel(self.texts["player_one"])
            self.player_one_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            addMenuWidget(self.layout_ref, self.player_one_label)

            self.player_two_label = QLabel(self.texts["player_two_waiting"])
            self.player_two_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            addMenuWidget(self.layout_ref, self.player_two_label)

            self.start_button = QPushButton(self.texts["start"])
            self.start_button.clicked.connect(self.parent_window.start_game_from_lobby)
            addMenuWidget(self.layout_ref, self.start_button)

            back_button = QPushButton(self.texts["back"])
            back_button.clicked.connect(lambda: asyncio.create_task(self.go_back()))
            addMenuWidget(self.layout_ref, back_button)

            self.layout_ref.addStretch()
            finalizeMenuLayout(self)
            self._apply_state(lobby_manager.snapshot())

        async def create_lobby(self):
            try:
                await lobby_manager.host_lobby()
            except OSError as err:
                self.status_label.setText(f"Could not create lobby: {err}")

        async def join_lobby(self):
            host = self.ip_input.text().strip()
            if not host:
                self.status_label.setText(f"Enter host IP and join on port {LOBBY_PORT}.")
                return

            try:
                await lobby_manager.join_lobby(host)
            except OSError as err:
                self.status_label.setText(f"Could not join lobby: {err}")

        async def go_back(self):
            await lobby_manager.close_lobby()

            if hasattr(self.parent_window, "menu_container"):
                self.parent_window.menu_container.show()

            self.navigate(
                __import__(
                    f"{getProjectNameLower()}.gui.mainMenu",
                    fromlist=["createMainMenu"]
                ).createMainMenu,
                parent=self.parent_window,
                background=self.background
            )

        def _on_lobby_update(self, state):
            self._apply_state(state)
            if len(state["players"]) > 1:
                x, y = state["players"][1]
                game_widget.set_remote_player(x, y)

        def _apply_state(self, state):
            if not hasattr(self, "status_label"):
                return

            players = state["players"]
            self.status_label.setText(state["status"])
            self.player_one_label.setText(players[0] if len(players) > 0 else self.texts.get("player_one", "Player 1"))
            self.player_two_label.setText(players[1] if len(players) > 1 else self.texts.get("player_two_waiting", "Waiting for Player 2"))

            if state["is_host"] and state["host_address"]:
                self.ip_input.setText(state["host_address"])

        def closeEvent(self, event):
            lobby_manager.unregister_listener(self._on_lobby_update)
            super().closeEvent(event)

    return LobbyMenu(navigate, parent=parent, background=background)