from PySide6.QtWidgets import QInputDialog, QLineEdit, QLabel, QDialogButtonBox, QVBoxLayout, QDialog
import hashlib

PASSWORD = '7518f5e98c2e72067abdfc5f382b9e8217e441e4270140889418847a33ab9c45'


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.is_admin = False

        layout = QVBoxLayout(self)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        # Role selection
        self.role_input = QLineEdit()
        self.role_input.setPlaceholderText("Type 'admin' for admin, anything else for guest")

        layout.addWidget(QLabel("Select role ('admin' for administrator):"))
        layout.addWidget(self.role_input)
        layout.addWidget(buttons)

        buttons.accepted.connect(self.handle_login)
        buttons.rejected.connect(self.reject)

    def handle_login(self):
        role = self.role_input.text().strip().lower()
        if role == 'admin':
            pwd, ok = QInputDialog.getText(self, "Password", "Enter admin password:", QLineEdit.Password)
            hashed_input = hashlib.sha256(pwd.encode()).hexdigest()
            if ok and hashed_input == PASSWORD:  # set your admin password here
                self.is_admin = True
                self.accept()

        else:
            self.is_admin = False
            self.accept()
