from datetime import datetime
from functools import partial

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidgetItem, QTableWidget, QVBoxLayout, QDialog, QPushButton, QWidget, QHBoxLayout

from front.utils import book_server, free_server
from infrastructure.shared_models.shared_serversData import SharedServersData
from infrastructure.shared_models.shared_userRequests import SharedUserRequests
from infrastructure.validator import validate_user_request
from models.userRequest import UserRequest


class RequestsDialog(QDialog):
    def __init__(self, shared_servers: SharedServersData, shared_requests: SharedUserRequests, is_admin: bool, is_master: bool, parent=None):
        super().__init__(parent)
        self.setWindowTitle("User Requests")
        self.resize(650, 400)

        self.is_admin = is_admin
        self.is_master = is_master
        self.shared_requests = shared_requests
        self.shared_servers = shared_servers

        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 6, self)
        self.table.setHorizontalHeaderLabels(["User", "Time", "Available", "Host", "Comment", "Action"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setShowGrid(False)
        self.table.setFrameShape(QTableWidget.NoFrame)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        self.shared_requests.dataChanged.connect(self.populate_table)
        self.populate_table()

    def populate_table(self):
        reqs: list[UserRequest] = self.shared_requests.data.requests or []
        self.table.setRowCount(len(reqs))

        for row, r in enumerate(reqs):
            self.table.setItem(row, 0, QTableWidgetItem(r.user))
            self.table.item(row, 0).setTextAlignment(Qt.AlignCenter)
            self.table.setRowHeight(row, 40)

            t = datetime.fromtimestamp(r.timestamp)
            self.table.setItem(row, 1, QTableWidgetItem(t.strftime("%Y-%m-%d %H:%M:%S")))
            self.table.item(row, 1).setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 2, QTableWidgetItem("Yes" if r.available else "No"))
            self.table.item(row, 2).setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 3, QTableWidgetItem(r.host))
            self.table.item(row, 3).setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, QTableWidgetItem(r.comment))
            self.table.item(row, 4).setTextAlignment(Qt.AlignCenter)

            # Add Accept button
            button = QPushButton("Accept")
            button.setEnabled(self.is_admin and self.is_master)
            button.clicked.connect(partial(self.accept_request, r))

            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(button)
            layout.setAlignment(Qt.AlignCenter)
            self.table.setCellWidget(row, 5, container)
        self.table.resizeColumnsToContents()

    def accept_request(self, req: UserRequest):
        if validate_user_request(self.shared_servers.data, req):
            if not req.available:
                book_server(self.shared_servers.data, req.host, req.user, req.comment)
            else:
                free_server(self.shared_servers.data, req.host, req.comment)

            print(f"Request for host {req.host} accepted")
        else:
            print(f"Request for host {req.host} not valid. Deleting.")

        self.shared_requests.data.requests.remove(req)
        self.shared_requests.dataChanged.emit()
        self.shared_servers.dataChanged.emit()
