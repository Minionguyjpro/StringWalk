from PyQt6.QtWidgets import QPushButton
import asyncio
import glob
from pathlib import Path
from ...utility.ui.asyncWidget import AsyncWidget
from ..backgroundWidget import BackgroundWidget
from ...utility.ui.menuHandler import makeMenuLayout, addMenuWidget, finalizeMenuLayout
from ...utility.jsonParser import parseJson
from ...utility.data.languageHandler import setLanguage
from ...utility.data.textHandler import getText
from ...utility.data.projectNameHandler import getProjectNameLower
from ...utility.ui.menuRefresh import refresh_all_menus


def createlangSelect(navigate, parent=None, background=None) -> BackgroundWidget:
    class langSelect(BackgroundWidget):
        def __init__(self, navigate, parent=None, background=None):
            super().__init__(parent)
            self.navigate = navigate
            self.parent_window = parent
            self.background = background

            # Main layout
            outer, inner = makeMenuLayout()
            self.layout_ref = inner
            self.setLayout(outer)

            # Gather available languages
            current_dir = Path(__file__).resolve().parent
            i18n_dir = current_dir.parent.parent / "i18n"
            files = glob.glob(str(i18n_dir / "*.json"))

            self.languages = []
            for f in files:
                path = Path(f)
                code = path.stem
                name = parseJson(f, "lang_name")
                if name:
                    self.languages.append((name, code))

            # Load initial back button text and build UI
            self.run_task(getText("back"), self._build_layout)

        def _build_layout(self, task):
            if self.layout_ref is None or not self.isVisible():
                return

            try:
                back_text = task.result()
            except Exception:
                back_text = "Back"

            # Clear old widgets and spacers
            for i in reversed(range(self.layout_ref.count())):
                item = self.layout_ref.itemAt(i)
                if item.widget():
                    item.widget().setParent(None)
                else:
                    # remove spacers
                    self.layout_ref.removeItem(item)

            # Language buttons
            for name, code in self.languages:
                btn = QPushButton(name)
                btn.setProperty("variant", "setting")
                btn.clicked.connect(lambda checked, c=code: asyncio.create_task(self.setLanguageAndReload(c)))
                addMenuWidget(self.layout_ref, btn)

            # Back button
            back_btn = QPushButton(back_text)
            back_btn.clicked.connect(
                lambda: self.navigate(
                    __import__(
                        f"{getProjectNameLower()}.gui.settingsMenu",
                        fromlist=["createSettingsMenu"]
                    ).createSettingsMenu,
                    parent=self.parent_window,
                    background=self.background
                )
            )
            addMenuWidget(self.layout_ref, back_btn)

            self.layout_ref.addStretch()
            finalizeMenuLayout(self)

        async def setLanguageAndReload(self, lang_code):
            await setLanguage(lang_code)

            # Fetch updated back text and rebuild UI
            self.text_task = self.run_task(getText("back"), self._build_layout)

            # Refresh all menus
            refresh_all_menus()

    return langSelect(navigate, parent, background)
