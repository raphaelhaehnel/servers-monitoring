import json
import logging
import socket
import threading
import time
from functools import partial
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests

from infraNew.config_loader import get_config
from infraNew.messenger.fetchStateMessage import FetchStateMessage
from infraNew.messenger.forceMasterMessage import ForceMasterMessage
from infraNew.messenger.heartbeatMessage import HeartBeatMessage
from infraNew.messenger.joinRequestMessage import JoinRequestMessage
from infraNew.messenger.joinResponseMessage import JoinResponseMessage
from infraNew.messenger.leaveNotificationMessage import LeaveNotificationMessage
from infraNew.messenger.message_deserializer import MessageDeserializer
from infraNew.messenger.stateUpdateMessage import StateUpdateMessage
from infraNew.utils import IpManager
from models.clusterView import ClusterView
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
        self.last_master_heartbeat: int = 0

        # Data
        self.servers_data: ServersData = ServersData()
        self.cluster_view: ClusterView = ClusterView()
        self.user_requests: UserRequests = UserRequests()

        # Tasks
        self.heartbeat_sender_thread: threading.Thread = threading.Thread(target=self._heartbeat_sender, daemon=True)
        self.udp_listener_thread: threading.Thread = threading.Thread(target=self._udp_listener, daemon=True)
        self.tcp_server_thread: threading.Thread = threading.Thread(target=self._tcp_server, daemon=True)
        self.tcp_client_thread: threading.Thread = threading.Thread(target=self._tcp_client, daemon=True)
        self.http_server_thread: threading.Thread = threading.Thread(target=self._http_server, daemon=True)
        self.active_client_threads: list[threading.Thread] = []

        # Initializing the different threads
        self.start()

        #TODO if not received heartbeat for 3 * HEARTBEAT_INTERVAL, elect a new master
        #TODO if a tcp socket is alive more than 60 seconds, kill the socket.
    def start(self):
        self.udp_listener_thread.start()
        self.http_server_thread.start()

        # Request to join the network
        threading.Thread(target=self._join_network, daemon=True).start()

        try:
            while not self.stop_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            self.shutdown()

    def start_master_tasks(self, update_front=False):
        self.role = Role.MASTER
        if update_front:
            try:
                requests.post(f"http://localhost:{str(HTTP_PORT_FRONT)}/promote", timeout=1)
                self.logger.info(f"Sent PROMOTE request to update the front")
            except Exception as e:
                self.logger.warning(f"Failed to send PROMOTE request to the front: {e}")

        if self.tcp_client_thread.is_alive():
            self.tcp_client_thread.join(1)

        if not self.heartbeat_sender_thread.is_alive():
            self.heartbeat_sender_thread.start()
        else:
            self.logger.warning(f"Thread <HEARTBEAT_SENDER> was still alive. This is not the right behavior...")

        if not self.tcp_server_thread.is_alive():
            self.tcp_server_thread.start()
        else:
            self.logger.warning(f"Thread <TCP_SERVER> was still alive. This is not the right behavior...")

    def _http_server(self):
        class Handler(BaseHTTPRequestHandler):
            def __init__(self, *args, node_instance=None, **kwargs):
                self.node_instance = node_instance
                super().__init__(*args, **kwargs)

            def do_POST(self_inner):
                if self_inner.path == '/promote':
                    # handle REST trigger for master change
                    self.start_master_tasks()
                    self.logger.info("Promoted to master via HTTP, congratulations!")
                    self_inner.send_response(200)
                    self_inner.end_headers()
                else:
                    self_inner.send_response(404)
                    self_inner.end_headers()

        handler_with_context = partial(Handler, node_instance=self)
        httpd = HTTPServer(('0.0.0.0', HTTP_PORT), handler_with_context)
        httpd.serve_forever()

    def _tcp_server(self):
        self.logger.info(f"Thread <TCP_SERVER> started!")

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('', TCP_PORT))
        self.logger.info(f'TCP server started')

        # Listen to new clients
        server.listen()

        while not self.stop_event.is_set():
            self.logger.info(f'Waiting for new clients...')
            connection, address = server.accept()
            self.logger.info(f'A new client connected at address {address}')
            thread = threading.Thread(target=self._handle_client, args=(connection, address), daemon=True)
            self.active_client_threads.append(thread)
            thread.start()

    def _tcp_client(self):
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.master_ip, TCP_PORT))
            self.logger.info(f"Connected to master {self.master_ip}")

            while not self.stop_event.is_set():
                client_socket.send(FetchStateMessage().to_json().encode())
                data = client_socket.recv(8192)
                msg = json.loads(data.decode())

                message = MessageDeserializer().deserialize(msg)

                self.logger.info(f"Fetched message of type {message.__class__.__name__}")
                if message.__class__ == StateUpdateMessage:
                    self.servers_data = message.servers_data
                    self.cluster_view = message.cluster_view
                    self.user_requests = message.user_requests

                time.sleep(FETCH_INTERVAL / 1000)

            client_socket.close()

        except (ConnectionRefusedError, TimeoutError) as e:
            self.logger.warning(f"Failed to fetch state from master '{self.master_ip}': {e}")

    def _handle_client(self, connection, address):
        while not self.stop_event.is_set():
            data = connection.recv(4096)
            try:
                msg = json.loads(data.decode())
                message = MessageDeserializer().deserialize(msg)
            except Exception as e:
                self.logger.error(f"Didn't succeed to handle message from the client: {e}")
                connection.close()
                return

            self.logger.info(f"Got message of type {message.__class__.__name__}")
            if message.__class__ == FetchStateMessage:
                response = StateUpdateMessage(self.servers_data, self.cluster_view, self.user_requests)
                connection.send(response.to_json().encode())

        connection.close()


    def _heartbeat_sender(self):
        self.logger.info(f"Thread <HEARTBEAT_SENDER> started!")
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
        self.logger.info(f"Thread <UDP_LISTENER> started!")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', UDP_PORT))
        show_waiting_log = True
        while not self.stop_event.is_set():

            if show_waiting_log:
                self.logger.info("Waiting for UDP message...")

            data, addr = sock.recvfrom(4096)

            if addr[0] == self.ip:
                show_waiting_log = False
                continue

            show_waiting_log = True
            msg = json.loads(data.decode())
            self._handle_udp(msg, addr)

    def _handle_udp(self, msg, addr):
        message = MessageDeserializer().deserialize(msg)
        src_ip = addr[0]

        self.logger.info(f"Received UDP message {message.__class__.__name__} from {src_ip} !")

        if message.__class__ == JoinRequestMessage and self.role == Role.MASTER:
            self._reply_join(src_ip)
            self.logger.info(f"Replied to JoinRequest from {src_ip}")

        elif message.__class__ == JoinResponseMessage and self.role == Role.SLAVE:
            # Save the ip of the master, and update the data
            self.master_ip = src_ip
            self.servers_data: ServersData = message.servers_data
            self.cluster_view: ClusterView = message.cluster_view
            self.user_requests: UserRequests = message.cluster_view
            self.last_master_heartbeat = time.time()
            self.tcp_client_thread.start()
            self.logger.info(f"Master identified at address {src_ip} and acquired data successfully")

        elif message.__class__ == HeartBeatMessage:
            self.last_master_heartbeat = time.time()
            self.logger.info(f"Master still living!")

        elif message.__class__ == LeaveNotificationMessage:
            self.cluster_view.remove(src_ip)

            # If the user who leaved is the master
            if src_ip == self.master_ip:
                self.master_ip = self.cluster_view.get_highest_ip()
                self.logger.info(f"The master {src_ip} disconnected. The new master is {self.master_ip}")

                if self.master_ip == self.ip:
                    self.start_master_tasks(update_front=True)

                    self.logger.info(f"You've been chose as the new master, congratulations!")
            else:
                self.logger.info(f"The slave {src_ip} disconnected")

        elif message.__class__ == ForceMasterMessage:
            self.master_ip = src_ip
            self.logger.info(f"The slave {src_ip} forced master. Long live to the new master !")


    def _reply_join(self, dest_ip):
        response = JoinResponseMessage(self.servers_data, self.cluster_view, self.user_requests)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(response.to_json().encode(), (dest_ip, UDP_PORT))
        sock.close()

    def _join_network(self):
        for _ in range(JOIN_NETWORK_ATTEMPTS):
            self._send_join_request()
            time.sleep(JOIN_NETWORK_INTERVAL/1000)
            if self.master_ip:
                return

        self.logger.info("Didn't find a master connected. You've been upgraded to master!")
        self.master_ip = IpManager().get_own_ip()
        self.start_master_tasks(update_front=True)

    def _send_join_request(self):
        request_message = JoinRequestMessage(self.ip)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(request_message.to_json().encode(), ('<broadcast>', UDP_PORT))
        sock.close()
        self.logger.info("Sent JoinRequest broadcast")

    def shutdown(self):
        self.stop_event.set()
        #TODO maybe use join() for all the alive threads ?
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
    HTTP_PORT_FRONT = int(config.find('HttpPortFront').text)
    FETCH_INTERVAL = int(config.find('FetchInterval').text)
    HEARTBEAT_INTERVAL = int(config.find('HeartbeatInterval').text)
    JOIN_NETWORK_INTERVAL = int(config.find('JoinNetworkInterval').text)
    JOIN_NETWORK_ATTEMPTS = int(config.find('JoinNetworkAttempts').text)

    user = User()