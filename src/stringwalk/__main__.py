from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton
from .utility.projectNameHandler import getProjectName
from .gui.mainMenu import createMenu
import asyncio
import sys

def gameExec():
    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()

            title = getProjectName()
            self.setWindowTitle(title)

    # Create the Qt application
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    menu = createMenu(parent=window)
    window.setCentralWidget(menu)

    app.exec()

if __name__ == "__main__":
    try:
        gameExec()
    except Exception:
        print("Oh no! Something went wrong.")
        raise