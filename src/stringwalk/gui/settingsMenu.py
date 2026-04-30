from PyQt6.QtWidgets import QPushButton, QWidget
from ..utility.ui.asyncWidget import AsyncWidget
from .backgroundWidget import BackgroundWidget
from ..utility.ui.menuHandler import makeMenuLayout, addMenuWidget, finalizeMenuLayout
from ..utility.ui.menuRefresh import register_menu
from ..utility.data.textHandler import getText
from ..utility.data.projectNameHandler import getProjectNameLower
from ..utility.io.keyManager import load_bindings


def createSettingsMenu(navigate, parent=None, background=None) -> QWidget:
    class SettingsMenu(BackgroundWidget):
        def __init__(self, navigate, parent=None, background=None):
            super().__init__(parent)
            self.navigate = navigate
            self.parent_window = parent
            self.background = background

            register_menu(self)

            outer, inner = makeMenuLayout()

            self.keys = ["language", "resolution", "fps", "hotkeys", "back"]
            self.layout_ref = inner

            self.run_task(load_bindings(), self._hotkeys_loaded)
            self.hotkeys = {}

            self.setLayout(outer)

            self._reload_texts()

        def _reload_texts(self):
            """Fetch texts and rebuild buttons."""
            self.run_task(getText(self.keys), self.__texts_loaded)

        def _hotkeys_loaded(self, task):
            self.hotkeys = task.result()

        def __texts_loaded(self, task):
            texts = task.result()

            items = [
                (
                    texts[0],
                    lambda w=None: self.navigate(
                        __import__(
                            f"{getProjectNameLower()}.gui.settings.langSelect",
                            fromlist=["createlangSelect"]
                        ).createlangSelect,
                        parent=self.parent_window,
                        background=self.background
                    )
                ),
                (
                    texts[1],
                    lambda w=None: self.navigate(
                        __import__(
                            f"{getProjectNameLower()}.gui.settings.resolutionSelect",
                            fromlist=["createresolutionSelect"]
                        ).createresolutionSelect,
                        parent=self.parent_window,
                        background=self.background
                    )
                ),
                (
                    texts[2],
                    lambda w=None: self.navigate(
                        __import__(
                            f"{getProjectNameLower()}.gui.settings.fpsSelect",
                            fromlist=["createfpsSelect"]
                        ).createfpsSelect,
                        parent=self.parent_window,
                        background=self.background
                    )
                ),
                (
                    texts[3],
                    lambda w=None: self.navigate(
                        lambda nav, parent=None, background=None: __import__(
                            f"{getProjectNameLower()}.gui.hotkeyMenu",
                            fromlist=["createHotkeyMenu"]
                        ).createHotkeyMenu(nav, parent, self.hotkeys, background),
                        parent=self.parent_window,
                        background=self.background
                    )
                ),
                (
                    texts[4],
                    lambda w=None: self.navigate(
                        __import__(
                            f"{getProjectNameLower()}.gui.mainMenu",
                            fromlist=["createMainMenu"]
                        ).createMainMenu,
                        parent=self.parent_window,
                        background=self.background
                    )
                ),
            ]

            for text, action in items:
                btn = QPushButton(text)
                btn.clicked.connect(action)
                addMenuWidget(self.layout_ref, btn)

    return SettingsMenu(navigate, parent=parent, background=background)
