from PyQt6.QtWidgets import QPushButton
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt
from ..utility.ui.asyncWidget import AsyncWidget
from .backgroundWidget import BackgroundWidget
from ..utility.ui.menuHandler import makeMenuLayout
from ..utility.data.textHandler import getText
from ..utility.data.projectNameHandler import getProjectNameLower
from ..utility.io.keyManager import save_bindings
import asyncio


def _hotkey_name_from_event(event) -> str:
    text = event.text().strip()

    if text:
        return text.upper()

    try:
        key_name = Qt.Key(event.key()).name
        if key_name.startswith("Key_"):
            return key_name[4:]
        return key_name
    except Exception:
        return str(event.key())

def createHotkeyMenu(nav, parent=None, bindings=None, background=None) -> QWidget:
    if bindings is None:
        bindings = {
            "jump": "Space",
            "move_left": "A",
            "move_right": "D",
            "pause": "Escape"
        }

    class HotkeyMenu(BackgroundWidget):
        def __init__(self, navigate, parent=None, bindings=None, background=None):
            super().__init__(parent)
            
            self.navigate = navigate
            self.parent_window = parent
            self.background = background
            self.bindings = dict(bindings or {})
            self.action_labels = {
                "jump": "Jump",
                "move_left": "Move Left",
                "move_right": "Move Right",
                "pause": "Pause",
            }

            outer, inner = makeMenuLayout()
            self.layout_ref = inner
            self.setLayout(outer)

            self.buttons = {}

            for action, key in self.bindings.items():
                btn = HotkeyButton(self.action_labels.get(action, action), action, key, self.on_change)
                self.layout_ref.addWidget(btn)
                self.buttons[action] = btn

            self.back_btn = QPushButton("Back")
            self.back_btn.clicked.connect(self.go_back)
            self.layout_ref.addWidget(self.back_btn)

            self.run_task(getText("back"), self._back_text_loaded)
            self.run_task(getText(list(self.action_labels.keys())), self._action_texts_loaded)

            self.layout_ref.addStretch()

        def _back_text_loaded(self, task):
            try:
                self.back_btn.setText(task.result())
            except Exception:
                self.back_btn.setText("Back")

        def _action_texts_loaded(self, task):
            try:
                labels = task.result()
            except Exception:
                labels = []

            for action, label in zip(self.action_labels.keys(), labels):
                self.action_labels[action] = label
                if action in self.buttons:
                    self.buttons[action].set_action_label(label)

        def on_change(self, action, new_key):
            self.bindings[action] = new_key

            asyncio.create_task(self._delayed_save())

        async def _delayed_save(self):
            await asyncio.sleep(0.5)  # debounce
            await save_bindings(self.bindings)

        def go_back(self):
            self.navigate(
                __import__(
                    f"{getProjectNameLower()}.gui.settingsMenu",
                    fromlist=["createSettingsMenu"]
                ).createSettingsMenu,
                parent=self.parent_window,
                background=self.background
            )

    class HotkeyButton(QPushButton):
        def __init__(self, action_label, action_name, key, on_change=None):
            super().__init__(f"{action_label}: {key}")
            self.action_label = action_label
            self.action_name = action_name
            self.key = key
            self.on_change = on_change
            self.listening = False

            self.refresh()

            self.clicked.connect(self.start_capture)

        def refresh(self):
            self.setText(f"{self.action_label}: {self.key}")

        def set_action_label(self, action_label):
            self.action_label = action_label
            self.refresh()

        def start_capture(self):
            self.setText(f"{self.action_label}: ... (press key)")
            self.listening = True
            self.setFocus()

        def keyPressEvent(self, event):
            if not self.listening:
                return super().keyPressEvent(event)

            # convert Qt key → readable string
            key_name = _hotkey_name_from_event(event)

            self.key = key_name
            self.listening = False

            self.refresh()

            if self.on_change:
                self.on_change(self.action_name, key_name)
    return HotkeyMenu(nav, parent=parent, bindings=bindings, background=background)