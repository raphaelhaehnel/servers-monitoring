import requests
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QLineEdit, QFrame
from PySide6.QtCore import Qt, QThread, Signal

import sys, json, time
from consts import ColumnWidth
from front.stylesheet import style
from infrastructure.utils import seconds_to_elapsed
from widgets.customTitleBar import CustomTitleBar
from widgets.footerLayout import FooterLayout
from widgets.listItem import ListItem


# TODO add logs for each action that has been done
# TODO add logged as viewer or admin
# TODO perform multiple threading to get all servers at once (10 by 10)
# TODO modify the reservation by clicking on it. A window should show with:
# TODO - name of the user
# TODO - what does he want to check
# TODO add checkboxes for: available, occupied, operational, type (gw, microservice, mid, heart, other, emda)
# TODO In the lower right side, display when was the last update of the servers, and add a button for refresh now
# TODO add settings: show scripts from rpmqa ?
# TODO vertical alignment with the header
# TODO add 'about'
# TODO add border for the title bar
# TODO work on the bottom bar
# TODO use P2P mechanism
# TODO use priority list
# TODO Add button 'Be master' (only for admin) and slave for the others

class MasterThread(QThread):
    master_changed = Signal(str)
    def run(self):
        prev = None
        while True:
            try:
                r = requests.get("http://localhost:8000/master", timeout=1)
                if r.ok:
                    m = r.text
                    if m != prev:
                        prev = m
                        self.master_changed.emit(m)
            except:
                pass
            time.sleep(2)

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


class MainWindow(QWidget):
    def __init__(self, json_path=r"C:\Users\haehn\PycharmProjects\Playground\data.json", update_interval=3, is_admin: bool = False):
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
        self.items = []
        self.scroll.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll)

        # Footer layout
        self.footer_frame = FooterLayout()
        main_layout.addWidget(self.footer_frame)

        self.master_thread = MasterThread()
        self.master_thread.master_changed.connect(self.footer_frame.btn_master.setText)
        self.master_thread.start()
        
        self.thread = DataThread(json_path, interval=update_interval)
        self.thread.data_updated.connect(self.update_items)
        self.thread.start()

    def update_items(self, data_list):
        # remove every widget in the scroll_layout
        while self.scroll_layout.count():
            w = self.scroll_layout.takeAt(0).widget()
            if w:
                w.deleteLater()
        self.items.clear()

        for entry in data_list:
            card = QFrame()
            card.setFrameShape(QFrame.StyledPanel)
            card.setObjectName("cardFrame")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(5, 2, 5, 2)

            item = ListItem(entry.get("host", ""), entry.get("app", ""), entry.get("ip", ""), entry.get("env", ""),
                            entry.get("available", None), entry.get("action", ""), seconds_to_elapsed(entry.get("since", "")),
                            self.is_admin)
            card_layout.addWidget(item)
            self.scroll_layout.addWidget(card)
            self.items.append((card, item))

        self.filter_items(self.search_bar.text())

    def filter_items(self, text):
        q = text.lower()
        for card, item in self.items:
            card.setVisible(item.matches(q))

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

    window = MainWindow(is_admin=False)
    window.resize(1000, 600)
    window.show()
    sys.exit(app.exec())
