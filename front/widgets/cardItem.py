import time

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy, QMessageBox

from front.column_width import ColumnWidth
from front.widgets.freeServerDialog import FreeServerDialog
from front.widgets.hoverButton import HoverButton
from front.widgets.serverBookingDialog import ServerBookingDialog
from front.utils import free_server, book_server, seconds_to_elapsed
from infrastructure.shared_models.shared_serversData import SharedServersData
from infrastructure.shared_models.shared_userRequests import SharedUserRequests
from models.filterState import FilterState
from models.serversData import ServersData
from models.userRequest import UserRequest


class CardItem(QWidget):
    def __init__(self, host, app, ip, env, available, reservation_text, since, comment, is_admin, is_master, shared_servers, shared_users_requests):
        super().__init__()
        self.host: str = host
        self.app: str = app
        self.ip: str = ip
        self.env: str = env
        self.available: bool = available
        self.since: int = since
        self.reservation_text: str = "Available" if self.available == True else reservation_text
        self.shared_servers: SharedServersData = shared_servers
        self.shared_users_requests: SharedUserRequests = shared_users_requests
        self.comment: str = comment
        self.can_perform_action = is_admin and is_master

        self.setToolTip(f"{comment}")

        layout = QHBoxLayout()
        layout.setSpacing(10)

        self.host_label = QLabel(host)
        self.app_label = QLabel(app)
        self.ip_label = QLabel(ip)
        self.env_label = QLabel(env)
        self.available_label = QLabel(str(available))
        if not available:
            hover_text = "Free server"
        else:
            hover_text = "Book it!"
        self.reservation_button = HoverButton(self.reservation_text, hover_text, parent=self)
        self.start_time_label = QLabel(seconds_to_elapsed(since) if since != -1 else "")

        if not available:
            self.reservation_button.clicked.connect(self.open_free_dialog)
        else:
            self.reservation_button.clicked.connect(self.open_booking_dialog)


        # Ensure fixed width for alignment
        for widget, width in zip(
                (self.host_label, self.app_label, self.ip_label, self.env_label, self.available_label, self.reservation_button, self.start_time_label),
                (ColumnWidth.HOST, ColumnWidth.APP, ColumnWidth.IP, ColumnWidth.ENV, ColumnWidth.AVAILABLE,
                 ColumnWidth.RESERVATION, ColumnWidth.FROM)):
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

        for lbl in (self.host_label, self.app_label, self.ip_label, self.env_label, self.available_label, self.start_time_label):
            lbl.setObjectName("lineLabel")
        self.reservation_button.setObjectName("lineButton")

    def matches(self, query):
        q = query.lower()
        return (
                q in self.host.lower() or
                q in self.app.lower() or
                q in self.ip.lower() or
                q in self.env.lower() or
                q in str(self.available).lower() or
                q in str(self.since).lower() or
                q in self.reservation_text.lower()
        )

    def matches_conditions(self, state: FilterState):
        # 1) Availability filter
        # If “Available” is checked, hide any non-available servers
        if state is None:
            return True

        if state.available and not self.available:
            return False
        # If “Busy” is checked, hide any available servers
        if state.busy and self.available:
            return False
        # If neither “Available” nor “Busy” is checked, we skip availability filtering entirely

        # 2) Operational filter
        # If “Operational” is checked, only show items whose reservation_text is exactly “operational”
        if state.operational and self.reservation_text.lower() != "operational":
            return False

        # 3) Type filter
        # If a specific type (not “All”) is selected, require it to appear in the app name
        if state.type != "All":
            if state.type.lower() not in self.app.lower():
                return False

        if state.env != "All":
            if state.env.lower() != self.env.lower():
                return False

        # Passed all active filters
        return True

    def open_free_dialog(self):
        if not self.can_perform_action:
            result = QMessageBox.question(None, "Permission required",
                "You cannot free the server directly.\nDo you want to send a request instead?",
                QMessageBox.Yes | QMessageBox.No)
            if result != QMessageBox.Yes:
                print("User cancelled the request.")
                return

        dialog = FreeServerDialog(self.host)
        if dialog.exec():
            try:
                if self.can_perform_action:
                    free_server(self.shared_servers.data, self.host)
                    self.shared_servers.dataChanged.emit()
                    print("User confirmed to free the server.")
                else:
                    self.request_free_server()
                    print("User requested to free the server.")

            except RuntimeError:
                QMessageBox.critical(None, "Item Modified", "This server's data has changed during the operation.\n"
                                                            "Please try again.")
        else:
            print("User cancelled the action.")


    def open_booking_dialog(self):
        if not self.can_perform_action:
            result = QMessageBox.question(None, "Permission required",
                                          "You cannot book this server directly.\nDo you want to send a booking request instead?",
                                          QMessageBox.Yes | QMessageBox.No)
            if result != QMessageBox.Yes:
                print("User cancelled the request.")
                return

        dialog = ServerBookingDialog(self.host, self.comment)
        if dialog.exec():
            try:
                booking_data = dialog.booking_data()
                if self.can_perform_action:
                    book_server(self.shared_servers.data, booking_data.host_name, booking_data.user, booking_data.comment)
                    self.shared_servers.dataChanged.emit()
                    print("User booked server")
                else:
                    self.request_book_server(booking_data)
                    print("User requested to book the server.")

            except RuntimeError:
                QMessageBox.critical(None, "Item Modified", "This server's data has changed during the operation.\n"
                                                            "Please try again.")

    def request_free_server(self):
        self.shared_users_requests.data.requests.append(UserRequest(timestamp=time.time(),
                                                                    available=True,
                                                                    host=self.host,
                                                                    user="",
                                                                    comment=""))
        self.shared_users_requests.dataChanged.emit()

    def request_book_server(self, booking_data):
        self.shared_users_requests.data.requests.append(UserRequest(timestamp=time.time(),
                                                                    available=False,
                                                                    host=self.host,
                                                                    user=booking_data.user,
                                                                    comment=booking_data.comment))
        self.shared_users_requests.dataChanged.emit()