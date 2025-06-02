import json

from infraNew.messenger.generalMessage import GeneralMessage


class StateUpdateMessage(GeneralMessage):

    def __init__(self, servers_data, cluster_view, user_requests):
        self.servers_data = servers_data
        self.cluster_view = cluster_view
        self.user_requests = user_requests

    def get_payload(self):
        return {"ServersData": self.servers_data,
                "ClusterView": self.cluster_view,
                "UserRequests": self.user_requests}

    def to_json(self):
        return self._to_json("StateUpdate")
