from PyQt6.QtWidgets import QWidget, QPushButton, QSizePolicy, QVBoxLayout
from PyQt6.QtCore import pyqtSignal, Qt
import asyncio
from ..utility.textHandler import getText
from ..utility.buttonHandler import handleButton
from ..gui.mainMenu import createMenu
from functools import partial

def createSettingsMenu(goBack, parent=None):
    widget = QWidget(parent)
    layout = QVBoxLayout()
    layout.setContentsMargins(50, 50, 50, 50)
    layout.setSpacing(20)

    layout.addStretch()

    keys = ["language", "back"]
    texts = asyncio.run(getText(keys))

    actions = [
        lambda w=None: None, 
        lambda w=None: goBack()
    ]

    buttons = []
    for text, action in zip(texts, actions):
        btn = QPushButton(text)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        btn.setMinimumHeight(40)
        btn.setMinimumWidth(200)
        btn.clicked.connect(partial(handleButton, action, widget))
        layout.addWidget(btn)

    layout.addStretch()

    widget.setLayout(layout)
    widget.show()
    return widget