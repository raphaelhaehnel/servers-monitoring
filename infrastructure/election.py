import threading
import time
import json
import socket
import random
from infrastructure.utils import setup_logger, get_self_id

logger = setup_logger()

class LeaderElection:
    def __init__(self, config, discovery, manual_master=False):
        self.config = config
        self.discovery = discovery
        self.self_id = get_self_id()
        self.peers = discovery.peers
        self.manual_master = manual_master
        self.current_master = None
        self.lock = threading.Lock()
        self.running = True
        self.elect_port = config.get('broadcast_port', 50002)

        # Synchronization between nodes
        self.listen_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.listen_sock.bind(('', self.elect_port))

        threading.Thread(target=self._listen_loop, daemon=True).start()

    def start(self):
        threading.Thread(target=self._election_loop, daemon=True).start()

    def _listen_loop(self):
        while self.running:
            try:
                data, addr = self.listen_sock.recvfrom(1024)
                msg = json.loads(data)
                if msg.get('type') == 'election':
                    self._process_election(msg['id'])
                elif msg.get('type') == 'master':
                    self._update_master(msg['id'])
            except Exception as e:
                logger.error(f"Error in election listener: {e}")

    def _process_election(self, sender_id):
        with self.lock:
            # If the message comes from a higher-priority peer, update current master
            if self.current_master is None or sender_id < self.current_master:
                self.current_master = sender_id
                logger.info(f"Received election message from {sender_id}, updating master.")
                self._broadcast_master(sender_id)

    def _broadcast_master(self, master_id):
        msg = json.dumps({'type': 'master', 'id': master_id}).encode()
        self.listen_sock.sendto(msg, ('<broadcast>', self.elect_port))

    def _update_master(self, master_id):
        with self.lock:
            if master_id != self.current_master:
                self.current_master = master_id
                logger.info(f"Synchronized master update: {master_id}")

    def _election_loop(self):
        while self.running:
            with self.lock:
                if self.manual_master:
                    self.current_master = self.self_id
                    self._broadcast_master(self.self_id)
                    continue

                # Collect active peers including self
                candidates = sorted(list(set(self.discovery.peers.keys()) | {self.self_id}))
                if not candidates:
                    time.sleep(1)
                    continue

                # Synchronize election by broadcasting an election message
                self._broadcast_master(self.self_id)

                # Wait briefly to collect responses
                time.sleep(1)

                # Finalize master based on received updates
                if self.current_master is None or self.current_master not in candidates:
                    self.current_master = random.choice(candidates)
                    logger.info(f"Elected master after sync: {self.current_master}")
                    self._broadcast_master(self.current_master)

            time.sleep(self.config.get('heartbeat_interval', 5))

    def resign(self):
        with self.lock:
            self.running = False
            logger.info(f"{self.self_id} resigning mastership")

    def get_master(self):
        with self.lock:
            return self.current_master