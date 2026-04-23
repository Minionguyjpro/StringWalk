from ..ui.resolutionHandler import getWidth, getHeight
from ..configHandler import readConfigItem
import asyncio


class Camera:
    def __init__(self, game_widget):
        from ...gui.gameWidget import player

        self.game_widget = game_widget
        self.x = 0
        self.y = 0
        self.offset = [0.0, 0.0] # Offset for smooth camera movement
        self.last_offsets = []
        self.offset_delay = 30 # Number of frames to delay the offset
        self.top_margin = 150.0 # Margin to keep above the player

        self.player = player
        
        self.width = 0
        self.height = 0
        self.fps = 0
        
    def update(self, delta_time):
        asyncio.create_task(self._load_dimensions())
        asyncio.create_task(self._load_fps())
        self._update_camera(delta_time)

    def _update_world_offset(self):
        max_offset = max(0, self.game_widget.level_width - self.game_widget.width())
        self.world_offset_x = max(0, min(self.world_offset_x, max_offset))

    async def _load_dimensions(self):
        self.width = await getWidth()
        self.height = await getHeight()

    async def _load_fps(self):
        self.fps = await readConfigItem("current_fps")

    def _update_camera(self, delta_time):
        self.last_offsets.append((
            self.player.x - self.width / 2 + self.player.width / 2,
            self.player.y - self.height / 2 + self.player.height / 2
        ))
        
        if len(self.last_offsets) > self.offset_delay * self.fps * delta_time:
            self.x = int(self.last_offsets[0][0])
            self.y = int(self.last_offsets[0][1])
            self.last_offsets.pop(0)