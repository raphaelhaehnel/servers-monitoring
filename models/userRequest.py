from models.operationType import OperationType


class UserRequest:
    def __init__(self):
        self.nodeIP: str = ""
        self.timestamp: int = 0
        self.operation: OperationType | None = None
        self.serverHost: str = ""
        self.comment: str = ""

    def from_json(self, data):
        self.nodeIP = data.get("nodeIP", "")
        self.timestamp = data.get("timestamp", 0)
        self.operation = data.get("operation", None)
        self.serverHost = data.get("serverHost", "")
        self.comment = data.get("comment", "")
        return self

    def to_dict(self):
        return {"nodeIP": self.nodeIP, "timestamp": self.timestamp, "operation": self.operation,
                "serverHost": self.serverHost, "comment": self.comment}
