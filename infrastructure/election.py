import threading
import random
import time
import socket
import json
from infrastructure.utils import setup_logger, load_config, get_self_id

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

    def start(self):
        threading.Thread(target=self.election_loop, daemon=True).start()

    def election_loop(self):
        while self.running:
            self.try_elect()
            time.sleep(self.config.get('heartbeat_interval', 5))

    def try_elect(self):
        with self.lock:
            if self.manual_master:
                self.current_master = self.self_id
                return
            # gather candidates: known peers + self
            candidates = list(self.peers | {self.self_id})
            priorities = {p['id']: p['priority'] for p in self.config['peers']}
            # choose min priority
            min_prio = min(priorities.get(pid, float('inf')) for pid in candidates)
            top = [pid for pid in candidates if priorities.get(pid)==min_prio]
            if not top:
                # no valid candidates yet—fall back to self
                self.current_master = self.self_id
            else:
                self.current_master = random.choice(top)
            logger.info(f"Elected master: {self.current_master}")

    def resign(self):
        with self.lock:
            self.running = False
            logger.info(f"{self.self_id} resigning mastership")

    def get_master(self):
        with self.lock:
            return self.current_master