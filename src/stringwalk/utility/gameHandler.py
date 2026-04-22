from PyQt6.QtGui import QColor
import random


def generate_platform(self, floor_y, AVAILABLE_COLORS, x_start):
    return {
        "x": x_start + random.randint(0, 200),
        "y": random.randint(150, floor_y - 100),
        "width": random.randint(80, 180),
        "height": 20,
        "color": QColor(random.choice(AVAILABLE_COLORS))
    }