import socket
import threading
import json
import time
from infrastructure.utils import get_self_id, setup_logger

logger = setup_logger()

class Discovery:
    def __init__(self, config):
        self.config = config
        self.peers = {}  # id -> last_seen timestamp
        self.self_id = get_self_id()
        self.port = config['broadcast_port']
        self.timeout = config.get('heartbeat_timeout', 15)
        self.running = True

        # socket for broadcast and listening
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', self.port))

    def start(self):
        threading.Thread(target=self._broadcast_loop, daemon=True).start()
        threading.Thread(target=self._listen_loop, daemon=True).start()

    def _broadcast_loop(self):
        msg = json.dumps({'type': 'hello', 'id': self.self_id}).encode()
        while self.running:
            self.sock.sendto(msg, ('<broadcast>', self.port))
            time.sleep(self.config.get('heartbeat_interval', 5))

    def _listen_loop(self):
        while self.running:
            data, _ = self.sock.recvfrom(1024)
            try:
                msg = json.loads(data)
                if msg.get('type') == 'hello':
                    self.peers[msg['id']] = time.time()
            except Exception as e:
                logger.error(f"Malformed discovery message: {e}")

    def get_active_peers(self):
        now = time.time()
        return {pid for pid, ts in self.peers.items() if now - ts <= self.timeout}

    def stop(self):
        self.running = False