import os
import sys
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl
from importlib import resources
from ..data.projectNameHandler import getProjectNameLower
from ..jsonParser import parseJson

class AudioManager:
    def __init__(self):
        self.music_player = QMediaPlayer()
        self.music_output = QAudioOutput()
        self.music_player.setAudioOutput(self.music_output)
        self.music_muted = False

        self.sfx_player = QMediaPlayer()
        self.sfx_output = QAudioOutput()
        self.sfx_player.setAudioOutput(self.sfx_output)
        self.sfx_map = self._load_sfx_map()

        self.current_music = None
    
    def _resolve(self, category: str, filename: str):
        base = getProjectNameLower()
        module = f"{base}.assets.audio.{category}"
        return resources.files(module) / filename

    def _silence_ffmpeg(self):
        self._stderr = sys.stderr
        sys.stderr = open(os.devnull)
    
    def _restore_ffmpeg(self):
        sys.stderr.close()
        sys.stderr = self._stderr

    def play_music(self, filename: str):
        if self.current_music == filename and \
            self.music_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
                return

        path = self._resolve("music", filename)
        url = QUrl.fromLocalFile(str(path))

        self._silence_ffmpeg()
        self.music_player.setSource(url)
        self.music_player.setLoops(QMediaPlayer.Loops.Infinite)
        self.music_player.play()
        self._restore_ffmpeg()

        self.current_music = filename
    
    def stop_music(self):
        self.music_player.stop()
        self.current_music = None
    
    def play_sfx(self, filename: str):
        path = self._resolve("sfx", filename)
        url = QUrl.fromLocalFile(str(path))

        self._silence_ffmpeg()
        self.sfx_player.setSource(url)
        self.sfx_player.play()
        self._restore_ffmpeg()

    def _load_sfx_map(self):
        path = self._resolve("sfx", "map.json")
        data = parseJson(str(path))
        return data or {}

    def get_sfx_for(self, widget, event_name):
        wtype = type(widget).__name__
        return self.sfx_map.get(wtype, {}).get(event_name)

audio = AudioManager()