import json
from datetime import datetime

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton
from PySide6.QtCore import Qt

from front.column_width import ColumnWidth
from front.widgets.RequestsDialog import RequestsDialog
from front.widgets.customScrollArea import CustomScrollArea
from front.widgets.customTitleBar import CustomTitleBar
from front.widgets.filterPanel import FilterPanel
from front.widgets.footerLayout import FooterLayout
from front.widgets.cardItem import CardItem
from infrastructure.shared_models.shared_clusterView import SharedClusterView
from infrastructure.shared_models.shared_isMaster import SharedIsMaster
from infrastructure.shared_models.shared_serversData import SharedServersData
from infrastructure.shared_models.shared_userRequests import SharedUserRequests
from models.filterState import FilterState
from models.serversData import ServersData


# TODO perform multiple threading to get all servers at once (10 by 10)
# TODO Add sync button for each server (don't make the last update globally) and use this generic function for SSH requests with threads

class MainWindow(QWidget):
    def __init__(self, shared_servers: SharedServersData, shared_cluster: SharedClusterView, shared_requests: SharedUserRequests, shared_master: SharedIsMaster, is_admin: bool):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setObjectName("MainWindow")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 10, 0, 0)

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
        for name, width in zip(("Host", "App", "Status", "Env", "Available", "Reservation"), (
                ColumnWidth.HOST + shift, ColumnWidth.APP + shift, ColumnWidth.IP + shift, ColumnWidth.ENV + shift,
                ColumnWidth.AVAILABLE + shift, ColumnWidth.RESERVATION + shift)):
            lbl = QLabel(name)
            lbl.setFont(bold_font)
            lbl.setFixedWidth(width)
            header_layout.addWidget(lbl)

        # QLabel for arrow
        self.since_arrow = QLabel("")  # start with no arrow
        self.since_arrow.setFont(bold_font)
        self.since_arrow.setFixedWidth(20)
        self.since_arrow.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        header_layout.addWidget(self.since_arrow)

         # QPushButton label
        self.since_btn = QPushButton("Since")
        self.since_btn.setFont(bold_font)
        self.since_btn.setFlat(True)
        self.since_btn.setFixedWidth(ColumnWidth.FROM - shift)
        self.since_btn.clicked.connect(self.cycle_sort)
        header_layout.addWidget(self.since_btn)
        header_layout.addSpacing(20)

        header_layout.setContentsMargins(10, 5, 10, 0)
        main_layout.addLayout(header_layout)

        # sort_mode: 0 = no sort, 1 = ascending, 2 = descending
        self.sort_mode: int = 0

        self.scroll = CustomScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(10)
        self.scroll_layout.setAlignment(Qt.AlignTop)
        self.items: list[tuple[QFrame, CardItem]] = []
        self.scroll.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll)

        # Footer layout
        self.footer_frame = FooterLayout(self, shared_master)
        main_layout.addWidget(self.footer_frame)

        self.shared_servers = shared_servers
        self.shared_servers.dataChanged.connect(self.update_items)
        # When the servers data is being updated in the back, update also the front

        self.shared_is_master = shared_master
        self.shared_is_master.dataChanged.connect(self.footer_frame.update_master_button)
        # When the master is being updated in the back, update also the front

        self.shared_cluster: SharedClusterView = shared_cluster
        self.shared_requests: SharedUserRequests = shared_requests
        self.shared_requests.dataChanged.connect(self.update_request_badge)

        self.update_items()
        print("Initialized the front")

    def cycle_sort(self):
        # cycle 0 → 1 → 2 → 0
        self.sort_mode = (self.sort_mode + 1) % 3

        # update the arrow icon
        if self.sort_mode == 0:
            self.since_arrow.setText("")
        elif self.sort_mode == 1:
            self.since_arrow.setText("▲")
        else:
            self.since_arrow.setText("▼")

        self.update_items(force=True)

    def update_items(self, force=False):
        servers_data: ServersData = self.shared_servers.data

        # 1) If there's no list or it's empty, do nothing (and clear previous_data)
        if not hasattr(servers_data, "servers_list") or not servers_data.servers_list:
            print("There is no loaded data, ignoring update.")
            # Prevent any future clone() calls until we have data
            self.previous_data = None
            return

        # 2) Now that we know we have a proper list, update the footer
        self.refresh_last_update(servers_data.last_update)

        # 3) First-ever build or force-rebuild?
        if self.previous_data is None or force:
            self._full_rebuild(servers_data)
            return

        # --- here follows your “patch-only-the-changed-rows” logic ---
        prev_map = {e.host: e.to_dict() for e in self.previous_data.servers_list}
        curr_map = {e.host: e.to_dict() for e in servers_data.servers_list}

        # 4) Sort current snapshot
        data_list = list(servers_data.servers_list)
        if self.sort_mode == 1:
            data_list.sort(key=lambda s: s.since)
        elif self.sort_mode == 2:
            data_list.sort(key=lambda s: s.since, reverse=True)

        # 5) Compare whole snapshot quickly
        curr_str = json.dumps([e.to_dict() for e in data_list], sort_keys=True)
        prev_str = json.dumps([e.to_dict() for e in self.previous_data.servers_list], sort_keys=True)
        if curr_str == prev_str and not force:
            print("No modification. Items remaining untouched.")
            return

        print("A modification has been detected. Patching changed rows.")

        # 7) For each changed host, replace its row in place
        for idx, (frame, card) in enumerate(self.items):
            host = card.host
            if curr_map.get(host) != prev_map.get(host):
                # remove old
                self.scroll_layout.takeAt(idx)
                frame.deleteLater()

                # find new entry object
                entry = next(e for e in servers_data.servers_list if e.host == host)

                # create new frame+card
                new_frame = QFrame()
                new_frame.setFrameShape(QFrame.StyledPanel)
                new_frame.setObjectName("cardFrame")
                layout = QVBoxLayout(new_frame)
                layout.setContentsMargins(5, 2, 5, 2)

                new_card = CardItem(entry.host, entry.app, entry.status, entry.env, entry.available, entry.reservation,
                    entry.since, entry.comment, self.is_admin, self.shared_is_master.data, self.shared_servers,
                    self.shared_requests)
                layout.addWidget(new_card)

                # insert it back
                self.scroll_layout.insertWidget(idx, new_frame)
                self.items[idx] = (new_frame, new_card)

        # 8) Finally, update previous_data **after** we’ve successfully iterated
        self.previous_data = servers_data.clone()

        # 9) Re-apply filters so the patched rows show/hide correctly
        self.filter_items(self.filter_panel.search_bar.text())
        self.filter_control_items(self.filter_panel.filter_controls.current_filters)

    def _full_rebuild(self, servers_data: ServersData):
        """Tear down everything and rebuild from scratch."""
        # 1) Clear all existing rows
        while self.scroll_layout.count():
            w = self.scroll_layout.takeAt(0).widget()
            if w:
                w.deleteLater()
        self.items.clear()

        # 2) Sort
        data_list = list(servers_data.servers_list)
        if self.sort_mode == 1:
            data_list.sort(key=lambda s: s.since)
        elif self.sort_mode == 2:
            data_list.sort(key=lambda s: s.since, reverse=True)

        # 3) Build every row
        for entry in data_list:
            frame = QFrame()
            frame.setFrameShape(QFrame.StyledPanel)
            frame.setObjectName("cardFrame")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(5, 2, 5, 2)

            card = CardItem(entry.host, entry.app, entry.status, entry.env, entry.available, entry.reservation,
                entry.since, entry.comment, self.is_admin, self.shared_is_master.data, self.shared_servers,
                self.shared_requests)
            layout.addWidget(card)

            self.scroll_layout.addWidget(frame)
            self.items.append((frame, card))

        # 4) Only now that build succeeded do we snapshot
        self.previous_data = servers_data.clone()

        # 5) Apply filters
        self.filter_items(self.filter_panel.search_bar.text())
        self.filter_control_items(self.filter_panel.filter_controls.current_filters)

    def refresh_last_update(self, last_update):
        readable_date = datetime.fromtimestamp(last_update)
        formatted_date = readable_date.strftime("%Y-%m-%d %H:%M:%S")
        self.footer_frame.label_last_update.setText("Last update time: " + formatted_date)

    def filter_items(self, text):
        q = text.lower()
        for card, item in self.items:
            card.setVisible(
                item.matches(q) and item.matches_conditions(self.filter_panel.filter_controls.current_filters))

    def filter_control_items(self, state: FilterState):
        for card, item in self.items:
            card.setVisible(
                item.matches_conditions(state) and item.matches(self.filter_panel.search_bar.text().lower()))

    def show_requests_dialog(self):
        dlg = RequestsDialog(self.shared_servers, self.shared_requests, self.is_admin, self.shared_is_master.data, parent=self)
        dlg.exec()

    def update_request_badge(self):
        request_count = len(self.shared_requests.data.requests)
        self.footer_frame.view_requests_btn.set_count(request_count)