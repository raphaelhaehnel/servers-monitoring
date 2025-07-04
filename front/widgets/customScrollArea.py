from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QScrollArea


class CustomScrollArea(QScrollArea):
    def wheelEvent(self, event: QWheelEvent):
        delta = event.angleDelta().y() // 8
        self.verticalScrollBar().setValue(
            self.verticalScrollBar().value() - delta)