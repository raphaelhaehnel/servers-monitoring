import logging
import socket

class IpManager:

    logger = logging.getLogger("IpManager")

    @staticmethod
    def get_own_ip() -> str:
        # determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            return ip
        except:
            logger.error(f"Failed to identify user")
            return '127.0.0.1'
        finally:
            s.close()

    @staticmethod
    def get_own_ips() -> set[str]:
        hostname = socket.gethostname()
        _, _, host_ips = socket.gethostbyname_ex(hostname)
        return set(host_ips)