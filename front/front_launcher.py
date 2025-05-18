import sys

from PySide6.QtWidgets import QApplication

from front.resources.resources_rc import qInitResources, qCleanupResources
from front.resources.stylesheet import style
from front.widgets.mainWindow import MainWindow

def launch_front():
    qInitResources()
    app = QApplication(sys.argv)
    app.setStyleSheet(style)

    window = MainWindow(is_admin=False)
    window.resize(1000, 600)
    window.show()
    sys.exit(app.exec())