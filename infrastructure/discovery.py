import socket
import threading
import json
from infrastructure.utils import load_config, get_self_id, setup_logger

logger = setup_logger()

class Discovery:
    def __init__(self, config):
        self.config = config
        self.peers = set()
        self.self_id = get_self_id()
        self.port = config['broadcast_port']
        self.running = True

    def start(self):
        threading.Thread(target=self.listen, daemon=True).start()
        threading.Thread(target=self.broadcast_loop, daemon=True).start()

    def broadcast_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        msg = json.dumps({ 'type': 'hello', 'id': self.self_id }).encode()
        while self.running:
            sock.sendto(msg, ('<broadcast>', self.port))
            threading.Event().wait(self.config.get('heartbeat_interval', 5))

    def listen(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', self.port))
        while self.running:
            data, addr = sock.recvfrom(1024)
            try:
                msg = json.loads(data)
                if msg.get('type') == 'hello':
                    peer_id = msg.get('id')
                    self.peers.add(peer_id)
            except Exception as e:
                logger.error(f"Malformed discovery message: {e}")

    def stop(self):
        self.running = False