from models.serversData import ServersData
from models.userRequest import UserRequest


def validate_user_request(servers_data: ServersData, user_request: UserRequest) -> bool:
    for server in servers_data.servers_list:
        if server.host == user_request.host and server.available != user_request.available:
            if ((server.reservation != "" and user_request.available) or
                    (server.reservation == "" and (not user_request.available))):
                return True
    return False
