from infrastructure.messages.generalMessage import GeneralMessage
from models.clusterView import ClusterView
from models.serversData import ServersData
from models.usersRequests import UsersRequests


class JoinResponseMessage(GeneralMessage):

    def __init__(self, servers_data, cluster_view, user_requests):
        self.servers_data: ServersData = servers_data
        self.cluster_view: ClusterView = cluster_view
        self.user_requests: UsersRequests = user_requests

    def get_payload(self):
        return {"serversData": self.servers_data.to_dict(),
                "clusterView": self.cluster_view.to_dict(),
                "userRequests": self.user_requests.to_dict()}

    def to_json(self):
        return self._to_json("JoinResponse")

