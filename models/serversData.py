import threading
import time

from models.serverElement import ServerElement


class ServersData:
    def __init__(self, last_update=0, servers_list=None):
        self.last_update: int = last_update
        self.servers_list: list[ServerElement] = servers_list
        self.lock = threading.Lock()

    def update(self, servers_list):
        with self.lock:
            self.servers_list = servers_list
            self.last_update = int(time.time())

    @staticmethod
    def from_json(data):
        last_update = data.get("lastUpdate", 0)
        servers_list_dict = data.get("serversList", [])
        servers_list = [ServerElement().from_json(entry) for entry in servers_list_dict]
        return ServersData(last_update, servers_list)

    def to_dict(self):
        with self.lock:
            return {"lastUpdate": self.last_update,
                    "serversList": [s.to_dict() for s in self.servers_list]}

    def clone(self):
        with self.lock:
            new = ServersData()
            new.last_update = self.last_update
            # deep‐copy only the plain data, not the lock
            new.servers_list = [s.to_dict() for s in self.servers_list]
        return new
