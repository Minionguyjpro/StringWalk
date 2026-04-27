from PyQt6.QtGui import QPixmap
from dataclasses import dataclass


class Entity:
    def __init__(self, x, y, width, height, image_path, game_widget):
        self.x = x
        self.y = y
        self.name = "Entity"
        self.width = width
        self.height = height
        self.velocity_x = 0
        self.velocity_y = 0
        self.image = QPixmap(image_path)
        self.is_on_ground = True
        self.game_widget = game_widget

    def update(self, painter):
        painter.drawPixmap(
            int(self.x - self.game_widget.camera.x),
            int(self.y - self.game_widget.camera.y),
            self.width,
            self.height,
            self.image
        )