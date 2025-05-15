import subprocess
import json
from infrastructure.utils import load_config, get_self_id

class SSHManager:
    def __init__(self, config):
        self.config = config
        self.commands = config['ssh_commands']
        self.user = config['ssh_user']
        self.key = config['ssh_key_path']

    def run_all(self, host):
        results = {}
        for cmd in self.commands:
            proc = subprocess.run(
                ['ssh', '-i', self.key, f"{self.user}@{host}", cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                encoding='utf-8'
            )
            results[cmd] = { 'out': proc.stdout, 'err': proc.stderr }
        return results

    def write_json(self, data, path='status.json'):
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)