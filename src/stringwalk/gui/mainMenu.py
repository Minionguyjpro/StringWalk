from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QSizePolicy
from ..utility.ui.asyncWidget import AsyncWidget
from ..utility.ui.menuHandler import makeMenuLayout, addMenuWidget, finalizeMenuLayout
from ..utility.data.textHandler import getText
from ..utility.audio.soundHandler import playSound, toggleSound
from ..utility.audio.audioManager import audio
from ..utility.data.projectNameHandler import getProjectNameLower
from ..utility.ui.buttonHandler import reloadButton
from ..gui.gameWidget import GameWidget


def createMainMenu(navigate, parent=None):
    class MainMenu(AsyncWidget):
        def __init__(self, navigate, parent=None):
            super().__init__(parent)
            self.navigate = navigate
            self.parent_window = parent

            print(">>> MainMenu.__init__ called")
            print("    parent:", parent)
            print("    type(parent):", type(parent))
            print("    isinstance parent MainWindow?", isinstance(parent, QWidget))

            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

            # Main layout
            outer, inner = makeMenuLayout()
            self.keys = ["start", "settings", "exit", "sound"]
            self.layout_ref = inner

            global lobbyMusic
            lobbyMusic = "music", "lobby.mp3"

            playSound(lobbyMusic[0], lobbyMusic[1])

            self._reload_texts()

            self.setLayout(outer)

        def _reload_texts(self):
            """Fetch texts and rebuild buttons."""
            self.run_task(getText(self.keys), self.__texts_loaded)

        def __texts_loaded(self, task):
            texts = task.result()
            
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

            actions = [
                lambda w=None: self.start_game(),
                lambda w=None: self.navigate(
                    __import__(
                        f"{getProjectNameLower()}.gui.settingsMenu",
                        fromlist=["createSettingsMenu"]
                    ).createSettingsMenu,
                    key="SettingsMenu",
                    parent=self.parent_window
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
            for key, text, action in zip(self.keys, texts, actions):
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
            self.parent_window.game_widget = GameWidget(on_exit=self.return_to_menu)

        def return_to_menu(self):
            # Show menu container again when exiting game
            if self.parent_window and hasattr(self.parent_window, "menu_container"):
                self.parent_window.menu_container.show()

    return MainMenu(navigate, parent=parent)
