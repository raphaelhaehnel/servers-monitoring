import time
from datetime import timedelta

from models.serversData import ServersData


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

def set_host_available(data: ServersData, host_name):
    """
    Mark the given host as available in the JSON file at `path`.
    Updates the 'available' flag to True and sets 'since' to the current timestamp.
    """
    # Update matching entry
    updated = False
    for entry in data.servers_list:
        if entry.host == host_name:
            entry.available = True
            entry.since = -1
            entry.reservation = "Available"
            updated = True
            break

    if not updated:
        raise RuntimeError(f"Host '{host_name}' not found in data file.")

    return True

def book_server(data: ServersData, host_name, user_name, comment):
    # Update matching entry
    updated = False
    for entry in data.servers_list:
        if entry.host == host_name:
            entry.available = False
            entry.since = int(time.time())
            entry.reservation = user_name
            entry.comment = comment
            updated = True
            break

    if not updated:
        raise RuntimeError(f"Host '{host_name}' not found in data file.")

    return True