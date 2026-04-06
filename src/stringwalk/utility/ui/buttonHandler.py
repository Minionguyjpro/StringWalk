from PyQt6.QtWidgets import QPushButton
from ..audio.audioManager import audio


def handleButton(action, widget=None):
    """
    Universal handler: executes the action passed.
    The menu decides which action to pass per button.
    """
    if callable(action):
        action(widget)

def reloadButton(button: QPushButton):
    """
    Re-applies the current stylesheet to the button.
    Useful for dynamic property changes (e.g. mute/unmute).
    """
    button.style().unpolish(button)
    button.style().polish(button)

def create_action(button: QPushButton, func) -> function:
    """
    Wraps a function with SFX logic.
    Ensures SFX only plays when clicking the actual button area.
    """
    def wrapper(event=None):
        if isinstance(button, QPushButton):
            # Only play SFX if event position is inside the button
            if event is None or button.rect().contains(button.mapFromGlobal(event.globalPosition().toPoint())):
                sfx = audio.get_sfx_for(button, "MouseButtonPress")
                if sfx:
                    audio.play_sfx(sfx)

        # Call the real action
        func()

    return wrapper