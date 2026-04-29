from PyQt6.QtGui import QMovie, QPixmap
from dataclasses import dataclass


class Entity:
    def __init__(
        self,
        x,
        y,
        width,
        height,
        image_path,
        mass=1.0,
        quantity=1,
        animated=False,
        animation_type=None,
        frame_speed=0.1,
        game_widget=None,
        data=None
    ):
        self.x = x
        self.y = y
        self.name = "Entity"
        self.width = width
        self.height = height

        self.velocity_x = 0
        self.velocity_y = 0

        self.mass = mass
        self.quantity = quantity
        self.game_widget = game_widget

        self.is_on_ground = True

        self.animated = animated
        self.animation_type = animation_type
        self.frame_speed = frame_speed

        self.movie = None
        self.frames = []
        self.frame_index = 0
        self.frame_timer = 0.0

        self.current_frame = QPixmap()
        self.image = None

        if data:
            if data.get("icon_frames"):
                self.animation_type = "frames"

            elif self.animated or (image_path and image_path.lower().endswith(".gif")):
                self.animation_type = "gif"

            else:
                self.animation_type = "static"
        else:
            self.animation_type = "static"
        # ---------------------------
        # Load assets
        # ---------------------------
        if self.animation_type == "gif":
            self.movie = QMovie(image_path)
            self.movie.setCacheMode(QMovie.CacheMode.CacheAll)
            self.movie.setSpeed(100)  # 100% speed
            self.movie.start()

        elif self.animation_type == "frames":
            frame_list = data.get("icon_frames", [])
            self.frames = [
                QPixmap(path) for path in frame_list
            ]
            self.current_frame = self.frames[0] if self.frames else QPixmap()

        else:
            self.image = QPixmap(image_path)
            self.current_frame = self.image

    # ---------------------------
    # Animation update
    # ---------------------------
    def update_animation(self, dt):
        if self.animation_type == "frames":
            if not self.frames:
                return

            self.frame_timer += dt

            if self.frame_timer >= self.frame_speed:
                self.frame_timer = 0
                self.frame_index = (self.frame_index + 1) % len(self.frames)
                self.current_frame = self.frames[self.frame_index]

        elif self.animation_type == "gif":
            # FORCE QT TO ADVANCE (important in some event-loop setups)
            if self.movie:
                self.movie.jumpToNextFrame()

    # ---------------------------
    # Render
    # ---------------------------
    def update(self, painter):
        if self.animated and self.movie:
            pixmap = self.movie.currentPixmap()
        else:
            pixmap = self.image

        painter.drawPixmap(
            int(self.x - self.game_widget.camera.x),
            int(self.y - self.game_widget.camera.y),
            self.width,
            self.height,
            pixmap
        )