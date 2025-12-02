from PyQt6.QtWidgets import QWidget, QPushButton, QSizePolicy, QVBoxLayout
from PyQt6.QtCore import pyqtSignal, Qt
import asyncio
from ..utility.textHandler import getText
from ..utility.buttonHandler import handleButton
from functools import partial

def createMenu(parent=None):
    widget = QWidget(parent)
    layout = QVBoxLayout()
    layout.setContentsMargins(50, 50, 50, 50)
    layout.setSpacing(20)

    layout.addStretch()

    keys = ["start", "settings", "exit"]
    texts = asyncio.run(getText(keys))

    actions = [
        lambda w=None: print("Start pressed!"),           # Start button
        lambda w=None: print("Settings pressed!"),        # Settings button
        lambda w=None: exit()                             # Exit button
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