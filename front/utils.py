import json
import time
from datetime import timedelta

from consts import DATA_PATH
from models.serverData import ServerData


def seconds_to_elapsed(seconds):
    delta = time.time() - seconds
    td = timedelta(seconds=delta)
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes = remainder // 60

    parts = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")

    return "-".join(parts) if parts else "0"

def set_host_available(data: list[ServerData], host_name):
    """
        Mark the given host as available in the JSON file at `path`.
        Updates the 'available' flag to True and sets 'since' to the current timestamp.
        """
    # Update matching entry
    updated = False
    for entry in data:
        if entry.host == host_name:
            entry.available = True
            entry.since = 0
            entry.action = "Available"
            updated = True
            break

    if not updated:
        raise RuntimeError(f"Host '{host_name}' not found in data file.")

    # Write back to file
    with open(DATA_PATH, 'w') as f:
        json.dump([s.to_dict() for s in data], f, indent=2)

    return True

def book_server(data: list[ServerData], host_name, user_name):
    # Update matching entry
    updated = False
    for entry in data:
        if entry.host == host_name:
            entry.available = False
            entry.since = int(time.time())
            entry.action = user_name
            updated = True
            break

    if not updated:
        raise RuntimeError(f"Host '{host_name}' not found in data file.")

    # Write back to file
    with open(DATA_PATH, 'w') as f:
        json.dump([s.to_dict() for s in data], f, indent=2)

    return True