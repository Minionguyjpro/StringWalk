from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPixmap
import asyncio


class BackgroundWidget(QWidget):
    def __init__(self, *args, background=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.background = background
        self._tasks = []

    def run_task(self, coro, callback) -> asyncio.Task:
        task = asyncio.create_task(coro)
        task.add_done_callback(callback)
        self._tasks.append(task)
        return task

    def setBackground(self, pixmap):
        self.background = pixmap
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)

        if self.background:
            if isinstance(self.background, QPixmap):
                if not self.background.isNull():
                    painter.drawPixmap(self.rect(), self.background)
            elif isinstance(self.background, QWidget):
                # Allow using a live widget (e.g., VideoManager) as a source.
                pixmap = self.background.grab()
                if not pixmap.isNull():
                    painter.drawPixmap(self.rect(), pixmap)

        super().paintEvent(event)