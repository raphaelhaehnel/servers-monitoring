import sys

from PySide6.QtWidgets import QApplication

from front.resources.resources_rc import qInitResources, qCleanupResources
from front.resources.stylesheet import style
from front.widgets.mainWindow import MainWindow
from infrastructure.shared_models.shared_clusterView import SharedClusterView
from infrastructure.shared_models.shared_isMaster import SharedIsMaster
from infrastructure.shared_models.shared_serversData import SharedServersData
from infrastructure.shared_models.shared_userRequests import SharedUserRequests


def launch_front(shared_servers: SharedServersData, shared_cluster: SharedClusterView, shared_requests: SharedUserRequests, shared_master: SharedIsMaster, is_admin: bool):
    qInitResources()
    app = QApplication(sys.argv)
    app.setStyleSheet(style)

    window = MainWindow(shared_servers, shared_cluster, shared_requests, shared_master, is_admin)
    window.resize(1000, 600)
    window.show()
    sys.exit(app.exec())