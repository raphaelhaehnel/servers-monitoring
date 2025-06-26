from PySide6.QtWidgets import QLineEdit, QLabel, QDialogButtonBox, QVBoxLayout, QDialog
import hashlib

PASSWORD = '68b95279d089756caccd9037bfbc7766271afc9a738a681e7ad58f3771e262c3'


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Admin Login")
        self.is_admin = False

        layout = QVBoxLayout(self)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter admin password")

        layout.addWidget(QLabel("Admin password:"))
        layout.addWidget(self.password_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)

        buttons.accepted.connect(self.handle_login)
        buttons.rejected.connect(self.reject)

    def handle_login(self):
        hashed_input = hashlib.sha256(self.password_input.text().encode()).hexdigest()
        if hashed_input == PASSWORD:
            self.is_admin = True
            self.accept()
        else:
            self.password_input.clear()
            self.password_input.setPlaceholderText("Incorrect password, try again.")