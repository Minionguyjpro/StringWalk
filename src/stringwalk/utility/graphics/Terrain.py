from PyQt6.QtGui import QLinearGradient, QColor
from .Platform import Platform
import random


SCALE = 0.05

def get_terrain_height(x):
    return int(20 * (1 + math.sin(x / 100))) + 50

class Terrain:
    def __init__(self, player, game_widget):
        self.game_widget = game_widget
        self.chunks = []
        self.chunks_posses = []
        self.chunk_size = 16
        self.render_distance = 30
        self.world_height = 40
        self.tile_size = 64
        self.y_standard = 10

        self.player = player    

    def pos_to_chunk_pos(self, pos):
        return pos // self.chunk_size // self.tile_size
    
    def chunk_rendered(self, chunk):
        chunk_x = chunk[0][0].x
        return chunk_x + (self.render_distance * self.tile_size) > self.player.x and chunk_x - (self.render_distance * self.tile_size) < self.game_widget.camera.x
    
    def update_chunks(self, painter):
        for chunk in self.chunks:
            if self.chunk_rendered(chunk):
                for row in chunk:
                    for platform in row:
                        platform.update(painter)

    def add_chunk(self, x_pos):
        chunk_x = self.pos_to_chunk_pos(x_pos)
        
        if chunk_x in self.chunks_posses:
            return
        
        chunk = []
        self.y_standard = random.randint(9, 11)
        for x in range(self.chunk_size):
            row = []
            for y in range(-self.world_height, self.world_height + 1):
                if y < self.y_standard:
                    row.append(Platform("sky_tile", x * self.tile_size + x_pos, y * self.tile_size, self.tile_size, self.tile_size, "blue", self.game_widget))
                else:
                    row.append(Platform("ground_tile", x * self.tile_size + x_pos, y * self.tile_size, self.tile_size, self.tile_size, "green", self.game_widget, solid=True))
            chunk.append(row)
        self.chunks.append(chunk)
        self.chunks_posses.append(chunk_x)