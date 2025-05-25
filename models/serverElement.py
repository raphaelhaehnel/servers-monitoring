class ServerElement:
    def __init__(self):
        self.host: str = ""
        self.app: str = ""
        self.ip: str = ""
        self.env: str = ""
        self.available: bool | None = None
        self.action: str = ""
        self.since: int = 0
        self.comment: str = ""

    def from_json(self, data_element: dict):
        self.host = data_element.get("host", "")
        self.app = data_element.get("app", "")
        self.ip = data_element.get("ip", "")
        self.env = data_element.get("env", "")
        self.available = data_element.get("available", None)
        self.action = data_element.get("action", "")
        self.since = data_element.get("since", 0)
        self.comment = data_element.get("comment", "")
        return self

    def to_dict(self):
        return {"host": self.host, "app": self.app, "ip": self.ip, "env": self.env, "available": self.available,
                "action": self.action, "since": self.since, "comment": self.comment}
