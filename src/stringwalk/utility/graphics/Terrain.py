from PyQt6.QtCore import Qt
from PyQt6.QtGui import QLinearGradient, QColor, QPixmap, QBrush
from ..data.projectNameHandler import getProjectDir
import math
import random


SCALE = 1
BASE_RENDER_DISTANCE = 5
WORLD_HEIGHT = 20

def get_terrain_height(x):
    return WORLD_HEIGHT

class Terrain:
    def __init__(self, player, game_widget):
        self.game_widget = game_widget
        self.player = player
        
        self.chunks = {}
        self.column_heights = {}
        self.render_distance = BASE_RENDER_DISTANCE

        self.base_chunk_size = 16
        self.base_tile_size = 64

        self.chunk_size = self.base_chunk_size
        self.tile_size = self.base_tile_size

        self.chunk_world_width = self.chunk_size * self.tile_size

        self.world_height = WORLD_HEIGHT

        self.dirt_pixmap = QPixmap(f"{getProjectDir()}/assets/sprites/dirt.png").scaled(
            self.tile_size,
            self.tile_size,
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.FastTransformation
        )
        self.dirt_brush = QBrush(self.dirt_pixmap)

        print(f"Chunk size: {self.chunk_size}, Tile size: {self.tile_size}, Render distance: {self.render_distance}")

        self.y_standard = 10

    def pos_to_chunk_pos(self, pos):
        return int(pos // self.base_chunk_size)
    
    def chunk_rendered(self, chunk_x):
        if isinstance(chunk_x, list):
            return False

        player_chunk = self.pos_to_chunk_pos(self.player.x)
        return abs(chunk_x - player_chunk) <= self.render_distance
    
    def update_chunks(self, painter):
        player_chunk = self.world_to_chunk(self.player.x)

        for chunk_x in range(player_chunk - self.render_distance, player_chunk + self.render_distance + 1):
            tiles = self.chunks.get(chunk_x)
            if not tiles:
                continue

            for world_x, surface_y in tiles.items():
                screen_x = world_x - self.game_widget.camera.x
                screen_y = surface_y - self.game_widget.camera.y

                fill_height = int((self.world_height * self.tile_size) - surface_y)

                if fill_height > 0:
                    painter.setBrushOrigin(int(screen_x), int(screen_y))

                    painter.fillRect(
                        int(screen_x),
                        int(screen_y),
                        self.tile_size,
                        fill_height,
                        self.dirt_brush
                    )

    def is_solid_at(self, x, y):
        return y >= self.get_surface_y(x)

    def get_ground_y(self, x):
        return get_ground_height(x)

    def get_surface_y(self, world_x):
        world_x = int(world_x)
        chunk_x = self.world_to_chunk(world_x)
        chunk = self.chunks.get(chunk_x)

        if chunk and world_x in chunk:
            return chunk[world_x]

        return get_chunk_height(world_x)

    def get_tile(self, world_x, world_y):
        return "dirt" if world_y >= self.get_surface_y(world_x) else "sky"

    def store_seed(self, seed, chunk_x):
        self.seed = seed

    def world_to_chunk(self, x):
        return int(x // self.chunk_world_width)

    def chunk_to_world_x(self, chunk_x):
        return chunk_x * self.chunk_world_width

    def add_chunk(self, chunk_x):
        if chunk_x in self.chunks:
            return

        chunk = {}
        world_chunk_start_x = chunk_x * self.chunk_world_width

        for x in range(self.chunk_size):
            world_x = world_chunk_start_x + x * self.tile_size
            surface_y = get_chunk_height(world_x)
            chunk[world_x] = surface_y
            self.column_heights[world_x] = surface_y

        self.chunks[chunk_x] = chunk

    def check_collision(self, entity):
        entity.is_on_ground = False

        surface_y = max(
            self.get_surface_y(entity.x),
            self.get_surface_y(entity.x + entity.width / 2),
            self.get_surface_y(entity.x + entity.width - 1),
        )

        if entity.y + entity.height >= surface_y:
            entity.y = surface_y - entity.height
            if entity.velocity_y > 0:
                entity.velocity_y = 0
            entity.is_on_ground = True

def get_ground_height(x):
    return get_chunk_height(x)

def get_chunk_height(chunk_x):
    return random.Random(chunk_x).randint(0, 0)