from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QPixmap
from ..data.projectNameHandler import getProjectDir


class Platform:
    def __init__(self, tile_id, x, y, width, height, color, game_widget, **properties):
        self.tile_id = tile_id
        self.x = int(x)
        self.y = int(y)
        self.width = width + 1
        self.height = height
        self.color = QColor(color) if isinstance(color, str) else color
        self.game_widget = game_widget
        self.properties = properties
        
        project_dir = getProjectDir()
        image_path = f"{project_dir}/assets/sprites/{tile_id}.png"

        if self.tile_id == "sky":
            return

    def update(self, painter):
        painter.fillRect(
            self.x - self.game_widget.camera.x,
            self.y - self.game_widget.camera.y,
            self.width,
            self.height,
            self.color
        )

    def collide_x(self, entity):
        if not self.properties.get("solid", False):
            return False
        
        if entity.y + entity.height <= self.y or entity.y >= self.y + self.height:
            return False

        if entity.x + entity.width <= self.x or entity.x >= self.x + self.width:
            return False

        if entity.velocity_x < 0:
            entity.x = self.x + self.width
        elif entity.velocity_x > 0:
            entity.x = self.x - entity.width

        entity.velocity_x = 0
        return True

    def collide_y(self, entity):
        if not self.properties.get("solid", False):
            return False

        if entity.x >= self.x + self.width or entity.x + entity.width <= self.x:
            return False

        if entity.velocity_y <= 0:
            return False

        if entity.previous_y + entity.height <= self.y and entity.y + entity.height >= self.y:
            entity.y = self.y - entity.height
            entity.velocity_y = 0
            entity.is_on_ground = True
            return True

        return False