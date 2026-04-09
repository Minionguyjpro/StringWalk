from PyQt6.QtWidgets import QComboBox, QPushButton
from PyQt6.QtCore import Qt, QTimer
import asyncio
from ...utility.ui.asyncWidget import AsyncWidget
from ...utility.ui.menuHandler import makeMenuLayout, addMenuWidget, finalizeMenuLayout
from ...utility.configHandler import readConfigItem, writeConfigItem
from ...utility.data.textHandler import getText
from ...utility.ui.resolutionHandler import getResolution, lockWindowSize, centerWindow
from ...utility.data.projectNameHandler import getProjectNameLower


def createresolutionSelect(navigate, parent=None, background=None) -> AsyncWidget:
    class resolutionSelect(AsyncWidget):
        def __init__(self, navigate, parent=None):
            super().__init__(parent)
            self.navigate = navigate
            self.parent_window = parent
            self.background = background
            self.valid_resolution = True

            # Layout
            outer, inner = makeMenuLayout()
            self.layout_ref = inner
            self.setLayout(outer)

            self.run_task(self._load_resolutions(), self._res_loaded)

        async def _load_resolutions(self):
            # Read all valid resolutions from config
            try:
                resolutions = await readConfigItem("resolutions", default=["800x600"])
            except Exception:
                resolutions = ["800x600"]

            current_res = await getResolution()
            return resolutions, current_res

        def _res_loaded(self, task):
            try:
                res, current_res = task.result()  # <-- unpack the tuple correctly
            except Exception:
                res = ["800x600"]
                current_res = "800x600"

            # Convert resolutions to strings if needed
            self.resolutions = []
            for r in res:
                if isinstance(r, (list, tuple)):
                    self.resolutions.append(f"{r[0]}x{r[1]}")
                else:
                    self.resolutions.append(str(r))

            # Save current resolution
            self.current_res = str(current_res) if current_res else self.resolutions[0]

            self._reload_texts()

        def _reload_texts(self):
            """Rebuild texts for back button and dropdown."""
            self.run_task(getText(["back", "fullscreen", "maximized"]), self._build_layout)

        def _build_layout(self, task):
            try:
                back_text, fullscreen_disp, maximized_disp = task.result()
            except Exception:
                back_text, fullscreen_disp, maximized_disp = "Back", "Fullscreen", "Maximized"

            # Preserve previous selection if dropdown exists
            if hasattr(self, "res_dropdown") and self.res_dropdown is not None:
                selected_internal = self.reverse_map.get(
                    self.res_dropdown.currentText(),
                    self.res_dropdown.currentText()
                )
            else:
                selected_internal = getattr(self, "current_res", "800x600")

            # Clear layout
            for i in reversed(range(self.layout_ref.count())):
                item = self.layout_ref.itemAt(i)
                widget = item.widget()
                if widget:
                    widget.setParent(None)

            # Convert list/tuple resolutions to strings if needed
            res_strings = []
            for r in self.resolutions:
                if isinstance(r, (list, tuple)):
                    res_strings.append(f"{r[0]}x{r[1]}")
                else:
                    res_strings.append(str(r))

            # Build internal/display maps
            self.internal_items = self.resolutions + ["fullscreen", "maximized"]
            self.display_map = {r: r for r in self.resolutions}
            self.display_map.update({
                "fullscreen": fullscreen_disp,
                "maximized": maximized_disp
            })
            self.reverse_map = {v: k for k, v in self.display_map.items()}

            # Dropdown
            self.res_dropdown = QComboBox()
            self.res_dropdown.setProperty("variant", "setting")
            self.res_dropdown.setEditable(True)
            self.res_dropdown.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.res_dropdown.lineEdit().textEdited.connect(self._validate_resolution)

            for r in self.internal_items:
                self.res_dropdown.addItem(self.display_map.get(r, r))

            self.res_dropdown.setCurrentText(self.display_map.get(selected_internal, selected_internal))

            self.res_dropdown.currentTextChanged.connect(
                lambda val: asyncio.create_task(self.setResolutionAndReload(val))
            )

            addMenuWidget(self.layout_ref, self.res_dropdown)

            # Back button
            back_btn = QPushButton(back_text)
            back_btn.clicked.connect(
                lambda: self.navigate(
                    __import__(
                        f"{getProjectNameLower()}.gui.settingsMenu",
                        fromlist=["createSettingsMenu"]
                    ).createSettingsMenu,
                    parent=self.parent_window
                )
            )
            addMenuWidget(self.layout_ref, back_btn)

            self.layout_ref.addStretch()
            finalizeMenuLayout(self)

        def _validate_resolution(self, text):
            # Only validate numeric resolutions, ignore fullscreen/maximized
            if text.lower() in ("fullscreen", "maximized"):
                self._set_valid()
                return
            if "x" not in text.lower():
                self._set_invalid()
                return
            try:
                w, h = map(int, text.lower().split("x"))
            except ValueError:
                self._set_invalid()
                return
            if w < 800 or h < 600:
                self._set_invalid()
            else:
                self._set_valid()

        def _set_invalid(self):
            self.valid_resolution = False
            line = self.res_dropdown
            line.setStyleSheet("color: darkred;")

        def _set_valid(self):
            self.valid_resolution = True
            line = self.res_dropdown
            line.setStyleSheet("color: white;")

        async def setResolutionAndReload(self, display_value):
            if not self.valid_resolution:
                print("Resolution invalid — not applying")
                return

            # Convert display - internal key
            resolution = self.reverse_map.get(display_value, display_value)
            await writeConfigItem("current_resolution", resolution)

            window = self.nativeParentWidget()
            if not window:
                return

            if resolution == "fullscreen":
                window.showFullScreen()
                return
            if resolution == "maximized":
                window.showMaximized()
                return

            try:
                width, height = map(int, resolution.split("x"))
                window.showNormal()

                def apply_lock():
                    lockWindowSize(window, width, height)
                    window.adjustSize()
                    centerWindow(window)

                QTimer.singleShot(0, apply_lock)
            except ValueError:
                print(f"Invalid resolution: {resolution}")

    return resolutionSelect(navigate, parent)