import threading

from models.userRequest import UserRequest


class UserRequests:
    def __init__(self):
        self.requests: list[UserRequest] = []
        self.lock = threading.Lock()

    def from_json(self, data):
        self.requests = [UserRequest().from_json(entry) for entry in data]
        return self

    def add(self, req: UserRequest):
        with self.lock:
            self.requests.append(req)

    def to_list(self):
        with self.lock:
            return [r.to_dict() for r in self.requests]

    def to_dict(self):
        with self.lock:
            return [r.to_dict() for r in self.requests]