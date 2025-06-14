import json
import time

import requests
from PySide6.QtCore import QThread, Signal

from consts import DATA_PATH
from infrastructure.ip_manager import get_self_id
from models.serverElement import ServerElement
from models.serversData import ServersData


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
                        if prev == get_self_id():
                            user_state = "Master"
                        else:
                            user_state = "Slave"
                        self.master_changed.emit(user_state)
            except:
                pass
            time.sleep(2)

class DataThread(QThread):
    data_updated = Signal(object)

    def __init__(self, interval=5, parent=None):
        super().__init__(parent)
        self.interval = interval
        self.running = True
        self.paused = False

    def run(self):
        while self.running:
            if not self.paused:
                print("DataThread running")
                try:
                    with open(DATA_PATH, 'r') as f:
                        data = json.load(f)
                        servers_data = ServersData().from_json(data)
                    self.data_updated.emit(servers_data)
                except Exception as e:
                    print(f"Failed to read JSON: {e}")
            time.sleep(self.interval)

    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False

    def stop(self):
        self.running = False