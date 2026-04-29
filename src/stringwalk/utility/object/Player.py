from PyQt6.QtGui import QColor
from dataclasses import dataclass, field


@dataclass
class Player:
    x: int = 50
    y: int = 300
    width: int = 50
    height: int = 50
    color: QColor = field(default_factory=lambda: QColor("red"))
    speed: int = 5
    velocity_x: int = 0
    velocity_y: int = 0
    facing: str = "right"
    is_on_ground: bool = True
    mass: float = 1.0