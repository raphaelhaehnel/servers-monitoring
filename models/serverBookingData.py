from dataclasses import dataclass

@dataclass
class ServerBookingData:
    host_name: str
    user: str
    comment: str