from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QSizePolicy
from PyQt6.QtGui import QPainter, QKeyEvent, QColor
from PyQt6.QtCore import Qt, QTimer
from ..utility.ui.asyncWidget import AsyncWidget
from ..utility.ui.menuHandler import makeMenuLayout, addMenuWidget, finalizeMenuLayout
from ..utility.data.textHandler import getText
from ..utility.audio.soundHandler import playSound, toggleSound
from ..utility.audio.audioManager import audio
from ..utility.graphics.screenHandler import captureWidget, blur_pixmap
from ..utility.data.projectNameHandler import getProjectNameLower
from ..utility.ui.buttonHandler import reloadButton
from .gameWidget import GameWidget
from .lobbyMenu import createLobbyMenu


def createMainMenu(navigate, parent=None, background=None) -> QWidget:
    class MainMenu(AsyncWidget):
        def __init__(self, navigate, parent=None):
            super().__init__(parent)

            global lobbyMusic

            self.navigate = navigate
            self.parent_window = parent
            self.background = background

            print(">>> MainMenu.__init__ called")
            print("    parent:", parent)
            print("    type(parent):", type(parent))
            print("    isinstance parent MainWindow?", isinstance(parent, QWidget))

            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

            # Main layout
            outer, inner = makeMenuLayout()
            self.keys = ["start", "start_multiplayer", "settings", "exit", "sound"]
            self.layout_ref = inner

            self.parent_container = getattr(self.parent_window, "central_container", self.parent_window)

            self.pause_background = None

            self.sound_btn = None

            lobbyMusic = "music", "lobby.mp3"
            playSound(*lobbyMusic)

            self._reload_texts()

            self.setLayout(outer)

        def _reload_texts(self):
            keys = self.keys.copy()

            if getattr(self.parent_window, "pause_background", None):
                keys.insert(0, "resume")  # Add "resume" at the beginning if paused

            """Fetch texts and rebuild buttons."""
            self.run_task(getText(keys), self.__texts_loaded)

        def __texts_loaded(self, task):
            try:
                texts = task.result()
            except Exception as e:
                print("Text loading failed:", e)
                return

            def safe_text(i):
                return texts[i] if i < len(texts) else ""

            items = []

            if getattr(self.parent_window, "pause_background", None):
                items.append(("resume", safe_text(0), self.resume_game))
                offset = 1
            else:
                items.append(("start", safe_text(0), self.start_game))
                items.append(("start_multiplayer", safe_text(1), self.start_game_multiplayer))
                offset = 2

            items += [
                ("settings", safe_text(offset), self.open_settings),
                ("exit", safe_text(offset + 1), QApplication.quit),
            ]

            items.append(("sound", safe_text(offset + 2), self.toggle_mute))

            # CLEAR UI
            for i in reversed(range(self.layout_ref.count())):
                w = self.layout_ref.itemAt(i).widget()
                if w:
                    w.setParent(None)

            # BUILD UI
            for key, text, action in items:
                btn = QPushButton(text)
                btn.clicked.connect(action)
                addMenuWidget(self.layout_ref, btn)

                if key == "sound":
                    self.sound_btn = btn
                    btn.setProperty("variant", "sound" if not audio.music_muted else "mute")
                    reloadButton(btn)

            self.layout_ref.addStretch()
            finalizeMenuLayout(self)

        def open_settings(self, _=None):
            self.navigate(
                __import__(
                    f"{getProjectNameLower()}.gui.settingsMenu",
                    fromlist=["createSettingsMenu"]
                ).createSettingsMenu,
                key="SettingsMenu",
                parent=self.parent_window,
                background=getattr(self.parent_window, "pause_background", None) or self.background
            )

        def toggle_mute(self, _=None):
            toggleSound(lobbyMusic[0], lobbyMusic[1])
            if self.sound_btn:
                self.sound_btn.setProperty(
                    "variant",
                    "sound" if not audio.music_muted else "mute"
                )
                reloadButton(self.sound_btn)

        def start_game(self):
            game = self._start_game(
                GameWidget(
                    parent=self.parent_container,
                    on_exit=self.return_to_menu
                )
            )

        def start_game_multiplayer(self):
            self.navigate(
                createLobbyMenu,
                parent=self.parent_window,
                background=getattr(self.parent_window, "pause_background", None) or self.background
            )

        def _start_game(self, widget_obj, clear_background=True):
            if not self.parent_window:
                print("Error: parent_window is None! Cannot start game.")
                return

            # Stop background video
            if hasattr(self.parent_window, "video_manager"):
                try:
                    self.parent_window.video_manager.stop_video()
                except AttributeError:
                    print("Warning: video_manager.stop_video failed.")

            # Hide menu container
            if hasattr(self.parent_window, "menu_container"):
                self.parent_window.menu_container.hide()

            # Launch the game
            parent_container = getattr(self.parent_window, "central_container", self.parent_window)

            self.parent_window.mode = "game" if isinstance(widget_obj, GameWidget) else "lobby"

            self.parent_window.game_widget = widget_obj
            widget_obj.mode = "game" if isinstance(widget_obj, GameWidget) else "lobby"

            self.parent_window.game_widget.setGeometry(parent_container.rect())
            self.parent_window.game_widget.show()
            self.parent_window.game_widget.raise_()
            self.parent_window.game_widget.setFocus()     

        def resume_game(self):
            game = getattr(self.parent_window, "game_widget", None)

            if not game:
                return

            self.parent_window.menu_container.hide()  # Hide menu when resuming

            game.show()
            game.raise_()

            parent_container = getattr(self.parent_window, "central_container", self.parent_window)
            game.setGeometry(parent_container.rect())

            if getattr(game, "mode", None) == "lobby":
                self.parent_window.pause_background = None  # Clear pause background when resuming lobby

            game.resume_game()

            QTimer.singleShot(0, game.setFocus)

        def open_settings(self, _=None):
            self.navigate(
                __import__(
                    f"{getProjectNameLower()}.gui.settingsMenu",
                    fromlist=["createSettingsMenu"]
                ).createSettingsMenu,
                key="SettingsMenu",
                parent=self.parent_window,
                background=getattr(self.parent_window, "pause_background", None) or self.background
            )

        def return_to_menu(self, pixmap=None):
            # Show menu container again when exiting game
            if self.parent_window:
                self.parent_window.menu_container.show()

            if pixmap:
                self.parent_window.pause_background = blur_pixmap(pixmap)
            else:
                self.parent_window.pause_background = None
            
            self.update()
            self._reload_texts()

            QTimer.singleShot(0, self._force_focus)

        def _force_focus(self):
            self.raise_()
            self.activateWindow()
            self.setFocus()

        def keyPressEvent(self, event):
            if event.key() == Qt.Key.Key_Escape:
                self.resume_game()
                event.accept()
                return

            super().keyPressEvent(event)
        def showEvent(self, event):
            super().showEvent(event)
            self.setFocus()

        def paintEvent(self, event):
            if not self.parent_window.pause_background:
                return

            painter = QPainter(self)

            bg = getattr(self.parent_window, "pause_background", None)

            if bg:
                painter.drawPixmap(self.rect(), bg)
            else:
                painter.fillRect(self.rect(), QColor("#1e1e1e"))

            painter.end()

    return MainMenu(navigate, parent=parent)
