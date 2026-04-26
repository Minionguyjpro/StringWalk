from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor


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

    def update(self, painter):
        if self.tile_id == "sky_tile":
            return

        painter.fillRect(
            self.x - self.game_widget.camera.x,
            self.y - self.game_widget.camera.y,
            self.width,
            self.height,
            self.color
        )

    def collide_x(self, player):
        if not self.properties.get("solid", False):
            return False
        
        if player.y > self.y + self.height or player.y + player.height < self.y:
            return False

        if player.x + player.width > self.x and player.x < self.x + self.width:
            if player.facing == "left":
                player.x = self.x - player.width
                return True
            elif player.facing == "right":
                player.x = self.x + self.width
                return True
            return False
        return False

    def collide_y(self, player):
        if player.y + player.height < self.y or not self.properties.get("solid", False):
            return False

        if player.x > self.x + self.width or player.x + player.width < self.x:
            return False

        player.y = self.y - player.height
        player.velocity_y = 0

        self.game_widget.is_on_ground = True