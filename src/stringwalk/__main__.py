from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton
from .utility.projectNameHandler import getProjectName
from .gui.mainMenu import createMainMenu
from .gui.settingsMenu import createSettingsMenu
import asyncio
import sys
import qasync
import nest_asyncio
nest_asyncio.apply()


def gameExec():
    # Create the Qt application
    app = QApplication(sys.argv)

    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()

            title = getProjectName()
            self.setWindowTitle(title)
            self.show()

        def navigate(self, factory):
            """Replace central widget with a new menu instance."""
            widget = factory(self.navigate, parent=self)
            self.setCentralWidget(widget)

    window = MainWindow()
    window.resize(400, 300)
    window.navigate(createMainMenu)

    with loop:
        loop.run_forever()

if __name__ == "__main__":
    try:
        gameExec()
    except Exception:
        print("Oh no! Something went wrong.")
        raise