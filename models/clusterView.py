import threading

from models.clusterNode import ClusterNode


class ClusterView:
    def __init__(self):
        self.nodes: list[ClusterNode] = []
        self.lock = threading.Lock()

    def from_json(self, data):
        self.nodes = [ClusterNode().from_json(entry) for entry in data]
        return self

    def add_or_update(self, node_ip, role):
        with self.lock:
            for n in self.nodes:
                if n.nodeIP == node_ip:
                    n.role = role
                    return
            self.nodes.append(ClusterNode(node_ip, role))

    def remove(self, node_ip):
        with self.lock:
            self.nodes = [n for n in self.nodes if n.nodeIP != node_ip]

    def to_list(self):
        with self.lock:
            return [n.to_dict() for n in self.nodes]

    def get_highest_ip(self):
        with self.lock:
            if not self.nodes:
                return None
            return max(self.nodes, key=lambda node: node.nodeIP)

    def to_dict(self):
        with self.lock:
            return [n.to_dict() for n in self.nodes]