from PyQt6.QtWidgets import QPushButton
from ..utility.ui.asyncWidget import AsyncWidget
from ..utility.ui.menuHandler import makeMenuLayout, addMenuWidget, finalizeMenuLayout
from ..utility.data.textHandler import getText
from ..utility.data.projectNameHandler import getProjectNameLower


def createSettingsMenu(navigate, parent=None):
    class SettingsMenu(AsyncWidget):
        def __init__(self, navigate, parent=None):
            super().__init__(parent)
            self.navigate = navigate
            self.parent_window = parent

            outer, inner = makeMenuLayout()

            self.keys = ["language", "resolution", "back"]
            self.layout_ref = inner

            self.setLayout(outer)

            self._reload_texts()

        def _reload_texts(self):
            """Fetch texts and rebuild buttons."""
            self.run_task(getText(self.keys), self.__texts_loaded)

        def __texts_loaded(self, task):
            texts = task.result()

            actions = [
                lambda w=None: self.navigate(
                    __import__(
                        f"{getProjectNameLower()}.gui.settings.langSelect",
                        fromlist=["createlangSelect"]
                    ).createlangSelect,
                    parent=self.parent_window
                ),
                lambda w=None: self.navigate(
                    __import__(
                        f"{getProjectNameLower()}.gui.settings.resolutionSelect",
                        fromlist=["createresolutionSelect"]
                    ).createresolutionSelect,
                    parent=self.parent_window
                ),
                lambda w=None: self.navigate(
                    __import__(
                        f"{getProjectNameLower()}.gui.mainMenu",
                        fromlist=["createMainMenu"]
                    ).createMainMenu,
                    parent=self.parent_window
                ),
            ]

            # Clear old widgets first
            for i in reversed(range(self.layout_ref.count())):
                item = self.layout_ref.itemAt(i)
                widget = item.widget()
                if widget:
                    widget.setParent(None)

            # Add new buttons
            for text, action in zip(texts, actions):
                btn = QPushButton(text)
                btn.clicked.connect(action)
                addMenuWidget(self.layout_ref, btn)

            self.layout_ref.addStretch()
            finalizeMenuLayout(self)

    return SettingsMenu(navigate, parent=parent)
