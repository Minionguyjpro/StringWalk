from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor


class Platform:
    def __init__(self, x, y, width, height, color, game_widget):
        self.x = int(x)
        self.y = int(y)
        self.width = width + 1
        self.height = height
        self.color = QColor(color) if isinstance(color, str) else color
        self.game_widget = game_widget

    def update(self, painter):
        painter.fillRect(
            self.x - self.game_widget.camera.x,
            self.y - self.game_widget.camera.y,
            self.width,
            self.height,
            self.color
        )
