import sys

from PySide6.QtWidgets import QApplication

from front.stylesheet import style
from main import MainWindow

def launch_front():
    app = QApplication(sys.argv)
    app.setStyleSheet(style)

    window = MainWindow(is_admin=False)
    window.resize(1000, 600)
    window.show()
    sys.exit(app.exec())