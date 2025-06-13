import json
from abc import abstractmethod


class GeneralMessage:

    def get_type(self):
        return self.__class__

    @abstractmethod
    def get_payload(self):
        pass

    @abstractmethod
    def to_json(self):
        pass

    def _to_json(self, msg_type):
        return json.dumps({"Type": msg_type, "Payload": self.get_payload()})

    def get_name(self):
        return self.__class__.__name__