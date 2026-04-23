from ..ui.resolutionHandler import getWidth, getHeight
import asyncio


class Camera:
    def __init__(self, game_widget):
        from ...gui.gameWidget import player

        self.game_widget = game_widget
        self.x = 0.0
        self.y = 0.0
        self.offset = [0.0, 0.0] # Offset for smooth camera movement
        self.last_offsets = []
        self.offset_delay = 5 # Number of frames to delay the offset
        self.margin = 180.0 # Margin to keep around the player
        self.top_margin = 150.0 # Margin to keep above the player

        self.player = player
        
        self.width = 0
        self.height = 0

        self.initialized = False
        
    def update(self):
        asyncio.create_task(self._load_dimensions())
        self._update_camera()

    def _update_world_offset(self):
        max_offset = max(0, self.game_widget.level_width - self.game_widget.width())
        self.world_offset_x = max(0, min(self.world_offset_x, max_offset))

    def _calculate_offset(self):
        self.last_offsets.append((
            self.width / 2,
            self.height / 2
        ))

        if len(self.last_offsets) > self.offset_delay:
            self.offset = self.last_offsets[0]
            self.last_offsets.pop(0)

    async def _load_dimensions(self):
        self.width = await getWidth()
        self.height = await getHeight()

    def _update_camera(self):
        if not self.initialized and self.width > 0:
            self.x = self.player.x - self.width / 2 + self.player.width / 2
            self.y = self.player.y - self.height / 2 + self.player.height / 2
            self.initialized = True
            return

        screen_center = self.x + self.width / 2
        player_center = self.player.x + self.player.width / 2

        diff = player_center - screen_center

        target_x = self.x

        if diff > self.margin:
            target_x += diff - self.margin
        elif diff < -self.margin:
            target_x += diff + self.margin
        
        self.x += (target_x - self.x) * 0.1

        target_y = self.player.y - self.height / 2
        self.y += (target_y - self.y) * 0.1