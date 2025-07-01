import json
import logging
import socket
import threading
import time
from pathlib import Path

from infrastructure.messages.actionRequestMessage import ActionRequestMessage
from infrastructure.messages.fetchStateMessage import FetchStateMessage
from infrastructure.messages.forceMasterMessage import ForceMasterMessage
from infrastructure.messages.heartbeatMessage import HeartBeatMessage
from infrastructure.messages.joinRequestMessage import JoinRequestMessage
from infrastructure.messages.joinResponseMessage import JoinResponseMessage
from infrastructure.messages.leaveNotificationMessage import LeaveNotificationMessage
from infrastructure.message_deserializer import MessageDeserializer
from infrastructure.messages.stateUpdateMessage import StateUpdateMessage
from infrastructure.ip_manager import IpManager
from infrastructure.shared_models.shared_clusterView import SharedClusterView
from infrastructure.shared_models.shared_isMaster import SharedIsMaster
from infrastructure.shared_models.shared_serversData import SharedServersData
from infrastructure.shared_models.shared_userRequests import SharedUserRequests
from infrastructure.validator import validate_user_request
from models.serversData import ServersData
from models.role import Role
from models.userRequest import UserRequest
from models.usersRequests import UsersRequests

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s - %(message)s')


class User:
    def __init__(self, config, shared_servers: SharedServersData, shared_cluster: SharedClusterView, shared_requests: SharedUserRequests, shared_is_master: SharedIsMaster):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config
        self.ip: str = IpManager.get_own_ip()
        self.stop_core_event: threading.Event = threading.Event()
        self.stop_master_event = threading.Event()
        self.stop_slave_event = threading.Event()
        self.role: Role = Role.SLAVE
        self.master_ip: str = ""
        self.last_master_heartbeat: int = 0
        self.last_save: int = 0

        # Define UDP socket for sending
        self.udp_sender_socket = self.initialize_udp_sender_socket()
        self.client_socket = None
        self.client_socket_lock = threading.Lock()

        # Data
        self.shared_servers: SharedServersData = shared_servers
        self.shared_cluster: SharedClusterView = shared_cluster
        self.shared_requests: SharedUserRequests = shared_requests
        self.shared_is_master: SharedIsMaster = shared_is_master

        self.shared_is_master.dataChanged.connect(self.start_role_tasks)
        self.shared_requests.dataChanged.connect(self.send_request)

        # Tasks
        self.heartbeat_sender_thread: threading.Thread = threading.Thread(target=self._heartbeat_sender, daemon=True)
        self.udp_listener_thread: threading.Thread = threading.Thread(target=self._udp_listener, daemon=True)
        self.tcp_server_thread: threading.Thread = threading.Thread(target=self._tcp_server, daemon=True)
        self.tcp_client_thread: threading.Thread = threading.Thread(target=self._tcp_client, daemon=True)
        self.ssh_polling_thread: threading.Thread = threading.Thread(target=self._ssh_polling, daemon=True)
        self.data_saver_thread: threading.Thread = threading.Thread(target=self._data_saver, daemon=True)
        self.active_client_threads: list[threading.Thread] = []

    @staticmethod
    def initialize_udp_sender_socket():
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        return sock

    def start(self):
        self.udp_listener_thread.start()

        # Request to join the network
        threading.Thread(target=self._join_network, daemon=True).start()

        try:
            while not self.stop_core_event.is_set():
                self.stop_core_event.wait(1)

        except KeyboardInterrupt:
            self.shutdown()

    def start_role_tasks(self):
        if self.shared_is_master.data:
            self.start_master_tasks()
        else:
            self.start_slave_tasks()

    def send_request(self):
        if self.shared_is_master.data:
            return

        if not self.shared_requests.data.requests:

            return
        if not self.client_socket:
            self.logger.warning("Socket not ready, cannot send request")
            return

        message = ActionRequestMessage(self.shared_requests.data.requests[-1])
        with self.client_socket_lock:
            try:
                self.client_socket.send(message.to_json().encode())
                self.logger.info("Sent message of type ActionRequestMessage")

            except Exception as e:
                self.logger.error(f"Failed to send request: {e}")

    def load_server_data(self):
        # Ensure the directory exists
        save_dir = Path(self.config.SAVING_NETWORK_DIRECTORY)
        filename = save_dir / "ServersData.json"

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.shared_servers.data = ServersData.from_json(data)
        except Exception as e:
            self.logger.error(f"Failed to load ServerData: {e}")

    def start_master_tasks(self):
        self.logger.info("Starting Master tasks")

        if self.master_ip:  # Check if another master was already defined
            self.send_force_master()

        self.master_ip = IpManager.get_own_ip()
        self.role = Role.MASTER

        self.stop_slave_event.set()
        self.stop_master_event.clear()

        if not self.heartbeat_sender_thread.is_alive():
            self.heartbeat_sender_thread = threading.Thread(target=self._heartbeat_sender, daemon=True)
            self.heartbeat_sender_thread.start()
        else:
            self.logger.warning(f"Thread <HEARTBEAT_SENDER> was still alive. This is not the right behavior...")

        if not self.tcp_server_thread.is_alive():
            self.tcp_server_thread = threading.Thread(target=self._tcp_server, daemon=True)
            self.tcp_server_thread.start()
        else:
            self.logger.warning(f"Thread <TCP_SERVER> was still alive. This is not the right behavior...")

        if not self.ssh_polling_thread.is_alive():
            self.ssh_polling_thread = threading.Thread(target=self._ssh_polling, daemon=True)
            self.ssh_polling_thread.start()
        else:
            self.logger.warning(f"Thread <SSH_POLLING> was still alive. This is not the right behavior...")

        if not self.data_saver_thread.is_alive():
            self.data_saver_thread = threading.Thread(target=self._data_saver, daemon=True)
            self.data_saver_thread.start()
        else:
            self.logger.warning(f"Thread <DATA_SAVER_THREAD> was still alive. This is not the right behavior...")


    def start_slave_tasks(self):
        self.logger.info("Starting Slave tasks")
        self.role = Role.SLAVE
        self.last_master_heartbeat = time.time()

        self.stop_master_event.set()
        self.stop_slave_event.clear()

        if not self.tcp_client_thread.is_alive():
            self.tcp_client_thread = threading.Thread(target=self._tcp_client, daemon=True)
            self.tcp_client_thread.start()
        else:
            self.logger.warning(f"Thread <TCP_CLIENT> was still alive. This is not the right behavior...")

    def _tcp_server(self):
        self.logger.info(f"Thread <TCP_SERVER> started!")

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(('', self.config.TCP_PORT))
        self.logger.info(f'TCP server started')

        # Listen to new clients
        server.listen()
        server.settimeout(1) # Set a timeout to avoid the blocking line server.accept()
        has_logged_waiting = False # Flag to print log once for every new client

        while not self.stop_master_event.is_set():
            try:
                if not has_logged_waiting:
                    self.logger.info(f'Waiting for new clients...')
                    has_logged_waiting = True

                connection, address = server.accept()
                has_logged_waiting = False  # Once a client connects, reset the flag
                connection.settimeout(self.config.CLIENT_TCP_TIMEOUT / 1000)
                src_ip = address[0]
                self.logger.info(f'A new client connected at address {src_ip}')
                thread = threading.Thread(target=self._handle_client, args=(connection, src_ip), daemon=True)
                self.active_client_threads.append(thread)
                self.shared_cluster.data.add_or_update(src_ip, Role.SLAVE)
                thread.start()
            except socket.timeout:
                continue

        for client_thread in self.active_client_threads:
            client_thread.join(1)

        server.close()
        self.active_client_threads.clear()
        self.logger.info(f"Thread <TCP_SERVER> is shutting down")

    def _tcp_client(self):
        self.logger.info(f"Thread <TCP_CLIENT> started!")

        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.master_ip, self.config.TCP_PORT))
            self.logger.info(f"Connected to master {self.master_ip}")

            while not self.stop_slave_event.is_set():

                with self.client_socket_lock:
                    self.client_socket.send(FetchStateMessage().to_json().encode())
                self.logger.info("Sent message of type FetchStateMessage")

                data = self.client_socket.recv(8192)

                if not data:
                    self.logger.warning("Master closed connection unexpectedly.")
                    break

                msg = json.loads(data.decode())
                message = MessageDeserializer().deserialize(msg)
                self.logger.info(f"Fetched message of type {message.get_name()}")

                if isinstance(message, StateUpdateMessage):
                    self.shared_servers.data = message.servers_data
                    self.shared_cluster.data = message.cluster_view
                    self.shared_requests.data = message.user_requests

                self.stop_slave_event.wait(self.config.FETCH_INTERVAL / 1000)

            self.client_socket.close()
            self.client_socket = None

        except (ConnectionRefusedError, TimeoutError) as e:
            self.logger.warning(f"Cannot connect to master {self.master_ip}: {e}")

        except (ConnectionResetError, OSError) as e:
            self.logger.warning(f"Connection lost from master {self.master_ip}: {e}")

        finally:
            if self.client_socket is not None:
                try:
                    self.client_socket.close()
                    self.logger.info("TCP client socket closed.")
                except Exception:
                    pass

            self.logger.info(f"Thread <TCP_CLIENT> is shutting down")

    def _handle_client(self, connection, client_ip):
        while not self.stop_master_event.is_set():
            msg = None
            try:
                data = connection.recv(4096)
                if not data:  # Client closed cleanly
                    self.logger.info(f"Client {client_ip} closed the connection.")
                    break

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
                self.logger.error(f"msg: {msg}")
                continue

            self.logger.info(f"Got message of type {message.get_name()}")

            if isinstance(message, FetchStateMessage):
                response = StateUpdateMessage(self.shared_servers.data, self.shared_cluster.data, self.shared_requests.data)
                connection.send(response.to_json().encode())
                self.logger.info(f"Sent message of type {response.get_name()}")

            elif isinstance(message, ActionRequestMessage):
                user_request: UserRequest = message.user_request
                if validate_user_request(self.shared_servers.data, user_request):
                    requests_list: UsersRequests = self.shared_requests.data
                    requests_list.add(user_request)
                    self.logger.info(f"A new request from {client_ip} has been added to the requests list")

                else:
                    self.logger.warning(f"Got an invalid request from {client_ip}: user {user_request.user}, host {user_request.host}")
        connection.close()
        self.shared_cluster.data.remove(client_ip)
        self.logger.warning(f"Socket of client {client_ip} has been closed.")

    def _heartbeat_sender(self):
        self.logger.info(f"Thread <HEARTBEAT_SENDER> started!")

        while not self.stop_master_event.is_set():
            self.logger.info("Sending heartbeat broadcast")
            msg = HeartBeatMessage()
            self.udp_sender_socket.sendto(msg.to_json().encode(), ('<broadcast>', self.config.UDP_PORT))
            self.stop_master_event.wait(self.config.HEARTBEAT_INTERVAL / 1000)

        self.logger.info(f"Thread <HEARTBEAT_SENDER> is shutting down")

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

        while not self.stop_core_event.is_set():
            if show_waiting_log:
                self.logger.info("Waiting for UDP message...")

            try:
                data, addr = sock.recvfrom(4096)
                print(addr[0])
                print([element.to_dict() for element in self.shared_requests.data.requests])

                if addr[0] in IpManager.get_own_ips():
                    show_waiting_log = False
                    continue

                show_waiting_log = True
                msg = json.loads(data.decode())
                self._handle_udp(msg, addr[0])

            except socket.timeout:
                self.logger.warning(f"Timed out waiting for UDP messages. Didn't got Heartbeat from master. Reinitializing connection.")
                self.restart_tcp_client()

    def _handle_udp(self, msg, src_ip):
        message = MessageDeserializer().deserialize(msg)

        self.logger.info(f"Received UDP message {message.get_name()} from {src_ip}")

        if self.role == Role.SLAVE:
            heartbeat_delay = time.time() - self.last_master_heartbeat

            if heartbeat_delay > self.config.HEARTBEAT_RETRIES * self.config.HEARTBEAT_INTERVAL / 1000:
                self.logger.warning(f"Timed out waiting for Heartbeat message from master. Reinitializing connection.")
                self.restart_tcp_client()

        if isinstance(message, JoinRequestMessage) and self.role == Role.MASTER:
            self._reply_join(src_ip)
            self.logger.info(f"Replied to JoinRequest from {src_ip}")

        elif isinstance(message, JoinResponseMessage) and self.role == Role.SLAVE:
            # Save the ip of the master, and update the data
            self.master_ip = src_ip
            self.shared_servers.data = message.servers_data
            self.shared_cluster.data = message.cluster_view
            self.shared_requests.data = message.user_requests
            self.last_master_heartbeat = time.time()
            self.tcp_client_thread = threading.Thread(target=self._tcp_client, daemon=True)
            self.tcp_client_thread.start()
            self.logger.info(f"Master identified at address {src_ip} and acquired data successfully")

        elif isinstance(message, HeartBeatMessage):
            if self.shared_is_master.data:
                self.logger.error(f"Got heartbeat message from another master!")

            self.last_master_heartbeat = time.time()
            self.logger.info(f"Master still living!")

        elif isinstance(message, LeaveNotificationMessage):
            self.shared_cluster.data.remove(src_ip)

            # If the user who leaved is the master
            if src_ip == self.master_ip:
                self.master_ip = self.shared_cluster.data.get_highest_ip().nodeIP
                self.logger.info(f"The master {src_ip} disconnected. The new master is {self.master_ip}")

                if self.master_ip == self.ip:
                    self.shared_is_master.data = True # Call self.start_role_tasks()
                    self.logger.info(f"You've been chose as the new master, congratulations!")
            else:
                self.logger.info(f"The slave {src_ip} disconnected")

        elif isinstance(message, ForceMasterMessage):
            self.master_ip = src_ip
            self.shared_cluster.data.add_or_update(src_ip, Role.MASTER)
            self.logger.info(f"The slave {src_ip} forced master. Long live to the new master !")

            if self.shared_is_master.data:
                self.shared_is_master.data = False # Call self.start_role_tasks()
            else:
                self.restart_tcp_client(master_exists=True)


    def restart_tcp_client(self, master_exists=False):
        # Stop the TCP connection to the server

        self.logger.info(f"Restarting the TCP connection")
        self.stop_slave_event.set()

        if self.tcp_client_thread.is_alive():
            # This is the maximum time we'll have to wait to let the previous thread close itself
            self.tcp_client_thread.join(self.config.FETCH_INTERVAL / 1000)
            self.logger.info(f"Thread <TCP_CLIENT> is shutting down")
        else:
            self.logger.warning(f"Thread <TCP_CLIENT> was down. This is not the right behavior...")

        self.stop_slave_event.clear()
        if master_exists:
            self.tcp_client_thread = threading.Thread(target=self._tcp_client, daemon=True)
            self.tcp_client_thread.start()
        else:
            self.master_ip: str = ""
            threading.Thread(target=self._join_network, daemon=True).start()

    def _reply_join(self, dest_ip):
        response = JoinResponseMessage(self.shared_servers.data, self.shared_cluster.data, self.shared_requests.data)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(response.to_json().encode(), (dest_ip, self.config.UDP_PORT))
        sock.close()

    def _join_network(self):
        for _ in range(self.config.JOIN_NETWORK_ATTEMPTS):
            self._send_join_request()
            self.stop_core_event.wait(self.config.JOIN_NETWORK_INTERVAL / 1000)
            if self.master_ip:
                return

        self.logger.info("No master found. You've been promoted to master!")
        self.load_server_data()
        self.shared_is_master.data = True # Call self.start_role_tasks()

    def _send_join_request(self):
        request_message = JoinRequestMessage(self.ip)
        self.udp_sender_socket.sendto(request_message.to_json().encode(), ('<broadcast>', self.config.UDP_PORT))
        self.logger.info("Sent JoinRequest broadcast")

    def send_force_master(self):
        msg = ForceMasterMessage(self.ip)
        self.udp_sender_socket.sendto(msg.to_json().encode(), ('<broadcast>', self.config.UDP_PORT))
        self.logger.info("Sent ForceMaster broadcast")

    def _ssh_polling(self):
        self.logger.info(f"Thread <SSH_POLLING> started!")
        while not self.stop_master_event.is_set():
            self.stop_master_event.wait(self.config.SERVER_POLLING_INTERVAL / 1000)

            self.shared_servers.data.last_update = int(time.time())

            self.shared_servers.typed_data.servers_list[0].available = False
            self.shared_servers.typed_data.servers_list[0].reservation = "Raphael"
            self.shared_servers.typed_data.servers_list[0].since = int(time.time())

            self.shared_servers.typed_data.servers_list[1].available = True
            self.shared_servers.typed_data.servers_list[1].reservation = ""
            self.shared_servers.typed_data.servers_list[1].since = -1

            self.shared_servers.dataChanged.emit()

            self.logger.info("SSH command sent!")

            self.stop_master_event.wait(self.config.SERVER_POLLING_INTERVAL / 1000)

            self.shared_servers.data.last_update = int(time.time())

            self.shared_servers.typed_data.servers_list[0].available = True
            self.shared_servers.typed_data.servers_list[0].reservation = ""
            self.shared_servers.typed_data.servers_list[0].since = -1

            self.shared_servers.typed_data.servers_list[1].available = False
            self.shared_servers.typed_data.servers_list[1].reservation = "Odelia"
            self.shared_servers.typed_data.servers_list[1].since = time.time()

            self.logger.info("SSH command sent!")

            self.shared_servers.dataChanged.emit()

        self.logger.info(f"Thread <SSH_POLLING> is shutting down")

    def _data_saver(self):
        """
        Periodically serialize `self.servers_data` to JSON files in
        the directory specified by SAVING_NETWORK_DIRECTORY.
        """
        self.logger.info(f"Thread <DATA_SAVER> started!")

        # Ensure the directory exists
        save_dir = Path(self.config.SAVING_NETWORK_DIRECTORY)
        save_dir.mkdir(parents=True, exist_ok=True)

        while not self.stop_master_event.is_set():
            self.stop_master_event.wait(self.config.SAVING_INTERVAL / 1000)

            filename = save_dir / "ServersData.json"
            try:
                data = self.shared_servers.data.to_dict()
            except Exception as e:
                self.logger.error(f"Failed to serialize servers_data: {e}")
                continue

            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    text = json.dumps(data, ensure_ascii=False, indent=2)
                    f.write(text)
                self.logger.info(f"Saved servers_data snapshot to {filename}")
            except Exception as e:
                self.logger.error(f"Error writing to {filename}: {e}")

        self.logger.info(f"Thread <DATA_SAVER> is shutting down")

    def shutdown(self):
        self._send_leave()
        self.stop_core_event.set()
        self.stop_master_event.set()
        self.stop_slave_event.set()
        self.udp_sender_socket.close()

        if self.heartbeat_sender_thread.is_alive():
            self.heartbeat_sender_thread.join(1)
        if self.udp_listener_thread.is_alive():
            self.udp_listener_thread.join(1)
        if self.tcp_server_thread.is_alive():
            self.tcp_server_thread.join(1)
        if self.tcp_client_thread.is_alive():
            self.tcp_client_thread.join(1)
        if self.ssh_polling_thread.is_alive():
            self.ssh_polling_thread.join(1)
        if self.data_saver_thread.is_alive():
            self.data_saver_thread.join(1)

        for thread in self.active_client_threads:
            if thread.is_alive():
                thread.join(1)

    def _send_leave(self):
        msg = LeaveNotificationMessage(self.ip)
        self.logger.info("Sending leaving message...")
        self.udp_sender_socket.sendto(msg.to_json().encode(), ('<broadcast>', self.config.UDP_PORT))
        self.logger.info("Sent LeaveNotification")

