from PyQt6.QtWidgets import QComboBox, QPushButton
from PyQt6.QtCore import Qt, QTimer
import asyncio
from ...utility.ui.asyncWidget import AsyncWidget
from ...utility.ui.menuHandler import makeMenuLayout, addMenuWidget, finalizeMenuLayout
from ...utility.configHandler import readConfigItem, writeConfigItem
from ...utility.data.textHandler import getText
#from ...utility.ui.resolutionHandler import getFps
from ...utility.data.projectNameHandler import getProjectNameLower


def createfpsSelect(navigate, parent=None, background=None) -> QWidget:
    class fpsSelect(AsyncWidget):
        def __init__(self, navigate, parent=None):
            super().__init__(parent)
            self.navigate = navigate
            self.parent_window = parent
            self.background = background
            self.valid_fps = True

            # Layout
            outer, inner = makeMenuLayout()
            self.layout_ref = inner
            self.setLayout(outer)

            self.run_task(self._load_framerates(), self._fps_loaded)

        async def _load_framerates(self):
            # Read all valid framerates from config
            try:
                framerates = await readConfigItem("framerates", default=[60])
            except Exception:
                framerates = [60]

            current_fps = await readConfigItem("current_fps", default=60)
            return framerates, current_fps

        def _fps_loaded(self, task):
            try:
                fps, current_fps = task.result()  # <-- unpack the tuple correctly
            except Exception:
                fps = [60]
                current_fps = 60

            # Convert framerates to strings if needed
            self.framerates = []
            for r in fps:
                if isinstance(r, (list, tuple)):
                    self.framerates.append()
                else:
                    self.framerates.append(str(r))

            # Save current framerate
            self.current_fps = str(current_fps) if current_fps else self.framerates[0]

            self._reload_texts()

        def _reload_texts(self):
            """Rebuild texts for back button and dropdown."""
            self.run_task(getText("back"), self._build_layout)

        def _build_layout(self, task):
            try:
                back_text = task.result()
            except Exception:
                back_text = "Back"

            # Preserve previous selection if dropdown exists
            if hasattr(self, "fps_dropdown") and self.fps_dropdown is not None:
                selected_internal = self.reverse_map.get(
                    self.fps_dropdown.currentText(),
                    self.fps_dropdown.currentText()
                )
            else:
                selected_internal = getattr(self, "current_fps", "60")

            # Clear layout
            for i in reversed(range(self.layout_ref.count())):
                item = self.layout_ref.itemAt(i)
                widget = item.widget()
                if widget:
                    widget.setParent(None)

            # Convert list/tuple framerates to strings if needed
            fps_strings = []
            for r in self.framerates:
                if isinstance(r, (list, tuple)):
                    fps_strings.append(f"{r[0]}x{r[1]}")
                else:
                    fps_strings.append(str(r))

            # Build internal/display maps
            self.display_map = {r: r for r in self.framerates}
            self.reverse_map = {v: k for k, v in self.display_map.items()}

            # Dropdown
            self.fps_dropdown = QComboBox()
            self.fps_dropdown.setProperty("variant", "setting")
            self.fps_dropdown.setEditable(True)
            self.fps_dropdown.lineEdit().setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.fps_dropdown.lineEdit().textEdited.connect(self._validate_fps)

            for r in self.framerates:
                self.fps_dropdown.addItem(self.display_map.get(r, r))

            self.fps_dropdown.setCurrentText(self.display_map.get(selected_internal, selected_internal))

            self.fps_dropdown.currentTextChanged.connect(
                lambda val: asyncio.create_task(self.setFpsAndReload(val))
            )

            addMenuWidget(self.layout_ref, self.fps_dropdown)

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

        def _validate_fps(self, text):
            # Only validate numeric FPS values
            if "x" not in text.lower():
                self._set_invalid()
                return
            try:
                fps = int(text.lower())
            except ValueError:
                self._set_invalid()
                return
            if fps < 5:
                self._set_invalid()
            else:
                self._set_valid()

        def _set_invalid(self):
            self.valid_fps = False
            line = self.fps_dropdown
            line.setStyleSheet("color: darkred;")

        def _set_valid(self):
            self.valid_fps = True
            line = self.fps_dropdown
            line.setStyleSheet("color: white;")

        async def setFpsAndReload(self, display_value):
            if not self.valid_fps:
                print("FPS invalid — not applying")
                return

            # Convert display - internal key
            fps = self.reverse_map.get(display_value, display_value)
            await writeConfigItem("current_fps", fps)

            window = self.nativeParentWidget()
            if not window:
                return

            try:
                fps = int(fps)
                window.showNormal()

                async def apply_fps():
                    await writeConfigItem("current_fps", fps)

                QTimer.singleShot(0, lambda: asyncio.create_task(apply_fps()))
            except ValueError:
                print(f"Invalid fps: {fps}")

    return fpsSelect(navigate, parent)