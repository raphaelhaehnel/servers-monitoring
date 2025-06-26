class ServerElement:
    def __init__(self):
        self.host: str = ""
        self.app: str = ""
        self.ip: str = ""
        self.env: str = ""
        self.available: bool | None = None
        self.reservation: str = ""
        self.since: int = 0
        self.comment: str = ""

    def from_json(self, data_element: dict):
        self.host = data_element.get("host", "")
        self.app = data_element.get("app", "")
        self.ip = data_element.get("ip", "")
        self.env = data_element.get("env", "")
        self.available = data_element.get("available", None)
        self.reservation = data_element.get("reservation", "")
        self.since = data_element.get("since", 0)
        self.comment = data_element.get("comment", "")
        return self

    def to_dict(self):
        return {"host": self.host, "app": self.app, "ip": self.ip, "env": self.env, "available": self.available,
                "reservation": self.reservation, "since": self.since, "comment": self.comment}

    def clone(self):
        new = ServerElement()
        new.host = self.host
        new.app = self.app
        new.ip = self.ip
        new.env = self.env
        new.available = self.available
        new.reservation = self.reservation
        new.since = self.since
        new.comment = self.comment
        return new