from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QSizePolicy, QVBoxLayout
from ..utility.textHandler import getText
from ..utility.projectNameHandler import getProjectNameLower
from ..utility.buttonHandler import handleButton
from functools import partial
import asyncio


def createMainMenu(navigate, parent=None):
    class MainMenu(QWidget):
        def __init__(self, navigate, parent=None):
            super().__init__(parent)
            self.navigate = navigate

            # Main layout
            layout = QVBoxLayout()
            layout.setContentsMargins(50, 50, 50, 50)
            layout.setSpacing(20)
            layout.addStretch()

            self.keys = ["start", "settings", "exit"]
            self.layout_ref = layout

            loop = asyncio.get_event_loop()
            task = loop.create_task(getText(self.keys))
            task.add_done_callback(self.__texts_loaded)

            self.setLayout(layout)

        def __texts_loaded(self, task):
            texts = task.result()

            actions = [
                lambda w=None: print("Start pressed!"),
                lambda w=None: self.navigate(
                    __import__(
                        f"{getProjectNameLower()}.gui.settingsMenu",
                        fromlist=["createSettingsMenu"]
                    ).createSettingsMenu
                ),
                lambda w=None: QApplication.quit()
            ]

            for text, action in zip(texts, actions):
                btn = QPushButton(text)
                btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
                btn.setMinimumHeight(40)
                btn.setMinimumWidth(200)
                btn.clicked.connect(partial(handleButton, action, self))
                self.layout_ref.addWidget(btn)

            self.layout_ref.addStretch()

    return MainMenu(navigate, parent)
