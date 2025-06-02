import logging
import socket

class IpManager:

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_own_ip(self):
        # determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            return ip
        except:
            self.logger.error(f"Failed to identify user")
            return '127.0.0.1'
        finally:
            s.close()