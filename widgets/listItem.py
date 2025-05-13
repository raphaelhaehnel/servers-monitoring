from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QSizePolicy

from consts import ColumnWidth


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

        label1 = QLabel(host)
        label2 = QLabel(app)
        label_ip = QLabel(ip)
        label4 = QLabel(env)
        available_text = QLabel(str(available))
        button = QPushButton(action_text)
        label3 = QLabel(reservation_start)
        button.setEnabled(is_admin)

        # Ensure fixed width for alignment
        for widget, width in zip(
                (label1, label2, label_ip, label4, available_text, button, label3),
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

        for lbl in (label1, label2, label_ip, label4, available_text, label3):
            lbl.setObjectName("lineLabel")
        button.setObjectName("lineButton")

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
