from ..ui.resolutionHandler import getWidth, getHeight
from ..configHandler import readConfigItem
import asyncio


class Camera:
    def __init__(self, game_widget):
        from ...gui.gameWidget import player

        self.game_widget = game_widget
        self.x = 0
        self.y = 0
        self.offset_delay = 30 / 240 # Number of frames to delay the offset
        self.top_margin = 150.0 # Margin to keep above the player
        self.fps = 60
        
        self.width = 0
        self.height = 0

    @property
    def player(self):
        return self.game_widget.player

    def update(self, delta_time):
        self.width = self.game_widget.width()
        self.height = self.game_widget.height()
        self.fps = self.game_widget.target_fps
        self.offset_delay = 30 * delta_time if self.fps else 30 / 240
        
        self._update_camera(delta_time)

    def _update_world_offset(self):
        max_offset = max(0, self.game_widget.level_width - self.game_widget.width())
        self.world_offset_x = max(0, min(self.world_offset_x, max_offset))

    async def _load_dimensions(self):
        self.width = await getWidth()
        self.height = await getHeight()

    async def _load_fps(self, delta_time):
        self.fps = await readConfigItem("current_fps")
        self.offset_delay = 30 * delta_time if self.fps else 30 / 240

    def _update_camera(self, delta_time):
        target_x = self.player.x - self.width / 2 + self.player.width / 2
        target_y = self.player.y - self.height / 2 + self.player.height / 2

        smooth_speed = 10.0  # higher = snappier camera

        self.x += (target_x - self.x) * min(1, smooth_speed * delta_time)
        self.y += (target_y - self.y) * min(1, smooth_speed * delta_time)