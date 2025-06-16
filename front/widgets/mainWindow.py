import json
from datetime import datetime

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame
from PySide6.QtCore import Qt

from front.column_width import ColumnWidth
from front.widgets.customTitleBar import CustomTitleBar
from front.widgets.filterPanel import FilterPanel
from front.widgets.footerLayout import FooterLayout
from front.widgets.listItem import ListItem
from infrastructure.shared_models.shared_clusterView import SharedClusterView
from infrastructure.shared_models.shared_isMaster import SharedIsMaster
from infrastructure.shared_models.shared_serversData import SharedServersData
from infrastructure.shared_models.shared_userRequests import SharedUserRequests
from models.filterState import FilterState
from models.serversData import ServersData


# TODO add logs for each action that has been done
# TODO add logged as viewer or admin
# TODO perform multiple threading to get all servers at once (10 by 10)
# TODO In the lower right side, display when was the last update of the servers, and add a button for refresh now
# TODO add settings: show scripts from rpmqa ?
# TODO add 'about'
# TODO work on the bottom bar
# TODO add CSS for hovering the button master
# TODO enable the master button only if admin + slave
# TODO Add user-comment and server-comment
# TODO the admin must be automatically be the master
# TODO add mechanism: slave send request to the admin to choose a server. Add a request list for the admin
# TODO add sort by 'since' time

class MainWindow(QWidget):
    def __init__(self, shared_servers: SharedServersData, shared_cluster: SharedClusterView, shared_requests: SharedUserRequests, shared_master: SharedIsMaster, is_admin: bool, update_interval=3):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setObjectName("MainWindow")
        main_layout = QVBoxLayout(self)

        self.is_admin = is_admin
        self.previous_data: ServersData | None = None

        title_bar = CustomTitleBar(self.is_admin, self)
        main_layout.addWidget(title_bar)

        self.filter_panel = FilterPanel()
        self.filter_panel.search_text_changed.connect(self.filter_items)
        self.filter_panel.filter_controls.filters_changed.connect(self.filter_control_items)
        main_layout.addWidget(self.filter_panel)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        bold_font = QLabel().font()
        bold_font.setBold(True)

        shift = 20
        for name, width in zip(("Host", "App", "IP", "Env", "Available", "Reservation", "Since"), (
                ColumnWidth.HOST + shift, ColumnWidth.APP + shift, ColumnWidth.IP + shift, ColumnWidth.ENV + shift,
                ColumnWidth.AVAILABLE + shift, ColumnWidth.RESERVATION + shift, ColumnWidth.FROM + shift)):
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
        self.items: list[tuple[QFrame, ListItem]] = []
        self.scroll.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll)

        # Footer layout
        self.footer_frame = FooterLayout()
        main_layout.addWidget(self.footer_frame)

        self.shared_servers = shared_servers
        self.shared_servers.dataChanged.connect(self.update_items)
        # When the servers data is being updated in the back, update also the front

        self.shared_master = shared_master
        self.shared_master.dataChanged.connect(self.update_master_button)
        # When the master is being updated in the back, update also the front

        self.update_items()
        print("Initialized the front")

    def update_items(self):
        servers_data = self.shared_servers.data
        readable_date = datetime.fromtimestamp(servers_data.last_update)
        formatted_date = readable_date.strftime("%Y-%m-%d %H:%M:%S")
        self.footer_frame.label_last_update.setText("Last update time: " + formatted_date)

        # Compare current and previous data using a JSON string dump for simplicity
        current_data_str = json.dumps([s.to_dict() for s in servers_data.servers_list], sort_keys=True)

        if self.previous_data is not None:
            previous_data_str = json.dumps([s.to_dict() for s in self.previous_data.servers_list], sort_keys=True)
            if current_data_str == previous_data_str:
                return

        print("A modification has been detected. Updating items.")
        self.previous_data = servers_data.clone

        # Remove every widget in the scroll_layout
        while self.scroll_layout.count():
            w = self.scroll_layout.takeAt(0).widget()
            if w:
                w.deleteLater()
        self.items.clear()

        for entry in servers_data.servers_list:
            card = QFrame()
            card.setFrameShape(QFrame.StyledPanel)
            card.setObjectName("cardFrame")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(5, 2, 5, 2)

            item = ListItem(entry.host, entry.app, entry.ip, entry.env, entry.available, entry.action, entry.since,
                            self.is_admin, self.previous_data)
            card_layout.addWidget(item)
            self.scroll_layout.addWidget(card)
            self.items.append((card, item))

        self.filter_items(self.filter_panel.search_bar.text())
        self.filter_control_items(self.filter_panel.filter_controls.current_filters)

    def filter_items(self, text):
        q = text.lower()
        for card, item in self.items:
            card.setVisible(
                item.matches(q) and item.matches_conditions(self.filter_panel.filter_controls.current_filters))

    def filter_control_items(self, state: FilterState):
        for card, item in self.items:
            card.setVisible(
                item.matches_conditions(state) and item.matches(self.filter_panel.search_bar.text().lower()))

    def update_master_button(self):
        self.footer_frame.btn_master.setText("Master" if self.shared_master.data else "Slave")
        if self.shared_master.data:
            self.footer_frame.btn_master.setStyleSheet("background-color: #388e3c")
            self.footer_frame.btn_master.setEnabled(False)
        else:
            self.footer_frame.btn_master.setStyleSheet("background-color: #d32f2f")
            self.footer_frame.btn_master.setEnabled(True)
