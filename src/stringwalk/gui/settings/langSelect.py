from PyQt6.QtWidgets import QWidget, QPushButton, QSizePolicy, QVBoxLayout
from PyQt6.QtCore import pyqtSignal, Qt
import asyncio
import glob
from pathlib import Path
from ...utility.jsonParser import parseJson
from ...utility.languageHandler import setLanguage
from ...utility.textHandler import getText
from ...utility.projectNameHandler import getProjectNameLower
from functools import partial
import os


def createlangSelect(navigate, parent=None):
    class langSelect(QWidget):
        def __init__(self, navigate, parent=None):
            super().__init__(parent)
            self.navigate = navigate

            self.layout_ref = QVBoxLayout()
            self.layout_ref.setContentsMargins(50, 50, 50, 50)
            self.layout_ref.setSpacing(20)
            self.layout_ref.addStretch()
            self.setLayout(self.layout_ref)

            current_dir = Path(__file__).resolve().parent
            i18n_dir = current_dir.parent.parent / "i18n"
            files = glob.glob(str(i18n_dir / "*.json"))

            self.languages = []
            for f in files:
                path = Path(f)
                code = path.stem
                name = parseJson(f, "lang_name")
                if name:
                    self.languages.append((name, code))

            loop = asyncio.get_event_loop()
            task = loop.create_task(getText(["back"]))
            task.add_done_callback(self.__texts_loaded)

        def __texts_loaded(self, task):
            texts = task.result()

            # Create language buttons
            for name, code in self.languages:
                lang_btn = QPushButton(name)
                lang_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                lang_btn.setMinimumHeight(40)
                lang_btn.setMinimumWidth(200)
                lang_btn.clicked.connect(lambda checked, c=code: asyncio.create_task(self.setLanguageAndReload(c)))
                self.layout_ref.addWidget(lang_btn)

            # Back button
            back_btn = QPushButton(texts[0])
            back_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            back_btn.setMinimumHeight(40)
            back_btn.setMinimumWidth(200)
            back_btn.clicked.connect(
                lambda: self.navigate(
                    __import__(f"{getProjectNameLower()}.gui.settingsMenu", fromlist=["createSettingsMenu"]).createSettingsMenu
                )
            )
            self.layout_ref.addWidget(back_btn)

            self.layout_ref.addStretch()

        async def setLanguageAndReload(self, lang_code):
            await setLanguage(lang_code)

            # Reload settings menu
            self.navigate(
                __import__(
                    f"{getProjectNameLower()}.gui.settingsMenu",
                    fromlist=["createSettingsMenu"]
                ).createSettingsMenu
            )

    return langSelect(navigate, parent)
