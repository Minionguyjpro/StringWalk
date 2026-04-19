from PyQt6.QtWidgets import QApplication, QMainWindow, QSizePolicy, QWidget, QVBoxLayout, QStackedLayout
from PyQt6.QtCore import Qt, QTimer
from .utility.qtMessageHandler import installQtMessageHandler
from .utility.filter.SFXFilter import SFXFilter
from .utility.ui.qssProcessor import applyGlobalStyles
from .utility.data.projectNameHandler import getProjectName
from .utility.ui.resolutionHandler import getResolution, centerWindow, lockWindowSize
from .utility.video.videoManager import VideoManager
from .gui.mainMenu import createMainMenu
import asyncio
import os
import sys
import qasync
import nest_asyncio
from functools import partial
nest_asyncio.apply()


def gameExec():
    # Configure logging
    installQtMessageHandler()

    # Create the Qt application
    app = QApplication(sys.argv)

    sfx_filter = SFXFilter()
    app.installEventFilter(sfx_filter)

    # Try applying the global styling on the application
    try:
        applyGlobalStyles(app, "gui/styles")
    except Exception as err:
        print(f"Styling couldn't be loaded: {err}")

    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)

    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            title = getProjectName()
            self.setWindowTitle(title)

            # Central container
            self.central_container = QWidget(self)
            self.setCentralWidget(self.central_container)

            self.video_manager = None
            self.background_source = QWidget(self.central_container)
            self.background_source.setGeometry(self.central_container.rect())
            self.background_source.setStyleSheet(
                "background-color: #11151c;"
            )
            self.background_source.show()

            try:
                self.video_manager = VideoManager(self.central_container)
                self.video_manager.setGeometry(self.central_container.rect())
                self.video_manager.show()
                self.video_manager.play_video("lobby.mp4")
                self.background_source = self.video_manager
            except Exception as err:
                print(f"Video background unavailable: {err}")

            # Menu container on top (transparent)
            self.menu_container = QWidget(self.central_container)
            self.menu_container.setGeometry(self.central_container.rect())
            self.menu_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            self.menu_container.raise_()
            self.menu_container.show()

            # Stacked layout for smooth menu switching
            self.menu_layout = QStackedLayout(self.menu_container)
            self.menu_layout.setContentsMargins(0, 0, 0, 0)

            # Store already-created menus to avoid flicker
            self.menu_widgets = {}

            self.pause_background = None
            self.game_paused = False

        def navigate(self, factory, *, key=None, parent=None, background=None):
            if key is None:
                key = getattr(factory, "__name__", None) or f"menu_{id(factory)}"
            
            if key not in self.menu_widgets:
                # Create new menu if not cached
                widget = factory(self.navigate, parent=parent, background=background)
                self.menu_layout.addWidget(widget)
                self.menu_widgets[key] = widget
            else:
                # Update parent_window on cached menu
                widget = self.menu_widgets[key]
                if hasattr(widget, "parent_window") and parent is not None:
                    widget.parent_window = parent
                if hasattr(widget, "background") and background is not None:
                    widget.background = background

            self.menu_layout.setCurrentWidget(self.menu_widgets[key])

        def changeEvent(self, event):
            super().changeEvent(event)

            if event.type() == event.Type.WindowStateChange:
                new = self.windowState()
                old = event.oldState()

                # KDE fullscreen → normal fix
                if old == Qt.WindowState.WindowFullScreen and new == Qt.WindowState.WindowNoState:
                    # Step 1: hide to force decoration recalculation
                    self.hide()

                    # Step 2: showNormal and center after decorations are applied
                    QTimer.singleShot(0, lambda: self._kde_restore_and_center())
                    return

                # Normal unmaximize case
                if new == Qt.WindowState.WindowNoState:
                    QTimer.singleShot(0, lambda: centerWindow(self))

        def _kde_restore_and_center(self):
            self.showNormal()
            QTimer.singleShot(0, lambda: centerWindow(self))

        def resizeEvent(self, event):
            super().resizeEvent(event)
            if self.video_manager is not None:
                self.video_manager.setGeometry(self.central_container.rect())
            elif hasattr(self, "background_source"):
                self.background_source.setGeometry(self.central_container.rect())
            self.menu_container.setGeometry(self.central_container.rect())

        def return_to_menu(self, pixmap=None):
            self.menu_container.show()

            if pixmap:
                self.pause_background = pixmap
            else:
                self.pause_background = None

            self.menu_container.raise_()
    async def setup() -> MainWindow:
        res = await getResolution()
    
        main_window = MainWindow()

        if res.lower() == "fullscreen":
            main_window.showFullScreen()
        elif res.lower() == "maximized":
            main_window.showMaximized()
        else:
            try:
                x, y = map(int, res.split("x"))
            except ValueError:
                x, y = 800, 600
            lockWindowSize(main_window, x, y)
            main_window.show()    
            QTimer.singleShot(0, lambda: centerWindow(main_window))

        main_window.navigate(createMainMenu, key="MainMenu", parent=main_window, background=main_window.background_source)
        return main_window
    
    main_window = loop.run_until_complete(setup())

    with loop:
        loop.run_forever()

if __name__ == "__main__":
    try:
        gameExec()
    except Exception:
        print("Oh no! Something went wrong.")
        raise