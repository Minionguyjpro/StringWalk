from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel
from ..configHandler import readConfigItem, writeConfigItem
from ..data.textHandler import getText
from dataclasses import dataclass, field
import asyncio


class Overlay:
    def __init__(self, game_widget):
        self.game_widget = game_widget
        
        self.labels = {}
        self.values = {}

        self.display = {}

    def register(self, key: str, label_text: str):
        label = QLabel(self.game_widget)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        index = len(self.labels)
        label.move(10, 10 + index * 20)
        
        asyncio.create_task(self._load_translations())

        label.show()

        self.labels[key] = label
        self.values[key] = label_text

    def set(self, key: str, value, unit=""):
        if key in self.labels:
            prefix = self.display.get(key, key)
            if unit:
                self.labels[key].setText(f"{prefix}: {value} {unit}")
            else:
                self.labels[key].setText(f"{prefix}: {value}")

    async def _load_translations(self):
        for key in self.labels.keys():
            self.display[key] = await getText(key)

    @staticmethod
    async def is_enabled() -> bool:
        state = await readConfigItem("debug_mode", default=False)
        
        if state is None:
            await writeConfigItem("debug_mode", False)
            return False
        
        return state