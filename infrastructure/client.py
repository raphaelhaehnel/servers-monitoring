import socket
import json
from infrastructure.utils import load_config, get_self_id

class PeerClient:
    def __init__(self, election, config):
        self.election = election
        self.config = config
        self.port = config['tcp_port']
        self.self_id = get_self_id()

    def fetch(self):
        master = self.election.get_master()
        if master is None:
            raise RuntimeError("No master elected yet")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((master, self.port))
            sock.send(b'get_status')
            data = sock.recv(10_000_000)
        if data == b"not_master":
            raise RuntimeError(f"Master ({master}) refuses request")
        return json.loads(data)