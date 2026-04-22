from ..ui.resolutionHandler import getWidth, getHeight
import asyncio


class Camera:
    def __init__(self, game_widget):
        from ...gui.gameWidget import player

        self.game_widget = game_widget
        self.x = 0.0
        self.y = 0.0
        self.top_margin = 150.0  # How far from the top of the screen the player can go before the camera starts moving
        self.camera_top_margin = 80.0  # A smaller margin used for smoother camera movement

        self.player = player
        
        self.width = 0
        self.height = 0
        
    def update(self):
        asyncio.create_task(self._load_dimensions())
        self._update_camera()

    def _update_world_offset(self):
        max_offset = max(0, self.game_widget.level_width - self.game_widget.width())
        self.world_offset_x = max(0, min(self.world_offset_x, max_offset))

    async def _load_dimensions(self):
        self.width = await getWidth()
        self.height = await getHeight()

    def _update_camera(self):
        self.x = self.player.x - self.width / 2 + self.player.width / 2
        self.y = self.player.y - self.height / 2 + self.player.height / 2