class UserRequest:
    def __init__(self, nodeIP="", timestamp=0, available=False, host="", user="", comment=""):
        self.nodeIP: str = nodeIP
        self.timestamp: int = timestamp
        self.available: bool = available
        self.host: str = host
        self.user: str = user
        self.comment: str = comment

    def from_json(self, data):
        self.nodeIP = data.get("nodeIP", "")
        self.timestamp = data.get("timestamp", 0)
        self.available = data.get("operation", False)
        self.host = data.get("host", "")
        self.user = data.get("user", "")
        self.comment = data.get("comment", "")
        return self

    def to_dict(self):
        return {"nodeIP": self.nodeIP, "timestamp": self.timestamp, "available": self.available, "host": self.host,
                "user": self.user, "comment": self.comment}
