from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter

class BackgroundWidget(QWidget):
    def __init__(self, *args, background=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.background = background

    def setBackground(self, pixmap):
        self.background = pixmap
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)

        if self.background:
            painter.drawPixmap(0, 0, self.background)

        super().paintEvent(event)