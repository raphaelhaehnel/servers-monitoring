import sys
import threading
import time

from PySide6.QtWidgets import QApplication

from infrastructure.config_parser import ConfigParser
from front.front_launcher import launch_front
from infrastructure.shared_models.shared_clusterView import SharedClusterView
from infrastructure.shared_models.shared_isMaster import SharedIsMaster
from infrastructure.shared_models.shared_serversData import SharedServersData
from infrastructure.shared_models.shared_userRequests import SharedUserRequests
from infrastructure.user import User
from models.clusterView import ClusterView
from models.serversData import ServersData
from models.userRequests import UserRequests
from front.resources.stylesheet import style

if __name__ == '__main__':

    # Initiate the shared data
    servers_data: ServersData = ServersData()
    cluster_view: ClusterView = ClusterView()
    user_requests: UserRequests = UserRequests()
    is_master = False  # Must always be false at the beginning

    is_admin = True

    # Wrap the data in QObject wrappers in ordered to be shared
    shared_servers = SharedServersData(servers_data)
    shared_cluster = SharedClusterView(cluster_view)
    shared_requests = SharedUserRequests(user_requests)
    shared_master = SharedIsMaster(is_master)

    try:
        config = ConfigParser()

    except Exception as e:
        print(f"Failed to load configuration: {e}", file=sys.stderr)
        sys.exit(1)

    user = User(config, shared_servers, shared_cluster, shared_requests, shared_master)
    backend_thread = threading.Thread(target=user.start, daemon=True)
    backend_thread.start()

    app = QApplication(sys.argv)
    app.setStyleSheet(style)

    # Tell Qt to call user.shutdown() just before the app quits
    app.aboutToQuit.connect(user.shutdown)

    window = launch_front(shared_servers, shared_cluster, shared_requests, shared_master, is_admin)
    window.show()

    # Enter Qt main loop. When the user closes the window, this will emit aboutToQuit.
    ret = app.exec()

    # (Optional) wait for backend to finish
    backend_thread.join()

    sys.exit(ret)
