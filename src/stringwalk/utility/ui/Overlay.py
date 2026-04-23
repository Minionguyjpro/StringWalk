from dataclasses import dataclass, field
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel


@dataclass
class Overlay:
    duration: int
    start_time: float
    debug_labels: list = field(default_factory=list)
    texts: list = field(default_factory=list)

def is_active(self, current_time):
        return current_time - self.start_time < self.duration

def create_debug_label(self, i):
    self.texts = [
         "fps",
         "latency"
    ]

    for i, name in enumerate([self.texts[i] for i in range(len(self.texts))]):
        label = QLabel(None)
        label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        label.move(10, 10 + i * 20)
        self.debug_labels.append(label)

overlay = Overlay()