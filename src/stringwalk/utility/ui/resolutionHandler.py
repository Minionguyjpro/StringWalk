from ..configHandler import readConfigItem
from PyQt6.QtWidgets import QApplication


async def getResolution() -> str:
    """
    Get the currently selected resolution.
    """
    # Get the current resolution in the config
    resolution = await readConfigItem("current_resolution")

    if resolution is None:
        # Set a default resolution if the current resolution cannot be read
        resolution = "640x480"
        result = resolution
    elif resolution == "fullscreen" or resolution == "maximized":
        result = await getResolutionMax()
    else:
        result = resolution

    # Return result
    return result

async def getResolutionMax() -> str:
    """
    Get the resolution of the primary screen for fullscreen or maximized mode.
    """
    screen = QApplication.primaryScreen()
    size = screen.size()
    return f"{size.width()}x{size.height()}"

async def getWidth() -> int:
    """
    Get the width of the currently selected resolution.
    """
    resolution = await getResolution()
    width_str = resolution.split("x")[0]
    return int(width_str)

async def getHeight() -> int:
    """
    Get the height of the currently selected resolution.
    """
    resolution = await getResolution()
    height_str = resolution.split("x")[1]
    return int(height_str)

def centerWindow(window):
    """
    Center a top-level window on its screen (DPI-safe)
    """
    screen = window.screen() or QApplication.primaryScreen()
    screen_geo = screen.availableGeometry()  # logical pixels
    win_geo = window.frameGeometry()         # logical pixels

    x = screen_geo.x() + (screen_geo.width() // 2 - win_geo.width()) // 2
    y = screen_geo.y() + (screen_geo.height() // 2 - win_geo.height()) // 2

    window.move(x, y)

def lockWindowSize(window, width, height):
    """
    Lock window size in logical pixels, respecting DPI scaling.
    width/height = desired physical pixels
    """
    window.setMinimumSize(width, height)
    window.setMaximumSize(width, height)
    window.resize(width, height)