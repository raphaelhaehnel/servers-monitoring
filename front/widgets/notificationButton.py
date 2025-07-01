from PySide6.QtWidgets import QWidget, QPushButton, QLabel
from PySide6.QtCore import Qt

class NotificationButton(QWidget):
    def __init__(self, text="", parent=None):
        super().__init__(parent)

        self.button = QPushButton(text, self)
        self.button.setFixedSize(140, 35)

        # Ensure the badge is always on top
        self.badge = QLabel("0", self)
        self.badge.setFixedSize(18, 18)
        self.badge.setAlignment(Qt.AlignCenter)
        self.badge.setStyleSheet("""
            QLabel {
                background-color: #d32f2f;
                border: 2px solid black; 
                color: white;
                border-radius: 9px;
                font-size: 11px;
                padding: 1px;
            }
        """)
        self.badge.move(self.button.width() - 10, 0)
        self.badge.raise_()  # Ensure it draws above the button
        self.badge.hide()

        self.setFixedSize(self.button.size())

    def resizeEvent(self, event):
        # Reposition the badge on top-right corner
        self.badge.move(self.button.width() - 16, -2)
        super().resizeEvent(event)

    def set_count(self, count: int):
        if count > 0:
            self.badge.setText(str(count))
            self.badge.show()
        else:
            self.badge.hide()

    def clicked(self, callback):
        self.button.clicked.connect(callback)

    def setEnabled(self, enabled: bool):
        self.button.setEnabled(enabled)
