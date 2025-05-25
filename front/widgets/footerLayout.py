import requests
from PySide6.QtGui import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QPushButton, QLabel


class FooterLayout(QFrame):
    
    def __init__(self):
        super().__init__()
        self.setObjectName("footerFrame")
        self.footer_layout = QHBoxLayout(self)
        self.footer_layout.setContentsMargins(10, 5, 10, 5)
        self.footer_layout.setAlignment(Qt.AlignVCenter)

        self.btn_master = QPushButton("User role")
        self.btn_master.clicked.connect(self.on_be_master)
        self.footer_layout.addWidget(self.btn_master)

        self.label_last_update = QLabel("Not up-to-date")
        self.label_last_update.setObjectName("lastUpdateTime")
        self.footer_layout.addWidget(self.label_last_update)

        # Stretch pushes the next widgets to the right
        self.footer_layout.addStretch()

        self.version_label = QLabel("v1.0")
        self.version_label.setObjectName("versionLabel")
        self.footer_layout.addWidget(self.version_label)

        self.footer_layout.addSpacing(20)

        self.copyright_name = QLabel("© Raphael Haehnel")
        self.copyright_name.setObjectName("copyrightName")
        self.footer_layout.addWidget(self.copyright_name)

    @staticmethod
    def on_be_master():
        # Calls backend’s POST endpoint overriding master role:
        try:
            r = requests.post("http://localhost:8000/master", json={"id": "<your-peer-id>"})
            if r.status_code == 204:
                print("Master override sent!")  # optionally refresh your display
            else:
                print("Failed to set master:", r.status_code)
        except Exception as e:
            print("Error contacting control server:", e)