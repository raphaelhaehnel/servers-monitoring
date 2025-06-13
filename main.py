import sys

from infrastructure.config_parser import ConfigParser
from front.front_launcher import launch_front
from infrastructure.user import User
from models.clusterView import ClusterView
from models.serversData import ServersData
from models.userRequests import UserRequests

if __name__ == '__main__':

    # Initiate the shared data
    servers_data: ServersData = ServersData()
    cluster_view: ClusterView = ClusterView()
    user_requests: UserRequests = UserRequests()
    is_admin = True
    is_master = False # Must always be false at the beginning

    # Launch the Qt UI
    launch_front(servers_data, cluster_view, user_requests, is_admin, is_master)

    try:
        config = ConfigParser()

    except Exception as e:
        print(f"Failed to load configuration: {e}", file=sys.stderr)
        sys.exit(1)

    user = User(config, servers_data, cluster_view, user_requests, is_master)
    user.start()