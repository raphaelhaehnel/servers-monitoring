import json
import logging
import os
import socket
from datetime import timedelta

def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    return logging.getLogger()


def load_config(file="config.json"):
    path = os.path.join(os.getcwd(), "infrastructure", file)
    with open(path) as f:
        return json.load(f)


def get_self_id():
    try:
        return os.uname().nodename
    except AttributeError:
        return socket.gethostname()

def seconds_to_elapsed(seconds):
    td = timedelta(seconds=seconds)
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