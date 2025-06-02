import json
import logging
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

from infraNew.config_loader import get_config
from infraNew.messenger.fetchStateMessage import FetchStateMessage
from infraNew.messenger.heartbeatMessage import HeartBeatMessage
from infraNew.messenger.joinRequestMessage import JoinRequestMessage
from infraNew.messenger.joinResponseMessage import JoinResponseMessage
from infraNew.messenger.leaveNotificationMessage import LeaveNotificationMessage
from infraNew.messenger.message_deserializer import MessageDeserializer
from infraNew.messenger.stateUpdateMessage import StateUpdateMessage
from infraNew.utils import IpManager
from models.cluserView import ClusterView
from models.serversData import ServersData
from models.userRequests import UserRequests
from models.role import Role

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')

class User:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.ip: str = IpManager().get_own_ip()
        self.stop_event: threading.Event = threading.Event()
        self.role: Role = Role.SLAVE
        self.master_ip: str = ""

        # Data
        self.servers_data: ServersData = ServersData()
        self.cluster_view: ClusterView = ClusterView()
        self.user_requests: UserRequests = UserRequests()

        # Initializing the different threads
        self.start()

    def start(self):

        #TODO don't open all the threads here. Open and close them only when needed
        threading.Thread(target=self._udp_listener, daemon=True).start()
        threading.Thread(target=self._heartbeat_sender, daemon=True).start()
        threading.Thread(target=self._tcp_server, daemon=True).start()
        threading.Thread(target=self._http_server, daemon=True).start()

        # Request to join the network
        threading.Thread(target=self._join_network, daemon=True).start()

        try:
            while not self.stop_event.is_set():
                if self.role == Role.SLAVE:
                    self._fetch_state()
                time.sleep(FETCH_INTERVAL/1000)

        except KeyboardInterrupt:
            self.shutdown()

    def _fetch_state(self):
        try:
            if not self.master_ip:
                self.logger.warning(f"Master still not defined, cannot perform fetch request")
                return

            self.logger.info(f"Fetching data from the master")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.master_ip, TCP_PORT))
            sock.send(FetchStateMessage().to_json().encode())
            data = sock.recv(8192)
            msg = json.loads(data.decode())

            self.logger.info(f"Fetched message of type {msg.get('Type')}")
            if msg.get('Type') == 'StateUpdate':

                # update local state
                self.servers_data = msg['Payload']

                # userRequests  # TODO: merge logic
            sock.close()

        except Exception as e:
            self.logger.warning(f"Failed to fetch state from master '{self.master_ip}': {e}")

    def _http_server(self):
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self_inner):
                if self_inner.path == '/promote':
                    # handle REST trigger for master change
                    self.role = 'master'
                    self.logger.info("Promoted to master via HTTP")
                    self_inner.send_response(200)
                    self_inner.end_headers()
                else:
                    self_inner.send_response(404)
                    self_inner.end_headers()

        httpd = HTTPServer(('0.0.0.0', HTTP_PORT), Handler)
        httpd.serve_forever()

    def _tcp_server(self):
        # TODO don't we need to open a port for each client ? Maybe do like the tic-tac-toe online

        self.logger.info(f"Thread <tcp_server> started!")
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('', TCP_PORT))
        server.listen(5) # TODO what is this number ?
        while not self.stop_event.is_set():
            client, addr = server.accept()
            threading.Thread(target=self._handle_tcp, args=(client,), daemon=True).start()

    def _handle_tcp(self, client):
        data = client.recv(4096)
        try:
            msg = json.loads(data.decode())
        except:
            client.close()
            return

        self.logger.info(f"Got message of type {msg.get('Type')}")
        if msg.get('Type') == 'FetchState' and self.role == Role.MASTER:
            resp = StateUpdateMessage(self.servers_data, self.cluster_view, self.user_requests)
            client.send(resp.to_json().encode())

        client.close() #TODO we are opening and closing the tcp connection each time. Not good, change this !

    def _heartbeat_sender(self):
        self.logger.info(f"Thread <heartbeat_sender> started!")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        while not self.stop_event.is_set():
            self.logger.info("Sending heartbeat broadcast")
            msg = HeartBeatMessage()
            sock.sendto(msg.to_json().encode(), ('<broadcast>', UDP_PORT))
            time.sleep(HEARTBEAT_INTERVAL/1000)

    def _udp_listener(self):
        """
        Start listening for messages of type JoinRequest, Heartbeat, LeaveNotification, ForceMaster
        :return:
        """
        self.logger.info(f"Thread <udp_listener> started!")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', UDP_PORT))

        while not self.stop_event.is_set():
            self.logger.info("Waiting for UDP message...")
            data, addr = sock.recvfrom(4096)
            msg = json.loads(data.decode())
            self._handle_udp(msg, addr)

    def _handle_udp(self, msg, addr):
        """
        Handler for UDP messages
        :param msg: The msg as dict
        :param addr: TODO
        :return:
        """
        message = MessageDeserializer().deserialize(msg)
        src_ip = addr[0]
        if src_ip == self.ip:
            return

        self.logger.info(f"Received UDP message {message.__class__.__name__} from {src_ip} !")
        if message.__class__ == JoinRequestMessage and self.role == Role.MASTER:
            self._reply_join(src_ip)

        elif message.__class__ == JoinResponseMessage and self.role == Role.SLAVE:
            # Save the ip of the master, and update the data
            self.master_ip = src_ip
            self.servers_data = message.servers_data
            self.cluster_view = message.cluster_view
            self.user_requests = message.cluster_view



        # TODO: handle other message types: Heartbeat, LeaveNotification, ForceMaster, etc.

    def _reply_join(self, dest_ip):
        response = JoinResponseMessage(self.servers_data, self.cluster_view, self.user_requests)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(response.to_json().encode(), (dest_ip, UDP_PORT))
        sock.close()
        self.logger.info(f"Replied to JoinRequest from {dest_ip}")

    def _join_network(self):
        for _ in range(JOIN_NETWORK_ATTEMPTS):
            self._send_join_request()
            time.sleep(JOIN_NETWORK_INTERVAL/1000)
            if self.master_ip:
                return

        self.logger.info("Didn't find a master connected. You've been upgraded to master!")
        self.master_ip = IpManager().get_own_ip()
        self.role = Role.MASTER

    def _send_join_request(self):
        requestMessage = JoinRequestMessage(self.ip)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(requestMessage.to_json().encode(), ('<broadcast>', UDP_PORT))
        sock.close()
        self.logger.info("Sent JoinRequest broadcast")

    def shutdown(self):
        self.stop_event.set()
        self._send_leave()

    def _send_leave(self):
        msg = LeaveNotificationMessage(self.ip)
        self.logger.info("Sending leaving message...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(msg.to_json().encode(), ('<broadcast>', UDP_PORT))
        sock.close()
        self.logger.info("Sent LeaveNotification")

if __name__ == "__main__":
    config = get_config()
    UDP_PORT = int(config.find('UdpPort').text)
    TCP_PORT = int(config.find('TcpPort').text)
    HTTP_PORT = int(config.find('HttpPort').text)
    FETCH_INTERVAL = int(config.find('FetchInterval').text)
    HEARTBEAT_INTERVAL = int(config.find('HeartbeatInterval').text)
    JOIN_NETWORK_INTERVAL = int(config.find('JoinNetworkInterval').text)
    JOIN_NETWORK_ATTEMPTS = int(config.find('JoinNetworkAttempts').text)

    user = User()