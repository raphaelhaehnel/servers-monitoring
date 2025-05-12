from PySide6.QtWidgets import QInputDialog, QLineEdit, QLabel, QDialogButtonBox, QVBoxLayout, QDialog


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
            if ok and pwd == 'admin123':  # set your admin password here
                self.is_admin = True
                self.accept()
            else:
                QLabel("Incorrect password").show()
        else:
            self.is_admin = False
            self.accept()
