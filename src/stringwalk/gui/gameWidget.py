from ..utility.ui.asyncWidget import AsyncWidget
from ..utility.ui.menuHandler import makeMenuLayout, addMenuWidget
from ..utility.audio.soundHandler import stopSound
from ..utility.data.textHandler import getText
from ..utility.graphics.screenHandler import captureWidget
from ..utility.configHandler import readConfigItem
from PyQt6.QtGui import QPainter, QColor, QKeyEvent, QPen
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QLabel
import time
import asyncio
import random

class GameWidget(AsyncWidget):
    def __init__(self, parent=None, on_exit=None):
        super().__init__(parent)
        self.on_exit = on_exit
        self.setWindowTitle("Simple Game")
        self.setMinimumSize(600, 400)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        stopSound()  # Stop any music from the main menu when entering the game

        # Game state
        self.is_paused = False

        # Player block properties
        self.player_x = 50
        self.player_y = 300
        self.player_width = 50
        self.player_height = 50
        self.player_color = QColor("red")
        self.speed = 5

        self.border_color = QColor("black")
        self.border_size = 0

        # Floor
        self.floor_height = 80
        self.segment_width = 50

        self.AVAILABLE_COLORS = [
            "darkgreen",
            "green",
            "forestgreen",
            "limegreen",
            "seagreen",
            "mediumseagreen",
            "springgreen",
            "mediumspringgreen",
            "lightgreen",
            "palegreen"
        ]

        self.floor_segments = [random.choice(self.AVAILABLE_COLORS) for _ in range(100)] 

        self.floor_y = self.height() - self.floor_height

        # Physics
        self.gravity = 1.0
        self.jump_velocity = -14.0
        self.velocity_y = 1.0
        self.is_on_ground = True

        self.world_offset_x = 0

        self.camera_margin = 80

        # Keys that can trigger left movement
        self.LEFT_KEYS = [
            Qt.Key.Key_Left,
            Qt.Key.Key_A
        ]

        # Keys that can trigger right movement
        self.RIGHT_KEYS = [
            Qt.Key.Key_Right,
            Qt.Key.Key_D
        ]

        # Keys that can trigger a jump
        self.JUMP_KEYS = [
            Qt.Key.Key_Up,
            Qt.Key.Key_W,
            Qt.Key.Key_Space
        ]

        # Keys that can trigger downward movement
        self.DOWN_KEYS = [
            Qt.Key.Key_Down,
            Qt.Key.Key_S
        ]
        
        self.BORDER_RELEASE_KEYS = self.JUMP_KEYS + [Qt.Key.Key_Shift]

        self.last_time = time.perf_counter()
        self.frame_count = 0
        self.fps_accumulated = 0

        self.target_fps = 60

        self.update_interval = int(1000 / self.target_fps)  # Update interval in milliseconds for the timer

        # Timer to update the game (60 FPS)
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self.timer.start(self.update_interval)

        # Currently pressed keys
        self.keys_pressed = set()

        self.debug_labels = []

        for i, name in enumerate(["fps", "latency"]):
            label = QLabel(None, self)
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            label.move(10, 10 + i * 20)
            self.debug_labels.append(label)

        self.fps_text = "FPS"
        self.latency_text = "Latency"

        asyncio.create_task(self._load_debug_label_texts())
        asyncio.create_task(self._apply_settings())

    def showEvent(self, event):
        super().showEvent(event)
        # Ensure the widget receives keyboard events immediately.
        QTimer.singleShot(0, self._force_focus)
        
    def _force_focus(self):
        self.raise_()
        self.activateWindow()
        self.setFocus()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        painter.fillRect(event.rect(), QColor("#1e1e1e"))
        
        # Draw floor segments
        floor_y = int(round(self.floor_y))
        for i, color_name in enumerate(self.floor_segments):
            x_pos = i * self.segment_width - self.world_offset_x
            if x_pos > self.width():
                break
            if x_pos + self.segment_width < 0:
                continue
                
            painter.fillRect(
                int(x_pos),
                floor_y,
                self.segment_width,
                self.floor_height,
                QColor(color_name)
            )

        # Draw player block
        player_x = int(round(self.player_x))
        player_y = int(round(self.player_y))

        if hasattr(self, "border_color"):
            pen = QPen(self.border_color, self.border_size)
        else:
            pen = QPen(self.player_color.darker(), 4)

        painter.setPen(pen)
        painter.setBrush(self.player_color)
        painter.drawEllipse(
            player_x,
            player_y,
            self.player_width,
            self.player_height,
        )

        painter.end()

    def setBorder(self, color, size):
        self.border_color = QColor(color)
        self.border_size = size
        self.update()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            if self.is_paused:
                self.resume_game()
            else:
                self.pause_game()
            return
        
        if event.key() in self.JUMP_KEYS and self.is_on_ground:
            self.velocity_y = self.jump_velocity
            self.is_on_ground = False
            self.setBorder("yellow", 6)

        if event.key() == Qt.Key.Key_Shift:
            self.speed = 10
            self.setBorder("gray", 4)
    
        self.keys_pressed.add(event.key())
        self.handle_movement()
        self.update()

    def keyReleaseEvent(self, event: QKeyEvent):
        if event.key() in self.keys_pressed:
            self.keys_pressed.remove(event.key())

        if event.key() in self.BORDER_RELEASE_KEYS:
            self.setBorder("", 0)

        if event.key() == Qt.Key.Key_Shift:
            self.speed = 5

    def closeEvent(self, event):
        self.timer.stop()
        if callable(self.on_exit):
            pixmap = captureWidget(self)
            self.on_exit(pixmap)
        super().closeEvent(event)

    def pause_game(self):
        if self.is_paused:
            return

        self.is_paused = True
        self.timer.stop()

        pixmap = captureWidget(self)

        self.last_time = time.perf_counter()  # Reset time to avoid large delta when resuming

        self.hide()

        self.on_exit(pixmap)

    def _tick(self):
        current_time = time.perf_counter()
        delta_time = current_time - self.last_time
        self.last_time = current_time

        if delta_time > 0:
            actual_fps = 1 / delta_time

            self.debug_labels[0].setText(f"{self.fps_text}: {int(actual_fps)}")
            self.debug_labels[1].setText(f"{self.latency_text}: {int(delta_time * 1000)} ms")

            for label in self.debug_labels:
                label.adjustSize()

        visible_segments = int(self.width() / self.segment_width) + 2

        current_max_segment = len(self.floor_segments)

        needed_segments = int((self.world_offset_x / self.segment_width) + visible_segments) + 1

        while current_max_segment < needed_segments:
            self.floor_segments.append(self.generate_segment())
            current_max_segment += 1

        self.handle_movement(delta_time)
        self.update()

    def generate_segment(self):
        return random.choice(self.AVAILABLE_COLORS)

    def handle_movement(self, delta_time=1 / 60):
        # Scale per-frame values so gameplay speed stays consistent across FPS values.
        dt_scale = delta_time * 60

        # LEFT movement
        if any(key in self.keys_pressed for key in self.LEFT_KEYS):
            if self.player_x > self.camera_margin:
                # Move player normally
                self.player_x -= self.speed * dt_scale
            else:
                # Move world
                self.world_offset_x = max(0, self.world_offset_x - (self.speed * dt_scale))

        # RIGHT movement
        if any(key in self.keys_pressed for key in self.RIGHT_KEYS):
            if self.player_x < self.width() - self.camera_margin - self.player_width:
                # Move player normally
                self.player_x += self.speed * dt_scale
            else:
                # Move world
                self.world_offset_x += self.speed * dt_scale
 
        if any(key in self.keys_pressed for key in self.JUMP_KEYS):
            self.player_y = max(0, self.player_y - (self.speed * dt_scale))
        if any(key in self.keys_pressed for key in self.DOWN_KEYS):
            self.player_y = min(self.floor_y - self.player_height, self.player_y + (self.speed * dt_scale))

        # Vertical physics
        self.velocity_y += self.gravity * dt_scale
        self.player_y += self.velocity_y * dt_scale

        ground_top = self.floor_y - self.player_height
        if self.player_y >= ground_top:
            self.player_y = ground_top
            self.velocity_y = 0
            self.is_on_ground = True

    def resume_game(self):
        if not self.is_paused:
            return

        self.is_paused = False

        stopSound()  # Stop any music that might be playing in the menu

        self.last_time = time.perf_counter()
        
        if not self.timer.isActive():
            self.timer.start(self.update_interval)

        self.setFocus()

        asyncio.create_task(self._apply_settings())  # Re-apply settings in case they were changed in the menu

    async def _load_debug_label_texts(self):
        try:
            self.fps_text = await getText("fps")
            self.latency_text = await getText("latency")
        except Exception as e:
            print(f"Error loading debug label texts: {e}")
    
    async def _apply_settings(self):
        try:
            config_fps_str = await readConfigItem("current_fps")
            print(config_fps_str)
            config_fps = int(config_fps_str)

            if config_fps > 0:
                self.target_fps = config_fps
                self.update_interval = int(1000 / self.target_fps)
                
                self.timer.start(self.update_interval)
                print(f"FPS adjusted to: {self.target_fps} (interval: {self.update_interval} ms)")
        except Exception as e:
            print(f"Error applying settings: {e}")