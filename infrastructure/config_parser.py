import xml.etree.ElementTree as ET

class ConfigParser:

    def __init__(self):
        tree = ET.parse('config.xml')
        root = tree.getroot()

        self.UDP_PORT = int(root.find('UdpPort').text)
        self.TCP_PORT = int(root.find('TcpPort').text)
        self.HTTP_PORT = int(root.find('HttpPort').text)
        self.HTTP_PORT_FRONT = int(root.find('HttpPortFront').text)
        self.FETCH_INTERVAL = int(root.find('FetchInterval').text)
        self.HEARTBEAT_INTERVAL = int(root.find('HeartbeatInterval').text)
        self.HEARTBEAT_RETRIES = int(root.find('HeartbeatRetries').text)
        self.JOIN_NETWORK_INTERVAL = int(root.find('JoinNetworkInterval').text)
        self.JOIN_NETWORK_ATTEMPTS = int(root.find('JoinNetworkAttempts').text)
        self.CLIENT_TCP_TIMEOUT = int(root.find('ClientTcpTimeout').text)
        self.SAVING_NETWORK_DIRECTORY = root.find('SavingNetworkDirectory').text
        self.SAVING_INTERVAL = int(root.find('SavingInterval').text)
        self.SERVER_POLLING_INTERVAL = int(root.find('ServerPollingInterval').text)
