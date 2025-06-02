import logging

from infraNew.messenger.fetchStateMessage import FetchStateMessage
from infraNew.messenger.forceMasterMessage import ForceMasterMessage
from infraNew.messenger.heartbeatMessage import HeartBeatMessage
from infraNew.messenger.joinRequestMessage import JoinRequestMessage
from infraNew.messenger.joinResponseMessage import JoinResponseMessage
from infraNew.messenger.leaveNotificationMessage import LeaveNotificationMessage
from infraNew.messenger.stateUpdateMessage import StateUpdateMessage


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
                return JoinResponseMessage(payload["serversData"], payload["clusterView"], payload["userRequests"])
            elif msg_type == "LeaveNotification":
                return LeaveNotificationMessage(payload["nodeIP"])
            elif msg_type == "StateUpdate":
                return StateUpdateMessage(payload["serversData"], payload["clusterView"], payload["userRequests"])
            else:
                self.logger.error(f"Message type identified does not corresponds to any known type")
        except Exception as e:
            self.logger.error(f"Message type identified, but deserialization failed: {e}")

