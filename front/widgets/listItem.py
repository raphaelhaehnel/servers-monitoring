from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy

from front.consts import ColumnWidth
from front.widgets.freeServerDialog import FreeServerDialog
from front.widgets.hoverButton import HoverButton
from front.widgets.serverBookingDialog import ServerBookingDialog
from front.utils import set_host_available, book_server, seconds_to_elapsed
from models.filterState import FilterState


class ListItem(QWidget):
    def __init__(self, host, app, ip, env, available, action_text, reservation_start, is_admin, data):
        super().__init__()
        self.host: str = host
        self.app: str = app
        self.ip: str = ip
        self.env: str = env
        self.available: bool = available
        self.reservation_start: int = reservation_start
        self.action_text: str = action_text
        self.data = data

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
        self.action_button = HoverButton(action_text, hover_text, parent=self)
        self.action_button.setEnabled(is_admin)
        self.start_time_label = QLabel(seconds_to_elapsed(reservation_start) if reservation_start != 0 else "0")

        if not available:
            self.action_button.clicked.connect(self.open_free_dialog)
        else:
            self.action_button.clicked.connect(self.open_booking_dialog)


        # Ensure fixed width for alignment
        for widget, width in zip(
                (self.host_label, self.app_label, self.ip_label, self.env_label, self.available_label, self.action_button, self.start_time_label),
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
        self.action_button.setObjectName("lineButton")

    def matches(self, query):
        q = query.lower()
        return (
                q in self.host.lower() or
                q in self.app.lower() or
                q in self.ip.lower() or
                q in self.env.lower() or
                q in str(self.available).lower() or
                q in str(self.reservation_start).lower() or
                q in self.action_text.lower()
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
        # If “Operational” is checked, only show items whose action_text is exactly “operational”
        if state.operational and self.action_text.lower() != "operational":
            return False

        # 3) Type filter
        # If a specific type (not “All”) is selected, require it to appear in the app name
        if state.type != "All":
            if state.type.lower() not in self.app.lower():
                return False

        # Passed all active filters
        return True

    def open_free_dialog(self):
        main_window = self.window()
        if hasattr(main_window, 'data_listener_thread'):
            main_window.data_listener_thread.pause()

        dialog = FreeServerDialog(self.host)
        if dialog.exec():
            print("User confirmed to free the server.")
            set_host_available(self.data, self.host)

        else:
            print("User cancelled the action.")

        if hasattr(main_window, 'refresh_now'):
            main_window.refresh_now()

        # after dialog, resume updates
        if hasattr(main_window, 'data_listener_thread'):
            main_window.data_listener_thread.resume()

    def open_booking_dialog(self):
        main_window = self.window()
        if hasattr(main_window, 'data_listener_thread'):
            main_window.data_listener_thread.pause()

        dialog = ServerBookingDialog(self.host)
        if dialog.exec():
            print("User booked server")
            booking_data = dialog.booking_data()
            book_server(self.data, booking_data.host_name, booking_data.user)

        else:
            print("Booking cancelled")

        if hasattr(main_window, 'refresh_now'):
            main_window.refresh_now()

        # after dialog, resume updates
        if hasattr(main_window, 'data_listener_thread'):
            main_window.data_listener_thread.resume()