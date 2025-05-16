import threading, time, json, socket, hashlib, random
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

        # Election ports
        self.elect_port = config.get('election_port', config['broadcast_port'] + 1)

        # Socket for listening election broadcasts
        self.listen_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listen_sock.bind(('', self.elect_port))

        # Socket for sending election broadcasts
        self.elect_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.elect_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        self.epoch = 0
        self.seen_packets = {}

    def start(self):
        threading.Thread(target=self._listen_loop, daemon=True).start()
        threading.Thread(target=self._election_loop, daemon=True).start()

    def _listen_loop(self):
        while self.running:
            data, _ = self.listen_sock.recvfrom(65536)
            try:
                pkt = json.loads(data)
                if pkt.get('type') == 'election':
                    e = pkt['epoch']
                    self.seen_packets.setdefault(e, pkt)
            except Exception:
                continue

    def _election_loop(self):
        interval = self.config.get('heartbeat_interval', 5)
        while self.running:
            self.epoch += 1
            # prepare election packet
            cand = sorted(self.discovery.peers | {self.self_id})
            pkt = {'type': 'election', 'peers': cand, 'epoch': self.epoch}

            # broadcast election packet
            self.elect_sock.sendto(json.dumps(pkt).encode(), ('<broadcast>', self.elect_port))

            # wait window
            time.sleep(interval)

            # pick packet (ours if none received)
            chosen = self.seen_packets.pop(self.epoch, pkt)

            # build priority map
            cfg = {p['id']: p['priority'] for p in self.config['peers']}
            maxp = max(cfg.values(), default=0)
            default_p = maxp + 1

            # score candidates
            scored = [(cfg.get(c, default_p), c) for c in chosen['peers']]
            min_pr = min(pr for pr, _ in scored)
            top = [c for pr, c in scored if pr == min_pr]

            # deterministic randomness
            blob = json.dumps(chosen, sort_keys=True)
            seed = int(hashlib.sha256(blob.encode()).hexdigest(), 16)
            winner = random.Random(seed).choice(top) if top else self.self_id

            with self.lock:
                self.current_master = self.self_id if self.manual_master else winner
            logger.info(f"Elected master: {self.current_master}")

    def resign(self):
        with self.lock:
            self.running = False

    def get_master(self):
        with self.lock:
            return self.current_master