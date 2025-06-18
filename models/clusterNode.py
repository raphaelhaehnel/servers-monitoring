from models.role import Role


class ClusterNode:
    def __init__(self, node_ip="", role=None):
        self.nodeIP: str = node_ip
        self.role: Role | None = role

    def from_json(self, data):
        self.nodeIP = data.get("nodeIP", "")
        self.role = data.get("role", None)
        return self

    def to_dict(self):
        return {"nodeIP": self.nodeIP, "role": self.role}