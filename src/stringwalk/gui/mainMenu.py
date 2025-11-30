from PyQt6.QtWidgets import QWidget, QPushButton, QVBoxLayout
from PyQt6.QtCore import pyqtSignal
from ..utility.textHandler import getText

async def fetch_i18n_keys():
    start_text = await getText("start")
    settings_text = await getText("settings")
    exit_text = await getText("exit")
    print(start_text, settings_text, exit_text)
    return start_text, settings_text, exit_text

def createMenu(parent=None, texts=None):
    widget = QWidget(parent)
    layout = QVBoxLayout()

    btn_start = QPushButton(texts[0])
    btn_settings = QPushButton(texts[1])
    btn_exit = QPushButton(texts[2])
    layout.addWidget(btn_start)
    layout.addWidget(btn_settings)
    layout.addWidget(btn_exit)

    widget.setLayout(layout)
    return widget

async def main():
    texts = await fetch_i18n_keys()  # fetch strings first
    menu_widget = createMenu(texts=texts)
    menu_widget.show()