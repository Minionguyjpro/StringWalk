from PyQt6.QtWidgets import QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, QFrame
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QGraphicsVideoItem
from PyQt6.QtCore import QUrl, Qt, QSizeF

class VideoManager(QWidget):
    """Hardware-accelerated background video that fills the widget."""
    def __init__(self, parent=None):
        super().__init__(parent)

        self._video_enabled = False
        self.player = None
        self.audio_output = None
        self.video_item = None

        try:
            self._setup_player()
            self._video_enabled = True
        except Exception as err:
            print(f"Video background disabled: {err}")

    def _setup_player(self):
        # Scene & view
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene, self)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setFrameShape(QFrame.Shape.NoFrame)
        self.view.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.view)

        # Video item
        self.video_item = QGraphicsVideoItem()
        self.scene.addItem(self.video_item)

        # Media player
        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.audio_output.setVolume(0)
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_item)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self._video_enabled:
            return
        # Fill the QGraphicsView
        self.view.setGeometry(self.rect())
        # Scale the video item to fill the view (keep aspect ratio)
        rect = self.view.rect()

        w = max(rect.width(), 1)
        h = max(rect.height(), 1)

        self.video_item.setSize(QSizeF(float(w), float(h)))

    def play_video(self, filename: str):
        if not self._video_enabled:
            return

        from pathlib import Path
        path = Path(__file__).resolve().parent.parent.parent / "assets" / "video" / filename
        if not path.exists():
            print(f"ERROR: Video not found: {path}")
            return
        try:
            self.player.setSource(QUrl.fromLocalFile(str(path)))
            self.player.setLoops(QMediaPlayer.Loops.Infinite)
            self.player.play()
        except Exception as err:
            print(f"Video playback disabled: {err}")
            self._video_enabled = False

    def stop_video(self):
        """Stops the video playback safely."""
        if not self._video_enabled:
            return

        if self.player.playbackState() != QMediaPlayer.PlaybackState.StoppedState:
            self.player.stop()

        # Detach media safely
        self.player.setSource(QUrl())