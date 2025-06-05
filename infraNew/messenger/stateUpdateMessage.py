from infraNew.messenger.generalMessage import GeneralMessage
from models.clusterView import ClusterView
from models.serversData import ServersData
from models.userRequests import UserRequests


class StateUpdateMessage(GeneralMessage):

    def __init__(self, servers_data, cluster_view, user_requests):
        self.servers_data: ServersData = servers_data
        self.cluster_view: ClusterView = cluster_view
        self.user_requests: UserRequests = user_requests

    def get_payload(self):
        return {"ServersData": self.servers_data.to_dict(),
                "ClusterView": self.cluster_view.to_dict(),
                "UserRequests": self.user_requests.to_dict()}

    def to_json(self):
        return self._to_json("StateUpdate")
