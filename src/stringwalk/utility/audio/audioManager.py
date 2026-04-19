import os
import sys
import time
from contextlib import redirect_stderr
from PyQt6.QtMultimedia import QMediaDevices, QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl
from importlib import resources
from ..data.projectNameHandler import getProjectNameLower
from ..jsonParser import parseJson


class _NullMediaPlayer:
    def setAudioOutput(self, _output):
        return None

    def setSource(self, _url):
        return None

    def setLoops(self, _loops):
        return None

    def play(self):
        return None

    def stop(self):
        return None

    def playbackState(self):
        return QMediaPlayer.PlaybackState.StoppedState

class AudioManager:
    def __init__(self):
        self.enabled = False
        self._init_failed = False
        self._last_init_try = 0.0
        self._retry_delay_seconds = 2.0
        self._last_sfx_time = 0.0
        self._last_sfx_name = None
        self._sfx_cooldown_seconds = 0.08
        self.available_outputs = []
        self.default_output = QMediaDevices.defaultAudioOutput()
        self.music_output = QAudioOutput(self.default_output)
        self.sfx_output = QAudioOutput(self.default_output)
        self.music_player = QMediaPlayer()
        self.sfx_player = QMediaPlayer()
        self.music_player.setAudioOutput(self.music_output)
        self.sfx_player.setAudioOutput(self.sfx_output)
        self.music_muted = False
        self.sfx_map = self._load_sfx_map()
        self.current_music = None

    def _disable_audio(self, reason=None):
        if reason:
            print(reason)
        self.music_player = _NullMediaPlayer()
        self.sfx_player = _NullMediaPlayer()
        self.music_output = None
        self.sfx_output = None
        self.available_outputs = []
        self.default_output = None
        self.sfx_map = {}
        self.enabled = False
        self._init_failed = True

    def _has_live_backend(self):
        return (
            self.music_output is not None
            and self.sfx_output is not None
            and not isinstance(self.music_player, _NullMediaPlayer)
            and not isinstance(self.sfx_player, _NullMediaPlayer)
        )

    def _ensure_ready(self):
        if self.music_player is None or self.sfx_player is None:
            return False
        return True
    
    def _resolve(self, category: str, filename: str):
        base = getProjectNameLower()
        module = f"{base}.assets.audio.{category}"
        return resources.files(module) / filename

    def play_music(self, filename: str):
        if not self._ensure_ready():
            return

        path = self._resolve("music", filename)
        url = QUrl.fromLocalFile(str(path))

        if self.current_music == filename and \
            self.music_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                return

        self.music_player.setSource(url)
        self.music_player.setLoops(QMediaPlayer.Loops.Infinite)
        self.music_player.play()

        self.current_music = filename
    
    def stop_music(self):
        self.music_player.stop()
        self.current_music = None
    
    def play_sfx(self, filename: str):
        if not self._ensure_ready():
            return

        path = self._resolve("sfx", filename)
        url = QUrl.fromLocalFile(str(path))

        self.sfx_player.setSource(url)
        self.sfx_player.play()
        
        now = time.monotonic()
        self._last_sfx_name = filename
        self._last_sfx_time = now

        try:
            self._last_sfx_name = filename
            self._last_sfx_time = now
        except Exception as err:
            print(f"Sound effects error: {err}")

    def _load_sfx_map(self):
        try:
            path = self._resolve("sfx", "map.json")
            data = parseJson(str(path))
            return data or {}
        except Exception:
            return {}

    def get_sfx_for(self, widget, event_name):
        wtype = type(widget).__name__
        return self.sfx_map.get(wtype, {}).get(event_name)

audio = AudioManager()