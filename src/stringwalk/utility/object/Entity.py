from ..graphics.Image import is_frame_empty
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
        data=None,
        type=None
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

        self.type = type

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

            elif self.animated and (image_path and image_path.lower().endswith(".gif")):
                self.animation_type = "gif"
            elif self.animated and (image_path and image_path.lower().endswith(".png")):
                self.animation_type = "spritesheet"
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
            if not data:
                print("ERROR: frames animation but no data!")
                self.animation_type = "static"
                return

            frame_list = data.get("icon_frames", [])

            if not frame_list:
                print("ERROR: frames animation but no icon_frames:", data)
                self.animation_type = "static"
                return

            self.frames = []
            for path in frame_list:
                pix = QPixmap(path)
                if not pix.isNull():
                    self.frames.append(pix)
                else:
                    print(f"Failed to load frame: {path}")

            print(f"Loaded {len(self.frames)} frames for entity at ({self.x}, {self.y})")
            self.current_frame = self.frames[0] if self.frames else QPixmap()

        else:
            self.image = QPixmap(image_path)

            if self.animation_type == "spritesheet":
                # Standard size for spritesheet frames
                x_size = 16
                y_size = 16
                
                s_width = self.image.width()
                s_height = self.image.height()

                x_frames = s_width // x_size
                y_frames = s_height // y_size
 
                for y in range(x_frames):
                    for x in range(y_frames):
                        frame = self.image.copy(x * x_size, y * y_size, x_size, y_size)
                        if not frame.isNull() and not is_frame_empty(self.image, x * x_size, y * y_size, x_size, y_size):
                            self.frames.append(frame)

                i_frames = data.get("frames", None)

                if i_frames:
                    # Filter frames based on i_frames indices
                    self.frames = [self.frames[i] for i in i_frames if 0 <= i < len(self.frames)]

                print(len(self.frames), "frames in spritesheet")
                print(self.frames)
            else:
                self.current_frame = self.image

    # ---------------------------
    # Animation update
    # ---------------------------
    def update_animation(self, dt):
        if self.animation_type == "frames" or self.animation_type == "spritesheet":
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
        elif self.animation_type == "frames" or self.animation_type == "spritesheet":
            pixmap = self.current_frame
        else:
            pixmap = self.image

        painter.drawPixmap(
            int(self.x - self.game_widget.camera.x),
            int(self.y - self.game_widget.camera.y),
            self.width,
            self.height,
            pixmap
        )