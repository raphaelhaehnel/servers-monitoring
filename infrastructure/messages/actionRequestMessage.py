from infrastructure.messages.generalMessage import GeneralMessage
from models.userRequest import UserRequest


class ActionRequestMessage(GeneralMessage):

    def __init__(self, user_request: UserRequest):
        self.user_request = user_request

    def get_payload(self):
        return {"userRequest": self.user_request.to_dict()}

    def to_json(self):
        return self._to_json("ActionRequest")
