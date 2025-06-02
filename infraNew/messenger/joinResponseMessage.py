import json

from infraNew.messenger.generalMessage import GeneralMessage


class JoinResponseMessage(GeneralMessage):

    def __init__(self, servers_data, cluster_view, user_requests):
        self.servers_data = servers_data
        self.cluster_view = cluster_view
        self.user_requests = user_requests

    def get_payload(self):
        return {
            "clusterView": self.cluster_view,
            "serversData": self.servers_data,
            "userRequests": self.user_requests}

    def to_json(self):
        return self._to_json("JoinResponse")
