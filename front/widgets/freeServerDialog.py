from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QLineEdit


class FreeServerDialog(QDialog):
    def __init__(self, server_name, comment, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Confirm Server Release")
        self.server_name = server_name

        # Confirmation message
        message = f"Do you really want to free the server '{self.server_name}'?"
        self.label = QLabel(message)

        # Comment field
        self.comment_label = QLabel("Comment:")
        self.comment_edit = QLineEdit()
        self.comment_edit.setText(comment)

        # Yes / Cancel buttons
        self.yes_button = QPushButton("Yes")
        self.cancel_button = QPushButton("Cancel")
        self.yes_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        # Layout the form
        form_layout = QVBoxLayout()
        form_layout.addWidget(self.label)
        form_layout.addWidget(self.comment_label)
        form_layout.addWidget(self.comment_edit)

        # Layout the buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.yes_button)
        button_layout.addWidget(self.cancel_button)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.addLayout(form_layout)
        main_layout.addLayout(button_layout)
