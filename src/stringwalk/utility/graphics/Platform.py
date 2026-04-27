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
        
        if player.y + player.height <= self.y or player.y >= self.y + self.height:
            return False

        if player.x + player.width <= self.x or player.x >= self.x + self.width:
            return False

        if self.game_widget.move_x < 0:
            player.x = self.x + self.width
        elif self.game_widget.move_x > 0:
            player.x = self.x - player.width

        player.velocity_x = 0
        return True

    def collide_y(self, player):
        if not self.properties.get("solid", False):
            return False

        if player.x >= self.x + self.width or player.x + player.width <= self.x:
            return False

        if player.velocity_y <= 0:
            return False

        if player.previous_y + player.height <= self.y and player.y + player.height >= self.y:
            player.y = self.y - player.height
            player.velocity_y = 0
            self.game_widget.is_on_ground = True
            return True

        return False