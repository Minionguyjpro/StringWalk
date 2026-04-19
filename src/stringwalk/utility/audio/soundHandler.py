from .audioManager import audio
from PyQt6.QtMultimedia import QMediaPlayer


def playSound(category: str, filename: str):
    """
    Categories: "music", "sfx", "ui" etc.
    Filename: "lobby.mp3", "click.wav" etc.
    """
    if category == "music":
        if audio.music_muted:
            return
        audio.play_music(filename)
    elif category == "sfx":
        audio.play_sfx(filename)

def stopSound():
    try:
        audio.stop_music()
    except Exception:
        return

def toggleSound(category: str, filename: str):
    try:
        state = audio.music_player.playbackState()
        if state == QMediaPlayer.PlaybackState.PlayingState:
            audio.music_muted = True
            audio.stop_music()
        else:
            audio.music_muted = False
            # Resume last selected track, or use the provided fallback filename.
            track = audio.current_music or filename
            if track:
                if category == "music":
                    audio.play_music(track)
                elif category == "sfx":
                    audio.play_sfx(track)
    except Exception as err:
        print(f"Toggle sound error: {err}")

def isSoundPlaying() -> bool:
    try:
        return audio.music_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
    except Exception:
        return False