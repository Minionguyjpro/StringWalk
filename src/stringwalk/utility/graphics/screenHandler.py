from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QPainter
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsPixmapItem, QGraphicsBlurEffect


def captureWidget(widget) -> QPixmap:
    """
    Captures the current widget and returns as QPixmap.
    """
    if widget is None:
        return None

    # Grab the widget
    pixmap = widget.grab()

    return pixmap

def blur_pixmap(pixmap, radius=15):
    """
    Applies a blur effect to the given QPixmap.
    """

    # Create a graphics scene
    scene = QGraphicsScene()
    item = QGraphicsPixmapItem(pixmap)
    scene.addItem(item)

    # Apply blur effect
    blur = QGraphicsBlurEffect()
    blur.setBlurRadius(radius)
    item.setGraphicsEffect(blur)

    # Render the blurred pixmap
    blurred_pixmap = QPixmap(pixmap.size())
    blurred_pixmap.fill(Qt.GlobalColor.transparent)  # Fill with transparent background
    painter = QPainter(blurred_pixmap)
    scene.render(painter)
    painter.end()

    return blurred_pixmap