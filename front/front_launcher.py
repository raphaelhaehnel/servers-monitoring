import sys

from PySide6.QtWidgets import QApplication

from front.resources.resources_rc import qInitResources, qCleanupResources
from front.resources.stylesheet import style
from front.widgets.mainWindow import MainWindow
from models.clusterView import ClusterView
from models.serversData import ServersData
from models.userRequests import UserRequests


def launch_front(servers_data: ServersData, cluster_view: ClusterView, user_requests: UserRequests, is_admin: bool, is_master: bool):
    qInitResources()
    app = QApplication(sys.argv)
    app.setStyleSheet(style)

    window = MainWindow(servers_data, cluster_view, user_requests, is_admin=is_admin, is_master=is_master)
    window.resize(1000, 600)
    window.show()
    sys.exit(app.exec())