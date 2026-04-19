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
from ..gui.gameWidget import GameWidget


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
            self.keys = ["start", "settings", "exit", "sound"]
            self.layout_ref = inner

            self.pause_background = None

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
            texts = task.result()

            keys = self.keys.copy()

            if getattr(self.parent_window, "pause_background", None):
                keys.insert(0, "resume")  # Add "resume" at the beginning if paused
            
            sound_btn = None  # Will store reference to sound button

            def toggle_mute(_=None):
                toggleSound(lobbyMusic[0], lobbyMusic[1])
                # Update button visual state after toggle
                if sound_btn:
                    if not audio.music_muted:
                        sound_btn.setProperty("variant", "sound")
                    else:
                        sound_btn.setProperty("variant", "mute")
                    reloadButton(sound_btn)

            actions = []

            if getattr(self.parent_window, "pause_background", None):
                actions.append(lambda w=None: self.resume_game())  # Resume action

            actions += [
                lambda w=None: self.start_game(),
                lambda w=None: self.navigate(
                    __import__(
                        f"{getProjectNameLower()}.gui.settingsMenu",
                        fromlist=["createSettingsMenu"]
                    ).createSettingsMenu,
                    key="SettingsMenu",
                    parent=self.parent_window,
                    background=getattr(self.parent_window, "pause_background", None) or self.background
                ),
                lambda w=None: QApplication.quit(),
                toggle_mute
            ]

            # Clear old widgets first
            for i in reversed(range(self.layout_ref.count())):
                item = self.layout_ref.itemAt(i)
                widget = item.widget()
                if widget:
                    widget.setParent(None)

            # Add buttons
            for key, text, action in zip(keys, texts, actions):
                btn = QPushButton(text)
                btn.clicked.connect(action)
                addMenuWidget(self.layout_ref, btn)

                if key == "sound":
                    sound_btn = btn  # Store reference
                    if not audio.music_muted:
                        btn.setProperty("variant", "sound")
                    else:
                        btn.setProperty("variant", "mute")

                    reloadButton(btn)  # Apply the new property to update the style

            self.layout_ref.addStretch()
            finalizeMenuLayout(self)

        def start_game(self):
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
            
            self.parent_window.game_widget = GameWidget(
                parent=parent_container,
                on_exit=self.return_to_menu
            )

            self.parent_window.game_widget.setGeometry(parent_container.rect())
            self.parent_window.game_widget.show()
            self.parent_window.game_widget.raise_()
            self.parent_window.game_widget.setFocus()

            self.parent_window.pause_background = None  # Clear pause background when starting game

        def resume_game(self):
            game = getattr(self.parent_window, "game_widget", None)

            if not game:
                return

            self.parent_window.menu_container.hide()  # Hide menu when resuming

            game.show()
            game.raise_()

            parent_container = getattr(self.parent_window, "central_container", self.parent_window)
            game.setGeometry(parent_container.rect())

            game.resume_game()

            QTimer.singleShot(0, game.setFocus)

            self.parent_window.pause_background = None  # Clear pause background when resuming

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
