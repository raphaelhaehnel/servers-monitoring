from infrastructure.messages.generalMessage import GeneralMessage


class FetchStateMessage(GeneralMessage):

    def get_payload(self):
        return None

    def to_json(self):
        return self._to_json("FetchState")
