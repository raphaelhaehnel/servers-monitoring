import logging

from infrastructure.messages.fetchStateMessage import FetchStateMessage
from infrastructure.messages.forceMasterMessage import ForceMasterMessage
from infrastructure.messages.heartbeatMessage import HeartBeatMessage
from infrastructure.messages.joinRequestMessage import JoinRequestMessage
from infrastructure.messages.joinResponseMessage import JoinResponseMessage
from infrastructure.messages.leaveNotificationMessage import LeaveNotificationMessage
from infrastructure.messages.stateUpdateMessage import StateUpdateMessage
from models.clusterView import ClusterView
from models.serversData import ServersData
from models.userRequests import UserRequests


class MessageDeserializer:

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def deserialize(self, msg):
        msg_type = msg.get('Type', None)

        if msg_type is None:
            self.logger.error(f"Message not identified as a valid message")
            return

        payload: dict = msg.get("Payload")

        try:
            if msg_type == "FetchState":
                return FetchStateMessage()
            elif msg_type == "ForceMaster":
                return ForceMasterMessage(payload["requestedBy"])
            elif msg_type == "Heartbeat":
                return HeartBeatMessage()
            elif msg_type == "JoinRequest":
                return JoinRequestMessage(payload["nodeIP"])
            elif msg_type == "JoinResponse":
                return JoinResponseMessage(ServersData().from_json(payload["serversData"]),
                                           ClusterView().from_json(payload["clusterView"]),
                                           UserRequests().from_json(payload["userRequests"]))
            elif msg_type == "LeaveNotification":
                return LeaveNotificationMessage(payload["nodeIP"])
            elif msg_type == "StateUpdate":
                return StateUpdateMessage(ServersData().from_json(payload["serversData"]),
                                          ClusterView().from_json(payload["clusterView"]),
                                          UserRequests().from_json(payload["userRequests"]))
            else:
                self.logger.error(f"Message type identified does not corresponds to any known type")
        except Exception as e:
            self.logger.error(f"Message type identified, but deserialization failed: {e}")

