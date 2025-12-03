from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton
from .utility.projectNameHandler import getProjectName
from .gui.mainMenu import createMenu
from .gui.settingsMenu import createSettingsMenu
import asyncio
import sys

def gameExec():
    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()

            title = getProjectName()
            self.setWindowTitle(title)
            self.show()

            self.showMainMenu()

        def showMainMenu(self):
            menu = createMenu(self.showSettingsMenu, parent=self)
            self.setCentralWidget(menu)

        def showSettingsMenu(self):
            settings = createSettingsMenu(self.showMainMenu, parent=self)
            self.setCentralWidget(settings)

    # Create the Qt application
    app = QApplication(sys.argv)

    window = MainWindow()

    app.exec()

if __name__ == "__main__":
    try:
        gameExec()
    except Exception:
        print("Oh no! Something went wrong.")
        raise