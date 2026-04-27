from ..utility.ui.asyncWidget import AsyncWidget
from ..utility.ui.menuHandler import makeMenuLayout, addMenuWidget
from ..utility.audio.soundHandler import stopSound
from ..utility.data.textHandler import getText
from ..utility.graphics.screenHandler import captureWidget
from ..utility.configHandler import readConfigItem
from ..utility.io.keyManager import load_bindings
from ..utility.graphics.Camera import Camera
from ..utility.graphics.Terrain import Terrain
#from ..utility.ui.Overlay import Overlay
from ..utility.gameHandler import generate_platform
from PyQt6.QtGui import QPainter, QColor, QKeyEvent, QPen, QLinearGradient, QPixmap
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QLabel
from dataclasses import dataclass, field
import time
import asyncio
import random


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

player = Player()

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

        self.player = player
        self.camera = Camera(self)
        self.terrain = Terrain(player=self.player, game_widget=self)

        self.border_color = QColor("black")
        self.border_size = 0

        self.gradient = QLinearGradient(0, 0, self.width(), self.height())
        self.gradient.setColorAt(0, QColor("#1e1e1e"))
        self.gradient.setColorAt(1, QColor("#000080"))

        self.floor_segments = []

        self.platforms = []

        # Physics
        self.gravity = 0.25
        self.jump_velocity = -14.0
        self.is_on_ground = True

        self.world_offset_x = 0

        self.LEFT_KEYS = [Qt.Key.Key_A, Qt.Key.Key_Left]
        self.RIGHT_KEYS = [Qt.Key.Key_D, Qt.Key.Key_Right]
        self.JUMP_KEYS = [Qt.Key.Key_Space]
        self.DOWN_KEYS = [Qt.Key.Key_S]
        self.BORDER_RELEASE_KEYS = [Qt.Key.Key_Space, Qt.Key.Key_Shift]
        self.bindings = {
            "jump": "Space",
            "move_left": "A",
            "move_right": "D",
            "pause": "Escape",
        }

        self.last_time = time.perf_counter()
        self.frame_count = 0
        self.fps_accumulated = 0

        self.target_fps = 60

        self.update_interval = int(1000 / self.target_fps)  # Update interval in milliseconds for the timer

        # Timer to update the game (60 FPS)
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self.timer.start(self.update_interval)

        self.bg_sheet = QPixmap("../assets/sprites/sprinkling_power.png")

        # Currently pressed keys
        self.keys_pressed = set()

        #self.overlay = Overlay()

        self.debug_labels = []

        for i, name in enumerate(["fps", "latency"]):
            label = QLabel(None, self)
            label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            label.move(10, 10 + i * 20)
            self.debug_labels.append(label)

        self.fps_text = "FPS"
        self.latency_text = "Latency"

        asyncio.create_task(self._load_bindings()   )
        asyncio.create_task(self._load_debug_label_texts())
        asyncio.create_task(self._apply_settings())

    def get_qt_key(self, key_name: str, fallback):
        if not key_name:
            return fallback

        normalized = str(key_name).strip()

        if normalized.isdigit():
            try:
                return Qt.Key(int(normalized))
            except ValueError:
                return fallback

        special_keys = {
            "SPACE": "Key_Space",
            "ESCAPE": "Key_Escape",
            "SHIFT": "Key_Shift",
            "CTRL": "Key_Control",
            "CONTROL": "Key_Control",
            "ALT": "Key_Alt",
            "TAB": "Key_Tab",
            "ENTER": "Key_Return",
            "RETURN": "Key_Return",
            "BACKSPACE": "Key_Backspace",
            "LEFT": "Key_Left",
            "RIGHT": "Key_Right",
            "UP": "Key_Up",
            "DOWN": "Key_Down",
            "DELETE": "Key_Delete",
            "INSERT": "Key_Insert",
            "HOME": "Key_Home",
            "END": "Key_End",
            "PAGEUP": "Key_PageUp",
            "PAGEDOWN": "Key_PageDown",
        }

        special_attr = special_keys.get(normalized.upper())
        if special_attr and hasattr(Qt.Key, special_attr):
            return getattr(Qt.Key, special_attr)

        candidates = [
            f"Key_{normalized}",
            f"Key_{normalized.title()}",
            f"Key_{normalized.upper()}",
        ]

        for qt_attr in candidates:
            if hasattr(Qt.Key, qt_attr):
                return getattr(Qt.Key, qt_attr)

        return fallback

    def apply_bindings(self):
        # Keys that can trigger left movement
        self.LEFT_KEYS = [
            self.get_qt_key(self.bindings.get("move_left"), "A"),
            Qt.Key.Key_Left
        ]

        # Keys that can trigger right movement
        self.RIGHT_KEYS = [
            self.get_qt_key(self.bindings.get("move_right"), "D"),
            Qt.Key.Key_Right
        ]

        # Keys that can trigger a jump
        self.JUMP_KEYS = [
            self.get_qt_key(self.bindings.get("jump"), "Space")
        ]

        # Keys that can trigger downward movement
        self.DOWN_KEYS = [
            self.get_qt_key(self.bindings.get("down"), "S"),
            Qt.Key.Key_S
        ]
        
        self.BORDER_RELEASE_KEYS = self.JUMP_KEYS + [Qt.Key.Key_Shift]

    def showEvent(self, event):
        super().showEvent(event)

        # self._update_world_size()

        # Ensure the widget receives keyboard events immediately.
        QTimer.singleShot(0, self._force_focus)

    def _force_focus(self):
        self.raise_()
        self.activateWindow()
        self.setFocus()

    def paintEvent(self, event):
        for x in range(-self.terrain.render_distance, self.terrain.render_distance):
            nx = self.player.x + x * self.terrain.chunk_size * self.terrain.tile_size
            self.terrain.add_chunk(nx)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        painter.fillRect(
            0,
            0,
            self.width(),
            self.height(),
            self.gradient
        )

        self.terrain.update_chunks(painter)

        # Draw player block
        player_x = int(round(self.player.x - self.camera.x))
        player_y = int(round(self.player.y - self.camera.y))

        if hasattr(self, "border_color"):
            pen = QPen(self.border_color, self.border_size)
        else:
            pen = QPen(self.player.color.darker(), 4)

        painter.setPen(pen)
        painter.setBrush(self.player.color)
        painter.drawEllipse(
            player_x,
            player_y,
            self.player.width,
            self.player.height
        )

        painter.end()

    def setBorder(self, color, size):
        self.border_color = QColor(color)
        self.border_size = size
        self.update()

    def keyPressEvent(self, event: QKeyEvent):
        # Toggle pause on Escape key
        if event.key() == Qt.Key.Key_Escape:
            if self.is_paused:
                self.resume_game()
            else:
                self.pause_game()
            return

        if event.key() == Qt.Key.Key_R:
            self.player.x = 50
            self.player.y = 300
            self.world_offset_x = 0
            self.camera_y = 0.0

        self.keys_pressed.add(event.key())
        self.update()

    def keyReleaseEvent(self, event: QKeyEvent):
        if event.key() in self.keys_pressed:
            self.keys_pressed.remove(event.key())

        if event.key() in self.BORDER_RELEASE_KEYS:
            self.setBorder("", 0)

        if event.key() == Qt.Key.Key_Shift:
            self.player.speed = 5

    def closeEvent(self, event):
        self.timer.stop()
        if callable(self.on_exit):
            pixmap = captureWidget(self)
            self.on_exit(pixmap)
        super().closeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        self.update()

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

        delta_time = min(delta_time, 0.033)

        if delta_time > 0:
            actual_fps = 1 / delta_time
        
        self.debug_labels[0].setText(f"{self.fps_text}: {int(actual_fps)}")
        self.debug_labels[1].setText(f"{self.latency_text}: {int(delta_time * 1000)} ms")

        for label in self.debug_labels:
            label.adjustSize()

        self.world_offset_x = max(0, self.world_offset_x)

        self.handle_movement(delta_time)
        self.camera.update(delta_time)
        self.update()

    # def _update_world_size(self):
    #     _, floor_height = self.get_floor()
    #     floor_y = self.height() - floor_height

    #     self.player.y = min(self.player.y, floor_y - self.player.height)

    #     max_offset = max(0, (len(self.floor_segments) * self.segment_width) - self.width())
    #     self.world_offset_x = min(self.world_offset_x, max_offset)

    def generate_segment(self):
        return random.choice(self.AVAILABLE_COLORS)

    def handle_movement(self, delta_time=1 / 60):
        # Scale per-frame values so gameplay speed stays consistent across FPS values.
        dt_scale = delta_time * 60

        # if any(key in self.keys_pressed for key in self.DOWN_KEYS):
        #     self.player.y = min(self.player.height, self.player.y + (self.player.speed * dt_scale))

        # Jumping border effect and physics
        if any(key in self.keys_pressed for key in self.JUMP_KEYS) and self.is_on_ground:
            self.player.velocity_y += self.jump_velocity
            self.setBorder("#dddda0", 6)
        else:
            self.setBorder("", 0)

        # Vertical physics
        self.player.velocity_y += self.gravity * dt_scale  # Slightly increase gravity over time for a more dynamic feel
        self.player.velocity_y = min(self.player.velocity_y, 15)  # Terminal velocity to prevent excessive falling speed
        self.player.previous_y = self.player.y  # Store previous Y position for better collision detection
        self.player.y += self.player.velocity_y * dt_scale  # Apply velocity to position, with a small boost for responsiveness

        self.is_on_ground = False 

        for chunk in self.terrain.chunks:
            if not self.terrain.chunk_rendered(chunk):
                continue
            for row in chunk:
                for platform in row:
                    platform.collide_y(self.player)

        self.move_x = 0

        # LEFT movement
        if any(key in self.keys_pressed for key in self.LEFT_KEYS):
            self.player.facing = "left"
            self.move_x -= self.player.speed

        # RIGHT movement
        if any(key in self.keys_pressed for key in self.RIGHT_KEYS):
            self.player.facing = "right"
            self.move_x += self.player.speed

        self.player.x += self.move_x * dt_scale
 
        for chunk in self.terrain.chunks:
            if not self.terrain.chunk_rendered(chunk):
                continue
            for row in chunk:
                for platform in row:
                    if platform.collide_x(self.player):
                        break

        if Qt.Key.Key_Shift in self.keys_pressed:
            self.setBorder("gray", 4)
        
        if Qt.Key.Key_Shift in self.keys_pressed:
            self.player.speed = 10
        else:
            self.player.speed = 5

    def resume_game(self):
        if not self.is_paused:
            return

        self.is_paused = False

        stopSound()  # Stop any music that might be playing in the menu

        self.last_time = time.perf_counter()
        
        if not self.timer.isActive():
            self.timer.start(self.update_interval)

        self.setFocus()

        asyncio.create_task(self._load_bindings())  # Reload bindings in case they were changed in the menu
        asyncio.create_task(self._load_debug_label_texts())  # Reload debug label texts in case they were changed in the menu
        asyncio.create_task(self._apply_settings())  # Re-apply settings in case they were changed in the menu

    async def _load_bindings(self):
        self.bindings = await load_bindings()
        self.apply_bindings()

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