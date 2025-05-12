from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QHBoxLayout, QWidget, QLabel, QPushButton, QDialog

from widgets.loginDialog import LoginDialog


class CustomTitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(40)
        self.setObjectName("customTitleBar")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)

        self.title = QLabel("FacIT")
        self.title.setObjectName("titleLabel")
        layout.addWidget(self.title)
        layout.addStretch()

        self.login_button = QPushButton("Login as admin")
        self.login_button.setFixedSize(100, 20)
        self.login_button.clicked.connect(self.open_login_dialog)
        layout.addWidget(self.login_button)

        self.minimize_button = QPushButton("-")
        self.minimize_button.setFixedSize(20, 20)
        self.minimize_button.clicked.connect(self.minimize_window)
        layout.addWidget(self.minimize_button)

        self.close_button = QPushButton("x")
        self.close_button.setFixedSize(20, 20)
        self.close_button.clicked.connect(self.close_window)
        layout.addWidget(self.close_button)

    def open_login_dialog(self):
        dlg = LoginDialog()
        if dlg.exec() == QDialog.Accepted:
            self.parent.is_admin = dlg.is_admin

        if dlg.is_admin:
            self.login_button.setText("Logged as admin")
            self.login_button.setEnabled(False)
            #TODO update the list immediately

    def minimize_window(self):
        self.parent.showMinimized()

    def close_window(self):
        self.parent.close()

    def mousePressEvent(self, event: QMouseEvent):
        self.offset = event.globalPosition().toPoint() - self.parent.pos()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton:
            self.parent.move(event.globalPosition().toPoint() - self.offset)