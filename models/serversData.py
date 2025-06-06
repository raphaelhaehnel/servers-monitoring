import threading
import time

from models.serverElement import ServerElement


class ServersData:
    def __init__(self):
        self.last_update: int = 0
        self.servers_list: list[ServerElement] = []
        self.lock = threading.Lock()

    def update(self, servers_list):
        with self.lock:
            self.servers_list = servers_list
            self.last_update = int(time.time())

    def from_json(self, data):
        self.last_update = data.get("lastUpdate", 0)
        servers_list_dict = data.get("serversList", [])
        self.servers_list = [ServerElement().from_json(entry) for entry in servers_list_dict]
        return self

    def to_dict(self):
        with self.lock:
            return {"lastUpdate": self.last_update,
                    "serversList": [s.to_dict() for s in self.servers_list]}

