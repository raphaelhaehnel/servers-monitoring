from infrastructure.messages.generalMessage import GeneralMessage


class JoinRequestMessage(GeneralMessage):

    def __init__(self, ip):
        self.ip = ip

    def get_payload(self):
        return {"nodeIP": self.ip}

    def to_json(self):
        return self._to_json("JoinRequest")
