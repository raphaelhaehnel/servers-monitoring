from PySide6.QtCore import Qt
from PySide6.QtGui import QMouseEvent, QIcon, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QWidget, QLabel, QPushButton, QDialog

from front.widgets.loginDialog import LoginDialog


class CustomTitleBar(QWidget):
    def __init__(self, is_admin=False, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setFixedHeight(40)
        self.setObjectName("customTitleBar")
        self.offset = None
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)

        # Add icon before title
        self.icon_label = QLabel()
        self.icon_label.setPixmap(QPixmap(":graphics/images/graphics/icon.png").scaled(42, 42, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(self.icon_label)

        self.title = QLabel("FacIT")
        self.title.setObjectName("titleLabel")
        layout.addWidget(self.title)
        layout.addStretch()

        self.login_button = QPushButton("Login as admin")
        self.login_button.setFixedSize(120, 35)
        self.login_button.clicked.connect(self.open_login_dialog)
        layout.addWidget(self.login_button)
        if is_admin:
            self.make_button_admin()

        self.settings_button = QPushButton()
        self.settings_button.setFixedSize(35, 35)
        self.settings_button.setIcon(QIcon(":icons/images/icons/cil-settings.png"))
        self.settings_button.clicked.connect(self.open_settings_dialog)
        layout.addWidget(self.settings_button)

        self.minimize_button = QPushButton()
        self.minimize_button.setFixedSize(35, 35)
        self.minimize_button.setIcon(QIcon(":icons/images/icons/icon_minimize.png"))
        self.minimize_button.clicked.connect(self.minimize_window)
        layout.addWidget(self.minimize_button)

        self.close_button = QPushButton()
        self.close_button.setFixedSize(35, 35)
        self.close_button.setIcon(QIcon(":icons/images/icons/icon_close.png"))
        self.close_button.clicked.connect(self.close_window)
        layout.addWidget(self.close_button)

    def open_settings_dialog(self):
        pass

    def open_login_dialog(self):
        dlg = LoginDialog()
        if dlg.exec() == QDialog.Accepted:
            self.parent.is_admin = dlg.is_admin
            self.parent.footer_frame.update_master_button()

        if dlg.is_admin:
            self.make_button_admin()

            main_window = self.window()
            if hasattr(main_window, 'update_items'):
                main_window.update_items(force=True)


    def make_button_admin(self):
        self.login_button.setText("Logged as admin")
        self.login_button.setEnabled(False)  # TODO update the list immediately

    def minimize_window(self):
        self.parent.showMinimized()

    def close_window(self):
        self.parent.close()

    def mousePressEvent(self, event: QMouseEvent):
        self.offset = event.globalPosition().toPoint() - self.parent.pos()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton:
            self.parent.move(event.globalPosition().toPoint() - self.offset)
