import json
import logging
import os
import socket

def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    return logging.getLogger()


def load_config(path="config.json"):
    with open(path) as f:
        return json.load(f)


def get_self_id():
    try:
        # POSIX-style
        return os.uname().nodename
    except AttributeError:
        # Fallback for Windows
        return socket.gethostname()