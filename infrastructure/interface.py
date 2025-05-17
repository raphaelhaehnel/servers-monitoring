import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

from infrastructure.election import LeaderElection


class ControlHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/master":
            m = self.server.election.get_master().encode()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(m)
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/master":
            length = int(self.headers['Content-Length'])
            body = json.loads(self.rfile.read(length))
            new_master = body.get("id")
            if new_master:
                self.server.election.manual_master = True
                # force immediate change
                self.server.election._broadcast_master(new_master)
                self.server.election.current_master = new_master
                self.send_response(204)
            else:
                self.send_response(400)
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

def start_control_server(election: LeaderElection, host="0.0.0.0", port=8000):
    srv = HTTPServer((host, port), ControlHandler)
    srv.election = election
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv