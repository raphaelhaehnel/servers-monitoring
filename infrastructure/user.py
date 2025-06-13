import json
import logging
import socket
import threading
import time
from functools import partial
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import requests

from infrastructure.messages.fetchStateMessage import FetchStateMessage
from infrastructure.messages.forceMasterMessage import ForceMasterMessage
from infrastructure.messages.heartbeatMessage import HeartBeatMessage
from infrastructure.messages.joinRequestMessage import JoinRequestMessage
from infrastructure.messages.joinResponseMessage import JoinResponseMessage
from infrastructure.messages.leaveNotificationMessage import LeaveNotificationMessage
from infrastructure.message_deserializer import MessageDeserializer
from infrastructure.messages.stateUpdateMessage import StateUpdateMessage
from infrastructure.ip_manager import IpManager
from models.clusterView import ClusterView
from models.serversData import ServersData
from models.userRequests import UserRequests
from models.role import Role

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')


class User:
    def __init__(self, config, servers_data: ServersData, cluster_view: ClusterView, user_requests: UserRequests, is_master: bool):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config
        self.ip: str = IpManager().get_own_ip()
        self.stop_event: threading.Event = threading.Event()
        self.role: Role = Role.SLAVE
        self.master_ip: str = ""
        self.last_master_heartbeat: int = 0
        self.last_save: int = 0

        # Define UDP socket for sending
        self.udp_sender_socket = self.initialize_udp_sender_socket()

        # Data
        self.servers_data: ServersData = servers_data
        self.cluster_view: ClusterView = cluster_view
        self.user_requests: UserRequests = user_requests

        # Tasks
        self.heartbeat_sender_thread: threading.Thread = threading.Thread(target=self._heartbeat_sender, daemon=True)
        self.udp_listener_thread: threading.Thread = threading.Thread(target=self._udp_listener, daemon=True)
        self.tcp_server_thread: threading.Thread = threading.Thread(target=self._tcp_server, daemon=True)
        self.tcp_client_thread: threading.Thread = threading.Thread(target=self._tcp_client, daemon=True)
        self.http_server_thread: threading.Thread = threading.Thread(target=self._http_server, daemon=True)
        self.ssh_polling_thread: threading.Thread = threading.Thread(target=self._ssh_sender, daemon=True)
        self.data_saver_thread: threading.Thread = threading.Thread(target=self._save_data_to_file, daemon=True)
        self.active_client_threads: list[threading.Thread] = []

        # TODO If you use HTTP, post the data instead of doing get and then respond (less traffic)
        # TODO between back and front, use event-driven updates
        # - the back gives the data and master update
        # - the front gives the master update only
        # Use threading.Event() or queue.Queue()

    @staticmethod
    def initialize_udp_sender_socket():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        return sock

    def start(self):
        self.load_server_data()

        self.udp_listener_thread.start()
        self.http_server_thread.start()

        # Request to join the network
        threading.Thread(target=self._join_network, daemon=True).start()

        try:
            while not self.stop_event.is_set():
                time.sleep(1)
        except KeyboardInterrupt:
            self.shutdown()

    def load_server_data(self):
        # Ensure the directory exists
        save_dir = Path(self.config.SAVING_NETWORK_DIRECTORY)
        filename = save_dir / "ServersData.json"

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.servers_data = ServersData().from_json(data)
        except Exception as e:
            self.logger.error(f"Failed to load ServerData: {e}")

    def start_master_tasks(self, update_front=False):
        self.role = Role.MASTER
        if update_front:
            try:
                requests.post(f"http://localhost:{str(self.config.HTTP_PORT_FRONT)}/updateRole", data=f"master", timeout=1)
                self.logger.info(f"Sent updateRole MASTER request to the front")
            except Exception as e:
                self.logger.warning(f"Failed to send updateRole MASTER request to the front: {e}")

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

        if not self.ssh_polling_thread.is_alive():
            self.ssh_polling_thread.start()
        else:
            self.logger.warning(f"Thread <SSH_POLLING> was still alive. This is not the right behavior...")

        if not self.data_saver_thread.is_alive():
            self.data_saver_thread.start()
        else:
            self.logger.warning(f"Thread <DATA_SAVER_THREAD> was still alive. This is not the right behavior...")


    def start_slave_tasks(self):
        self.role = Role.SLAVE
        try:
            requests.post(f"http://localhost:{str(self.config.HTTP_PORT_FRONT)}/updateRole", data=f"slave", timeout=1)
            self.logger.info(f"Sent updateRole SLAVE request to the front")
        except Exception as e:
            self.logger.warning(f"Failed to send updateRole SLAVE request to the front: {e}")

        if self.heartbeat_sender_thread.is_alive():
            self.heartbeat_sender_thread.join(1)
            self.logger.info(f"Shutting down Thread <HEARTBEAT_SENDER>")

        if self.tcp_server_thread.is_alive():
            self.tcp_server_thread.join(1)
            self.logger.info(f"Shutting down Thread <TCP_SERVER>")

        if self.ssh_polling_thread.is_alive():
            self.ssh_polling_thread.join(1)
            self.logger.info(f"Shutting down Thread <SSH_POLLING>")

        if self.data_saver_thread.is_alive():
            self.data_saver_thread.join(1)
            self.logger.info(f"Shutting down Thread <DATA_SAVER_THREAD>")

        if not self.tcp_client_thread.is_alive():
            self.tcp_client_thread.start()
        else:
            self.logger.warning(f"Thread <TCP_CLIENT> was still alive. This is not the right behavior...")

    def _http_server(self):
        class Handler(BaseHTTPRequestHandler):
            def __init__(self, *args, node_instance=None, **kwargs):
                self.node_instance = node_instance
                super().__init__(*args, **kwargs)

            def do_POST(self_inner):
                if self_inner.path == '/promote':
                    # handle REST trigger for master change
                    self.send_force_master()
                    self.start_master_tasks()
                    self.logger.info("Promoted to master via HTTP, congratulations!")
                    self_inner.send_response(200)
                    self_inner.end_headers()
                else:
                    self_inner.send_response(404)
                    self_inner.end_headers()

        handler_with_context = partial(Handler, node_instance=self)
        httpd = HTTPServer(('0.0.0.0', self.config.HTTP_PORT), handler_with_context)
        httpd.serve_forever()

    def _tcp_server(self):
        self.logger.info(f"Thread <TCP_SERVER> started!")

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('', self.config.TCP_PORT))
        self.logger.info(f'TCP server started')

        # Listen to new clients
        server.listen()

        while not self.stop_event.is_set():
            self.logger.info(f'Waiting for new clients...')
            connection, address = server.accept()
            connection.settimeout(self.config.CLIENT_TCP_TIMEOUT / 1000)
            src_ip = address[0]
            self.logger.info(f'A new client connected at address {src_ip}')
            thread = threading.Thread(target=self._handle_client, args=(connection, src_ip), daemon=True)
            self.active_client_threads.append(thread)
            self.cluster_view.add_or_update(src_ip, Role.SLAVE)
            thread.start()

    def _tcp_client(self):
        client_socket = None

        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((self.master_ip, self.config.TCP_PORT))
            self.logger.info(f"Connected to master {self.master_ip}")

            while not self.stop_event.is_set():
                client_socket.send(FetchStateMessage().to_json().encode())
                self.logger.info("Sent message of type FetchStateMessage")

                data = client_socket.recv(8192)

                if not data:
                    self.logger.warning("Master closed connection unexpectedly.")
                    break

                msg = json.loads(data.decode())
                message = MessageDeserializer().deserialize(msg)
                self.logger.info(f"Fetched message of type {message.get_name()}")

                if isinstance(message, StateUpdateMessage):
                    self.servers_data = message.servers_data
                    self.cluster_view = message.cluster_view
                    self.user_requests = message.user_requests

                time.sleep(self.config.FETCH_INTERVAL / 1000)

            client_socket.close()

        except (ConnectionRefusedError, TimeoutError) as e:
            self.logger.warning(f"Cannot connect to master {self.master_ip}: {e}")

        except (ConnectionResetError, OSError) as e:
            self.logger.warning(f"Connection lost from master {self.master_ip}: {e}")

        finally:
            if client_socket is not None:
                try:
                    client_socket.close()
                    self.logger.info("TCP client socket closed.")
                except Exception:
                    pass

    def _handle_client(self, connection, client_ip):
        while not self.stop_event.is_set():
            try:
                data = connection.recv(4096)
                msg = json.loads(data.decode())
                message = MessageDeserializer().deserialize(msg)

            except (ConnectionResetError, OSError) as e:
                self.logger.warning(f"Client {client_ip} disconnected abruptly: {e}")
                break

            except socket.timeout:
                self.logger.warning(f"Timed out waiting for data from client {client_ip}. Disconnecting.")
                break

            except Exception as e:
                self.logger.error(f"Didn't succeed to handle message from the client: {e}")
                continue

            self.logger.info(f"Got message of type {message.get_name()}")

            if isinstance(message, FetchStateMessage):
                response = StateUpdateMessage(self.servers_data, self.cluster_view, self.user_requests)
                connection.send(response.to_json().encode())
                self.logger.info(f"Sent message of type {response.get_name()}")

        connection.close()
        self.cluster_view.remove(client_ip)
        self.logger.warning(f"Socket of client {client_ip} has been closed.")

    def _heartbeat_sender(self):
        self.logger.info(f"Thread <HEARTBEAT_SENDER> started!")

        while not self.stop_event.is_set():
            self.logger.info("Sending heartbeat broadcast")
            msg = HeartBeatMessage()
            self.udp_sender_socket.sendto(msg.to_json().encode(), ('<broadcast>', self.config.UDP_PORT))
            time.sleep(self.config.HEARTBEAT_INTERVAL / 1000)

    def _udp_listener(self):
        """
        Start listening for messages of type JoinRequest, Heartbeat, LeaveNotification, ForceMaster
        :return:
        """
        self.logger.info(f"Thread <UDP_LISTENER> started!")
        self.last_master_heartbeat = time.time()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(self.config.HEARTBEAT_RETRIES * self.config.HEARTBEAT_INTERVAL / 1000)
        sock.bind(('', self.config.UDP_PORT))
        show_waiting_log = True

        while not self.stop_event.is_set():
            if show_waiting_log:
                self.logger.info("Waiting for UDP message...")

            try:
                data, addr = sock.recvfrom(4096)
                if addr[0] == self.ip:
                    show_waiting_log = False
                    continue

                show_waiting_log = True
                msg = json.loads(data.decode())
                self._handle_udp(msg, addr[0])

            except socket.timeout:
                self.logger.warning(f"Timed out waiting for UDP messages. Didn't got Heartbeat from master. Reinitializing connection.")
                self.reinitialize_connection()

    def _handle_udp(self, msg, src_ip):
        message = MessageDeserializer().deserialize(msg)

        self.logger.info(f"Received UDP message {message.get_name()} from {src_ip}")

        if self.role == Role.SLAVE:
            heartbeat_delay = time.time() - self.last_master_heartbeat

            if heartbeat_delay > self.config.HEARTBEAT_RETRIES * self.config.HEARTBEAT_INTERVAL / 1000:
                self.logger.warning(f"Timed out waiting for Heartbeat message from master. Reinitializing connection.")
                self.reinitialize_connection()

        if isinstance(message, JoinRequestMessage) and self.role == Role.MASTER:
            self._reply_join(src_ip)
            self.logger.info(f"Replied to JoinRequest from {src_ip}")

        elif isinstance(message, JoinResponseMessage) and self.role == Role.SLAVE:
            # Save the ip of the master, and update the data
            self.master_ip = src_ip
            self.servers_data: ServersData = message.servers_data
            self.cluster_view: ClusterView = message.cluster_view
            self.user_requests: UserRequests = message.user_requests
            self.last_master_heartbeat = time.time()
            self.tcp_client_thread.start()
            self.logger.info(f"Master identified at address {src_ip} and acquired data successfully")

        elif isinstance(message, HeartBeatMessage):
            self.last_master_heartbeat = time.time()
            self.logger.info(f"Master still living!")

        elif isinstance(message, LeaveNotificationMessage):
            self.cluster_view.remove(src_ip)

            # If the user who leaved is the master
            if src_ip == self.master_ip:
                self.master_ip = self.cluster_view.get_highest_ip().nodeIP
                self.logger.info(f"The master {src_ip} disconnected. The new master is {self.master_ip}")

                if self.master_ip == self.ip:
                    self.start_master_tasks(update_front=True)
                    self.logger.info(f"You've been chose as the new master, congratulations!")
            else:
                self.logger.info(f"The slave {src_ip} disconnected")

        elif isinstance(message, ForceMasterMessage):
            self.master_ip = src_ip
            self.cluster_view.add_or_update(src_ip, Role.MASTER)
            self.logger.info(f"The slave {src_ip} forced master. Long live to the new master !")
            self.start_slave_tasks()

    def reinitialize_connection(self):
        # Stop the TCP connection to the server
        if self.tcp_client_thread.is_alive():
            self.tcp_client_thread.join(1)
        else:
            self.logger.warning(f"Thread <TCP_CLIENT> was down. This is not the right behavior...")

        self.master_ip: str = ""

        # Try to connect to the master
        threading.Thread(target=self._join_network, daemon=True).start()

    def _reply_join(self, dest_ip):
        response = JoinResponseMessage(self.servers_data, self.cluster_view, self.user_requests)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(response.to_json().encode(), (dest_ip, self.config.UDP_PORT))
        sock.close()

    def _join_network(self):
        for _ in range(self.config.JOIN_NETWORK_ATTEMPTS):
            self._send_join_request()
            time.sleep(self.config.JOIN_NETWORK_INTERVAL / 1000)
            if self.master_ip:
                return

        self.logger.info("No master found. You've been promoted to master!")
        self.master_ip = IpManager().get_own_ip()
        self.start_master_tasks(update_front=True)

    def _send_join_request(self):
        request_message = JoinRequestMessage(self.ip)
        self.udp_sender_socket.sendto(request_message.to_json().encode(), ('<broadcast>', self.config.UDP_PORT))
        self.logger.info("Sent JoinRequest broadcast")

    def send_force_master(self):
        msg = ForceMasterMessage(self.ip)
        self.udp_sender_socket.sendto(msg.to_json().encode(), ('<broadcast>', self.config.UDP_PORT))
        self.logger.info("Sent ForceMaster broadcast")

    def _ssh_sender(self):
        self.logger.info(f"Thread <SSH_SENDER> started!")
        while not self.stop_event.is_set():
            self.logger.info("SSH command sent!")
            self.servers_data.last_update = int(time.time())
            time.sleep(self.config.SERVER_POLLING_INTERVAL / 1000)

    def _save_data_to_file(self):
        """
        Periodically serialize `self.servers_data` to JSON files in
        the directory specified by SAVING_NETWORK_DIRECTORY.
        """
        self.logger.info(f"Thread <SAVE_DATA_TO_FILE> started!")

        # Ensure the directory exists
        save_dir = Path(self.config.SAVING_NETWORK_DIRECTORY)
        save_dir.mkdir(parents=True, exist_ok=True)

        while not self.stop_event.is_set():
            time.sleep(self.config.SAVING_INTERVAL / 1000)

            filename = save_dir / "ServersData.json"
            try:
                data = self.servers_data.to_dict()
            except Exception as e:
                self.logger.error(f"Failed to serialize servers_data: {e}")
                continue

            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                self.logger.info(f"Saved servers_data snapshot to {filename}")
            except Exception as e:
                self.logger.error(f"Error writing to {filename}: {e}")

    def shutdown(self):
        self._send_leave()
        self.udp_sender_socket.close()
        self.stop_event.set()

    def _send_leave(self):
        msg = LeaveNotificationMessage(self.ip)
        self.logger.info("Sending leaving message...")
        self.udp_sender_socket.sendto(msg.to_json().encode(), ('<broadcast>', self.config.UDP_PORT))
        self.logger.info("Sent LeaveNotification")

