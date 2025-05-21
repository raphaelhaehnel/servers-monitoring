from PySide6.QtWidgets import QPushButton

class HoverButton(QPushButton):
    def __init__(self, default_text: str, hover_text: str, parent=None):
        super().__init__(default_text, parent)
        self._default_text = default_text
        self._hover_text = hover_text

    def enterEvent(self, event):
        # called when mouse enters the widget
        self.setText(self._hover_text)
        super().enterEvent(event)

    def leaveEvent(self, event):
        # called when mouse leaves the widget
        self.setText(self._default_text)
        super().leaveEvent(event)

    def setDefaultText(self, txt: str):
        """Change the button’s normal text at runtime."""
        self._default_text = txt
        # if the mouse isn’t currently hovering, show it immediately
        if not self.underMouse():
            self.setText(txt)

    # if you want to change the hover‐text
    def setHoverText(self, txt: str):
        self._hover_text = txt
