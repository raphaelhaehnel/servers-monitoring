import hashlib
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
        self.manual_master = manual_master
        self.current_master = None
        self.lock = threading.Lock()
        self.running = True

        self.elect_port = config.get('election_port', config['broadcast_port'] + 1)
        # Combined socket for listening and broadcasting
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', self.elect_port))

        # Cooldown to prevent rapid re-election
        self.cooldown = config.get('election_cooldown', 10)
        self.last_election_time = 0

        # Epoch counter for varying RNG seed
        self.epoch = 0

        threading.Thread(target=self._listen_loop, daemon=True).start()

    def start(self):
        threading.Thread(target=self._election_loop, daemon=True).start()

    def _listen_loop(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                msg = json.loads(data)
                msg_type = msg.get('type')
                master_id = msg.get('id')
                if msg_type == 'master':
                    with self.lock:
                        # update only if within cooldown or better priority
                        if (self.current_master != master_id and
                            (time.time() - self.last_election_time) < self.cooldown or
                            self._compare_priority(master_id, self.current_master)):
                            self.current_master = master_id
                            logger.info(f"Synchronized master update: {master_id}")
            except Exception as e:
                logger.error(f"Error in listen loop: {e}")

    def _compare_priority(self, a, b):
        cfg = {p['id']: p['priority'] for p in self.config['peers']}
        pa = cfg.get(a, float('inf'))
        pb = cfg.get(b, float('inf'))
        if pa != pb:
            return pa < pb
        return a < b

    def _broadcast_master(self, master_id):
        msg = json.dumps({'type': 'master', 'id': master_id}).encode()
        self.sock.sendto(msg, ('<broadcast>', self.elect_port))

    def _election_loop(self):
        interval = self.config.get('heartbeat_interval', 5)
        while self.running:
            time.sleep(interval)
            now = time.time()
            if now - self.last_election_time < self.cooldown:
                continue
            with self.lock:
                self.epoch += 1
                if self.manual_master:
                    winner = self.self_id
                else:
                    # Gather active peers (prune stopped nodes)
                    active = self.discovery.get_active_peers() | {self.self_id}
                    candidates = sorted(active)
                    if not candidates:
                        continue
                    # Compute priorities
                    cfg = {p['id']: p['priority'] for p in self.config['peers']}
                    default_pr = max(cfg.values(), default=0) + 1
                    scored = [(cfg.get(c, default_pr), c) for c in candidates]
                    min_pr = min(pr for pr, _ in scored)
                    top = [c for pr, c in scored if pr == min_pr]
                    # synchronized random seed using epoch
                    seed_blob = {'candidates': sorted(candidates), 'epoch': self.epoch}
                    blob = json.dumps(seed_blob, sort_keys=True)
                    seed = int(hashlib.sha256(blob.encode()).hexdigest(), 16)
                    winner = random.Random(seed).choice(top)
                # Set and announce
                self.current_master = winner
                self.last_election_time = now
                logger.info(f"Elected master after consensus: {winner}")
                self._broadcast_master(winner)

    def resign(self):
        with self.lock:
            self.running = False
            logger.info(f"{self.self_id} resigning")

    def get_master(self):
        with self.lock:
            return self.current_master
