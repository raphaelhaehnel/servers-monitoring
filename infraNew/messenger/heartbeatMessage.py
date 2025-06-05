from infraNew.messenger.generalMessage import GeneralMessage


class HeartBeatMessage(GeneralMessage):

    def get_payload(self):
        return None

    def to_json(self):
        return self._to_json("Heartbeat")