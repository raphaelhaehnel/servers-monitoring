from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy

from front.consts import ColumnWidth
from front.widgets.freeServerDialog import FreeServerDialog
from front.widgets.hoverButton import HoverButton
from front.widgets.serverBookingDialog import ServerBookingDialog


class ListItem(QWidget):
    def __init__(self, host, app, ip, env, available, action_text, reservation_start, is_admin):
        super().__init__()
        self.host = host
        self.app = app
        self.ip = ip
        self.env = env
        self.available = available
        self.reservation_start = reservation_start
        self.action_text = action_text

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
        self.start_time_label = QLabel(reservation_start)

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
                q in self.reservation_start.lower() or
                q in self.action_text.lower()
        )

    def open_free_dialog(self):
        dialog = FreeServerDialog(self.host)
        if dialog.exec():
            print("User confirmed to free the server.")
            self.available_label.setText("True")
            #TODO write to json
        else:
            print("User cancelled the action.")

    def open_booking_dialog(self):
        dialog = ServerBookingDialog(self.host)
        if dialog.exec():
            data = dialog.booking_data()
            self.action_button.setDefaultText(data["user"])
            #TODO write to json
        else:
            print("Booking cancelled")