import json
import time

import requests
from PySide6.QtCore import QThread, Signal


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