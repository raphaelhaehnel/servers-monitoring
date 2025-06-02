import threading

from models.userRequest import UserRequest


class UserRequests:
    def __init__(self):
        self.requests: list[UserRequest] = []
        self.lock = threading.Lock()

    def add(self, req: UserRequest):
        with self.lock:
            self.requests.append(req)

    def to_list(self):
        with self.lock:
            return [r.to_dict() for r in self.requests]