import json

from infrastructure.messages.generalMessage import GeneralMessage


class ForceMasterMessage(GeneralMessage):

    def __init__(self, ip):
        self.ip = ip

    def get_payload(self):
        return {"requestedBy": self.ip}

    def to_json(self):
        return self._to_json("ForceMaster")