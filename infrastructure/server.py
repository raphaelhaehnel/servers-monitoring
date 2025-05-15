import socket
import threading
import json
from election import LeaderElection
from ssh_manager import SSHManager
from infrastructure.utils import load_config, setup_logger

logger = setup_logger()

class MasterServer:
    def __init__(self, election, config):
        self.election = election
        self.config = config
        self.ssh = SSHManager(config)
        self.port = config['tcp_port']
        self.running = True

    def start(self):
        threading.Thread(target=self.serve_loop, daemon=True).start()

    def serve_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', self.port))
        sock.listen(5)
        while self.running:
            conn, addr = sock.accept()
            threading.Thread(target=self.handle, args=(conn,), daemon=True).start()

    def handle(self, conn):
        data = conn.recv(1024)
        msg = data.decode()
        if msg == 'get_status':
            master = self.election.get_master()
            if master != self.config['self_id']:
                conn.send(b"not_master")
            else:
                # run SSH and return JSON
                info = self.ssh.run_all(self.config['self_id'])
                self.ssh.write_json(info)
                payload = json.dumps(info).encode()
                conn.send(payload)
        conn.close()

    def stop(self):
        self.running = False