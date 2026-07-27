from ..utility.ui.asyncWidget import AsyncWidget
from ..utility.ui.menuHandler import makeMenuLayout, addMenuWidget
from ..utility.audio.soundHandler import stopSound
from ..utility.data.textHandler import getText
from ..utility.data.projectNameHandler import getProjectDir
from ..utility.graphics.screenHandler import captureWidget
from ..utility.configHandler import readConfigItem
from ..utility.io.keyManager import load_bindings
from ..utility.graphics.Camera import Camera
from ..utility.graphics.Terrain import Terrain, get_ground_height
from ..utility.object.Player import Player
from ..utility.object.Entity import Entity
from ..utility.object.objectParser import getObjects
from ..network.lobbyManager import lobby_manager
from ..utility.ui.Overlay import Overlay
from ..utility.gameHandler import generate_platform
from PyQt6.QtGui import QPainter, QColor, QKeyEvent, QPen, QLinearGradient, QPixmap
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QLabel
import time
import asyncio
import random


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

        self.players = []
        self.player = Player()
        self.players.append(self.player)

        self.remote_players = {}

        self.camera = Camera(self)
        self.terrain = Terrain(player=self.player, game_widget=self)
        self.overlay = Overlay(self)

        self.border_color = QColor("black")
        self.border_size = 0

        self.background = QLinearGradient(0, 0, self.width(), self.height())
        self.background.setColorAt(0, QColor("#1e1e1e"))
        self.background.setColorAt(1, QColor("#000080"))

        self.entities = []
        self.platforms = []
        self.project_dir = getProjectDir()
        self.entity_data = getObjects().entities()
        print(f"Loaded entity data: {self.entity_data}")
        
        self.gravity = 0.25
        self.jump_velocity = -14.0

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

        self.texts = {
                "fps": "FPS",
                "latency": "Latency"
        }

        self._loaded_chunk_center = None

        self.network_task = asyncio.create_task(self.network_loop())

        self.init_world()
        self.resolve_spawn_position()
        self.setup_entities()

        lobby_manager.game_widget = self  # Provide reference to this game widget for lobby manager to call update on when receiving data

        asyncio.create_task(self._load_bindings())
        asyncio.create_task(self._load_overlay())
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

    async def _load_overlay(self):
        if await self.overlay.is_enabled():
            self.overlay.register("fps", self.texts["fps"])
            self.overlay.register("latency", self.texts["latency"])

    def showEvent(self, event):
        super().showEvent(event)

        # Ensure the widget receives keyboard events immediately.
        QTimer.singleShot(0, self._force_focus)

    def _force_focus(self):
        self.raise_()
        self.activateWindow()
        self.setFocus()

    def init_world(self):
        player_chunk = self.terrain.world_to_chunk(self.player.x)

        if self._loaded_chunk_center == player_chunk:
            return

        self._loaded_chunk_center = player_chunk

        for cx in range(player_chunk - self.terrain.render_distance,
                        player_chunk + self.terrain.render_distance + 1):
            self.terrain.add_chunk(cx)

    def resolve_spawn_position(self):
        x = self.player.x

        for y in range(-200, 200):
            if self.terrain.is_solid_at(x, y):
                self.player.y = self.terrain.get_surface_y(x) - self.player.height
                self.player.is_on_ground = False
                return

    def paintEvent(self, event):

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)

        # Paint background gradient
        painter.fillRect(
            0,
            0,
            self.width(),
            self.height(),
            self.background
        )

        self.entities = [e for e in self.entities if e.type not in ["local_player", "remote_player"]]

        self.terrain.update_chunks(painter)

        for p in self.players:
            obj = self.build_entity(
                key="local_player",
                data={
                    "icon": "face_smile.png",
                    "animated": False,
                    "properties": {
                        "mass": 0.8
                    }
                },
                x=(p.x),
                y=(p.y),
                width=p.width,
                height=p.height,
                entity_type="local_player"
            )
            self.entities.append(obj)
            print(f"Drawing local player at ({p.x}, {p.y}) with screen position ({p.x}, {p.y})")

        for p in self.remote_players.values():
            obj = self.build_entity(
                key="remote_player",
                data={
                    "icon": "face_smile.png",
                    "animated": False,
                    "properties": {
                        "mass": 0.8
                    }
                },
                x=(p.x),
                y=(p.y),
                width=p.width,
                height=p.height,
                entity_type="remote_player"
            )
            self.entities.append(obj)
            print(f"Drawing remote player at ({p.x}, {p.y}) with screen position ({p.x}, {p.y})")

        for entity in self.entities:
            entity.update(painter)

        # Draw player block
        player_x = int(round(self.player.x - self.camera.x))
        player_y = int(round(self.player.y - self.camera.y))

        if hasattr(self, "border_color"):
            pen = QPen(self.border_color, self.border_size)
        else:
            pen = QPen(self.player.color.darker(), 4)
        painter.setPen(pen)

    def build_entity(self, key, data, x, y, width=64, height=64, entity_type=None):
        props = data.get("properties", {})

        return Entity(
            x=x,
            y=y,
            width=width,
            height=height,
            image_path=f"{self.project_dir}/assets/sprites/{data['icon']}",
            animated=data.get("animated", False),
            game_widget=self,
            mass=props.get("mass"),
            quantity=props.get("quantity"),
            data=data,
            type=entity_type
        )

    def setup_entities(self):
        for key, data in self.entity_data.items():
            quantity = data.get("quantity", 1)

            for _ in range(quantity):
                range_x = data.get("spawn_range_x", [0, 5000])
                range_y = data.get("spawn_range_y", [0, 5000])

                random_x = random.randint(range_x[0], range_x[1])

                if isinstance(range_y, int):
                    random_y = range_y
                elif isinstance(range_y, list) and len(range_y) == 1:
                    random_y = range_y[0]
                elif isinstance(range_y, list) and len(range_y) >= 2:
                    random_y = random.randint(range_y[0], range_y[1])

                obj = self.build_entity(key, data, random_x, random_y)
                self.entities.append(obj)

    async def network_loop(self):
        while True:
            try:
                await lobby_manager.send({
                    "id": "player1",
                    "x": self.player.x,
                    "y": self.player.y,
                    "vx": self.player.velocity_x,
                    "vy": self.player.velocity_y
                })
            except Exception as e:
                print("Lobby connection lost:", e)
                await asyncio.sleep(1)

            config_fps_str = await readConfigItem("current_fps")
            print(config_fps_str)

            await asyncio.sleep(1/config_fps_str if config_fps_str.isdigit() and int(config_fps_str) > 0 else 1/60)

    def set_remote_player(self, player_id, x, y, vx=0, vy=0, dt=1/60):
        if player_id not in self.remote_players:
            p = Player()
            p.color = QColor("red")
            self.remote_players[player_id] = p

        p = self.remote_players[player_id]

        # smooth position correction
        alpha = 1 - pow(0.001, dt * 60)  # Smoothing factor based on delta time
        p.x += (x - p.x) * alpha
        p.y += (y - p.y) * alpha

        # optional: apply velocity for prediction feel
        p.x += vx * 0.1
        p.y += vy * 0.1

    def setBorder(self, color: str, size: int):
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

        if not event.isAutoRepeat():
            self.timer.start()

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
        
        if len(self.overlay.labels) >= 2:
            self.overlay.set("fps", int(actual_fps))
            self.overlay.set("latency", int(delta_time * 1000), "ms")

        for label in self.overlay.labels.values():
            label.adjustSize()

        self.handle_movement(delta_time)
        self.camera.update(delta_time)
        self.update()

    def _do_jump(self):
        if self.player.is_on_ground:
            self.player.velocity_y = self.jump_velocity
            self.player.is_on_ground = False
        for entities in self.entities:
            if entities.is_on_ground:
                entities.velocity_y = self.jump_velocity
                entities.is_on_ground = False

    def handle_movement(self, delta_time=1 / 60):
        # Scale per-frame values so gameplay speed stays consistent across FPS values.
        dt_scale = delta_time * 60

        # Jumping border effect and physics
        jumping = any(key in self.keys_pressed for key in self.JUMP_KEYS)
        
        if jumping:
            self._do_jump()

        self.player.is_on_ground = False  # Will be set to True if collision with ground is detected later

        for entity in self.entities:
            entity.is_on_ground = False  # Will be set to True if collision with ground is detected later

        self.player.velocity_x = 0

        # if any(key in self.keys_pressed for key in self.DOWN_KEYS):
        #     self.player.y = min(self.player.height, self.player.y + (self.player.speed * dt_scale))

        # LEFT movement
        if any(key in self.keys_pressed for key in self.LEFT_KEYS):
            self.player.facing = "left"
            self.player.velocity_x -= self.player.speed

        # RIGHT movement
        if any(key in self.keys_pressed for key in self.RIGHT_KEYS):
            self.player.facing = "right"
            self.player.velocity_x += self.player.speed

        # Vertical physics
        self.apply_physics(self.player, dt_scale)
        self.terrain.check_collision(self.player)

        self.player.x += (self.player.velocity_x * dt_scale)
        self.terrain.check_collision(self.player)

        self.init_world()

        for entity in self.entities:
            if not self.should_simulate(entity):
                continue

            self.apply_physics(entity, dt_scale)
            self.terrain.check_collision(entity)

        if jumping:
            self.setBorder("#dddda0", 6)
        elif Qt.Key.Key_Shift in self.keys_pressed:
            self.setBorder("gray", 4)
        else:
            self.setBorder("", 0)
        
        self.player.speed = 10 if Qt.Key.Key_Shift in self.keys_pressed else 5

    def should_simulate(self, entity):
        return self.is_on_screen(entity) or self.is_near_player(entity)

    def is_on_screen(self, entity, margin=200):
        screen_x = entity.x - self.camera.x
        screen_y = entity.y - self.camera.y

        return (
            -margin <= screen_x <= self.width() + margin and
            -margin <= screen_y <= self.height() + margin
        )

    def is_near_player(self, entity, distance=1500):
        return abs(entity.x - self.player.x) < distance

    def apply_physics(self, entity, dt_scale):
        # Remember previous position so collision resolution can revert movement when needed
        entity.previous_x = entity.x
        entity.previous_y = entity.y

        if not entity.is_on_ground:
            entity.velocity_y += self.gravity * entity.mass * dt_scale
            entity.velocity_y = min(entity.velocity_y, 15)

        entity.y += entity.velocity_y * dt_scale

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
        asyncio.create_task(self.overlay._load_translations())  # Reload translations in case they were changed in the menu
        asyncio.create_task(self._apply_settings())  # Re-apply settings in case they were changed in the menu

    async def _load_bindings(self):
        self.bindings = await load_bindings()
        self.apply_bindings()
    
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