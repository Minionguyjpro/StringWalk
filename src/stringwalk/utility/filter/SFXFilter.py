from PyQt6.QtCore import QObject, QEvent
from PyQt6.QtWidgets import QWidget, QPushButton
from ..audio.audioManager import audio

class SFXFilter(QObject):
    def _is_pointer_inside(self, obj, event):
        if not isinstance(obj, QWidget):
            return False

        edge_margin = 2

        def _strict_rect_contains(local_point):
            rect = obj.rect().adjusted(edge_margin, edge_margin, -edge_margin, -edge_margin)
            return rect.contains(local_point)

        # Prefer local event coordinates when available.
        if hasattr(event, "position"):
            local = event.position().toPoint()
            if isinstance(obj, QPushButton):
                return obj.hitButton(local) and _strict_rect_contains(local)
            return _strict_rect_contains(local)

        # Fallback for older/other mouse event variants.
        if hasattr(event, "globalPosition"):
            local = obj.mapFromGlobal(event.globalPosition().toPoint())
            if isinstance(obj, QPushButton):
                return obj.hitButton(local) and _strict_rect_contains(local)
            return _strict_rect_contains(local)

        return False

    def eventFilter(self, obj, event):
        # Only handle click events to keep SFX non-bursty.
        if event.type() in (QEvent.Type.MouseButtonPress,
                            QEvent.Type.MouseButtonRelease):
            if not self._is_pointer_inside(obj, event):
                return super().eventFilter(obj, event)

            sfx = audio.get_sfx_for(obj, event.type().name)
            if sfx:
                print(sfx)
                audio.play_sfx(sfx)
        return super().eventFilter(obj, event)