from PyQt6.QtGui import QPixmap


def is_frame_empty(spritesheet: QPixmap, x: int, y: int, width: int = 64, height: int = 64) -> bool:
    """
    Check if a frame in the spritesheet is empty (all pixels are transparent).

    :param spritesheet: The QPixmap representing the spritesheet.
    :param x: The x-coordinate of the top-left corner of the frame.
    :param y: The y-coordinate of the top-left corner of the frame.
    :param width: The width of the frame (default is 64).
    :param height: The height of the frame (default is 64).
    :return: True if the frame is empty, False otherwise.
    """
    for i in range(width):
        for j in range(height):
            pixel_color = spritesheet.toImage().pixelColor(x + i, y + j)
            if pixel_color.alpha() != 0:
                return False
    return True