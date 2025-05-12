from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QScrollArea, QLineEdit, QSizePolicy, QDialogButtonBox, QDialog, QInputDialog
)
from PySide6.QtCore import Qt, QThread, Signal

import sys, json, time

from sympy import false

from stylesheet import style

#TODO the css is not applying on the customTitleBar
#TODO add icons for close, minimize, settings like in Dorban

#TODO add logs for each action that has been done
#TODO add logged as viewer or admin
#TODO perform multiple threading to get all servers at once (10 by 10)
#TODO modify the reservation by clicking on it. A window should show with:
# - name of the user
# - what does he want to check
#TODO add icon\
#TODO login as admin
#TODO make a background as card in listTile, and color it (green/red/normal)
#TODO add column for environment
#TODO add checkboxes for: available, occupied, operational, type (gw, microservice, mid, heart, other, emda)
#TODO from: it must be 'since' instead of absolute time
#TODO In the lower right side, display when was the last update of the servers, and add a button for refresh now
#TODO add settings: show scripts from rpmqa ?

class DataThread(QThread):
    data_updated = Signal(list)

    def __init__(self, json_path, interval=5, parent=None):
        super().__init__(parent)
        self.json_path = json_path
        self.interval = interval
        self.running = True

    def run(self):
        while self.running:
            try:
                with open(self.json_path, 'r') as f:
                    data = json.load(f)
                self.data_updated.emit(data)
            except Exception as e:
                print(f"Failed to read JSON: {e}")
            time.sleep(self.interval)

    def stop(self):
        self.running = False

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
        self.minimize_button = QPushButton("-")
        self.minimize_button.setFixedSize(20, 20)
        self.minimize_button.clicked.connect(self.minimize_window)
        layout.addWidget(self.minimize_button)
        self.close_button = QPushButton("x")
        self.close_button.setFixedSize(20, 20)
        self.close_button.clicked.connect(self.close_window)
        layout.addWidget(self.close_button)

    def minimize_window(self):
        self.parent.showMinimized()

    def close_window(self):
        self.parent.close()

    def mousePressEvent(self, event: QMouseEvent):
        self.offset = event.globalPosition().toPoint() - self.parent.pos()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton:
            self.parent.move(event.globalPosition().toPoint() - self.offset)

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

class ListItem(QWidget):
    def __init__(self, host, app, ip, available, action_text, reservation_start, is_admin):
        super().__init__()
        self.host = host
        self.app = app
        self.ip = ip
        self.available = available
        self.reservation_start = reservation_start
        self.action_text = action_text

        layout = QHBoxLayout()
        layout.setSpacing(10)

        label1 = QLabel(host)
        label2 = QLabel(app)
        label_ip = QLabel(ip)
        available_text = QLabel(str(available))
        button = QPushButton(action_text)
        label3 = QLabel(reservation_start)
        button.setEnabled(is_admin)

        # Ensure fixed width for alignment
        for widget, width in zip(
            (label1, label2, label_ip, available_text, button, label3),
            (150, 150, 150, 100, 80, 200)
        ):
            widget.setFixedWidth(width)
            widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
            layout.addWidget(widget)

        self.setLayout(layout)

        if available is True:
            self.setObjectName("availableTrue")
        elif available is False:
            self.setObjectName("availableFalse")
        else:
            self.setObjectName("availableUnknown")

        for lbl in (label1, label2, label_ip, available_text, label3):
            lbl.setObjectName("lineLabel")
        button.setObjectName("lineButton")

    def matches(self, query):
        q = query.lower()
        return (
            q in self.host.lower() or
            q in self.app.lower() or
            q in self.ip.lower() or
            q in str(self.available).lower() or
            q in self.reservation_start.lower() or
            q in self.action_text.lower()
        )

class MainWindow(QWidget):
    def __init__(self, json_path="data.json", update_interval=5, is_admin: bool = false):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        main_layout = QVBoxLayout(self)

        self.is_admin = is_admin

        title_bar = CustomTitleBar(self)
        main_layout.addWidget(title_bar)
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search...")
        self.search_bar.textChanged.connect(self.filter_items)
        main_layout.addWidget(self.search_bar)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        bold_font = QLabel().font()
        bold_font.setBold(True)
        for name, width in zip(
            ("Host", "App", "IP", "Available", "Reservation", "From"),
            (150, 150, 150, 100, 90, 200)
        ):
            lbl = QLabel(name)
            lbl.setFont(bold_font)
            lbl.setFixedWidth(width)
            header_layout.addWidget(lbl)
        main_layout.addLayout(header_layout)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(10)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.items = []
        self.scroll.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll)

        self.thread = DataThread(json_path, interval=update_interval)
        self.thread.data_updated.connect(self.update_items)
        self.thread.start()

    def update_items(self, data_list):
        for item in self.items:
            self.scroll_layout.removeWidget(item)
            item.deleteLater()
        self.items.clear()

        for entry in data_list:
            item = ListItem(
                entry.get("host", ""),
                entry.get("app", ""),
                entry.get("ip", ""),
                entry.get("available", None),
                entry.get("action", ""),
                entry.get("reservation_start", ""),
                self.is_admin
            )
            self.scroll_layout.addWidget(item)
            self.items.append(item)

        self.filter_items(self.search_bar.text())

    def filter_items(self, text):
        for item in self.items:
            item.setVisible(item.matches(text))

    def closeEvent(self, event):
        # Stop background thread forcefully and immediately
        if self.thread.isRunning():
            self.thread.terminate()
            self.thread.wait()

        # Proceed to close the window
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(style)

    # Login
    login = LoginDialog()
    if login.exec() == QDialog.Accepted:
        window = MainWindow(is_admin=login.is_admin)
        window.resize(1000, 600)
        window.show()
        sys.exit(app.exec())