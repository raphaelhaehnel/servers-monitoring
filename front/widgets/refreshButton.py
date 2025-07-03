import threading

from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QTransform, QIcon, Qt, QPixmap
from PySide6.QtWidgets import QPushButton


class RefreshButton(QPushButton):
    """
    A QPushButton with a rotating icon and threaded task execution.
    Pass a callable task to run when clicked; spinner will show until done.
    """
    _task_done = Signal()

    def __init__(self, task_callable, parent=None):
        super().__init__(parent)
        self._task_callable = task_callable

        # Setup icon and fixed size
        self._orig_pix = QPixmap(":/icons/images/icons/cil-reload.png")
        self.setIcon(QIcon(self._orig_pix))
        self.setFixedSize(24, 24)
        self.setIconSize(self.size())
        self.setToolTip("Refresh server info")

        # Timer for spinning
        self._angle = 0
        self._timer = QTimer(self)
        self._timer.setInterval(50)
        self._timer.timeout.connect(self._rotate_icon)

        # Connect signals
        self.clicked.connect(self._on_clicked)
        self._task_done.connect(self._on_task_done)

    def _on_clicked(self):
        # Disable and start spinner
        self.setEnabled(False)
        self._angle = 0
        self._timer.start()
        # Run task in background
        threading.Thread(target=self._run_task, daemon=True).start()

    def _run_task(self):
        try:
            self._task_callable()
            self._task_done.emit()
        except RuntimeError:
            pass

    def _on_task_done(self):
        # Stop spinner, restore icon, re-enable
        self._timer.stop()
        self.setIcon(QIcon(self._orig_pix))
        self.setEnabled(True)

    def _rotate_icon(self):
        # Rotate original pixmap
        transform = QTransform().rotate(self._angle)
        rotated = self._orig_pix.transformed(transform, Qt.SmoothTransformation)
        self.setIcon(QIcon(rotated))
        self._angle = (self._angle + 20) % 360
