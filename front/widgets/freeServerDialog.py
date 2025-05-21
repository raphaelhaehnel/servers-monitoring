from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QHBoxLayout, QVBoxLayout

class FreeServerDialog(QDialog):
    def __init__(self, server_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirm Server Release")
        self.server_name = server_name
        self.result = False  # To store user decision

        # Create message label
        message = f"Do you really want to free the server '{self.server_name}'?"
        self.label = QLabel(message)

        # Create buttons
        self.yes_button = QPushButton("Yes")
        self.cancel_button = QPushButton("Cancel")

        # Connect signals
        self.yes_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        # Layout setup
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.yes_button)
        button_layout.addWidget(self.cancel_button)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.label)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
