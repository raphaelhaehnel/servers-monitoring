from PySide6.QtWidgets import (
    QDialog, QLabel, QLineEdit,
    QPushButton, QHBoxLayout,
    QVBoxLayout, QFormLayout
)

from models.serverBookingData import ServerBookingData


class ServerBookingDialog(QDialog):
    def __init__(self, server_name: str, parent=None):
        super().__init__(parent)
        self.server_name = server_name

        # --- Window setup ---
        self.setWindowTitle("Server booking")

        # Top label showing the server being booked
        header = QLabel(f"Booking server: '{self.server_name}'")

        # --- Form fields ---
        self.user_edit = QLineEdit()
        self.comment_edit = QLineEdit()

        form_layout = QFormLayout()
        form_layout.addRow("User:", self.user_edit)
        form_layout.addRow("Comment:", self.comment_edit)

        # --- Buttons ---
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.ok_button)
        btn_layout.addWidget(self.cancel_button)

        # --- Main layout ---
        main_layout = QVBoxLayout()
        main_layout.addWidget(header)
        main_layout.addLayout(form_layout)
        main_layout.addLayout(btn_layout)
        self.setLayout(main_layout)

    def booking_data(self) -> ServerBookingData:
        """Return a dict with the entered data if accepted."""
        return ServerBookingData(self.server_name, self.user_edit.text(), self.comment_edit.text())
