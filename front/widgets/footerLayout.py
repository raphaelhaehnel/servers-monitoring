from PySide6.QtGui import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QPushButton, QLabel

from front.widgets.notificationButton import NotificationButton
from infrastructure.shared_models.shared_isMaster import SharedIsMaster


class FooterLayout(QFrame):
    
    def __init__(self, parent, shared_master: SharedIsMaster):
        super().__init__(parent)
        self.setObjectName("footerFrame")
        self.footer_layout = QHBoxLayout(self)
        self.footer_layout.setContentsMargins(10, 8, 10, 8) #left, top, right, bottom
        self.footer_layout.setAlignment(Qt.AlignVCenter)

        self.shared_is_master: SharedIsMaster = shared_master

        self.btn_master = QPushButton("Slave")
        self.footer_layout.addWidget(self.btn_master)
        self.btn_master.clicked.connect(self.set_master)
        self.update_master_button()

        self.label_last_update = QLabel("Not up-to-date")
        self.label_last_update.setObjectName("lastUpdateTime")
        self.footer_layout.addWidget(self.label_last_update)

        self.view_requests_btn = NotificationButton("View Requests")
        self.view_requests_btn.clicked(self.parent().show_requests_dialog)
        self.footer_layout.addWidget(self.view_requests_btn)

        # Stretch pushes the next widgets to the right
        self.footer_layout.addStretch()

        self.version_label = QLabel("v1.0")
        self.version_label.setObjectName("versionLabel")
        self.footer_layout.addWidget(self.version_label)

        self.footer_layout.addSpacing(20)

        self.copyright_name = QLabel("© Raphael Haehnel")
        self.copyright_name.setObjectName("copyrightName")
        self.footer_layout.addWidget(self.copyright_name)

    def set_master(self):
        self.shared_is_master.data = True  # This will call update_master_button()

    def update_master_button(self):
        self.btn_master.setText("Master" if self.shared_is_master.data else "Slave")
        if self.shared_is_master.data:
            self.btn_master.setStyleSheet("background-color: #388e3c")
            self.btn_master.setEnabled(False)
            return
        else:
            self.btn_master.setStyleSheet("""QPushButton {
                                                background-color: #d32f2f;
                                            }
                                            QPushButton:hover {
                                                background-color: #f44336;
                                            }""")

        main_window = self.window()
        if hasattr(main_window, 'is_admin') and main_window.is_admin:
            self.btn_master.setEnabled(True)
        else:
            self.btn_master.setEnabled(False)