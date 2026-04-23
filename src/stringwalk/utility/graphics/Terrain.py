from dataclasses import dataclass, field
import math


SCALE = 0.05

def get_terrain_height(x):
    return int(20 * (1 + math.sin(x / 100))) + 50

@dataclass
class Terrain:
    player: object
    chunks: list = field(default_factory=list)
    chunks_posses: list = field(default_factory=list)
    chunk_size: int = 64
    render_distance: int = 5
    tile_size = 16

    def __post_init__(self):
        print(int(self.player.x), "X")

    @staticmethod
    def pos_to_chunk_pos(self, pos):
        return int(pos // self.chunk_size) * self.chunk_size
    
    @staticmethod
    def chunk_rendered(self, chunk):
        chunk_x = chunk[0][0].x
        return chunk_x + ( self.render_distance * self.chunk_size * self.tile_size ) > self.player.x and chunk_x - ( self.render_distance * self.chunk_size * self.tile_size ) < self.game_widget.camera.x
    
    def add_chunk(self, x):
        chunk_x = self.pos_to_chunk_pos(x)
        
        if chunk_x in self.chunks_posses:
            return
        
        # chunk = []
        # y_standard = 50
        # for x in range(self.chunk_size):
        #     row = []
        #     for y in range(-20, 20):
                