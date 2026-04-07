from PyQt6.QtGui import QPixmap


async def captureWidget(widget) -> QPixmap:
    """
    Captures the current widget and returns as QPixmap.
    """
    if widget is None:
        return None

    # Grab the widget
    pixmap = widget.grab()

    return pixmap