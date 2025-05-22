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


def load_config(file="config.json"):
    path = os.path.join(os.getcwd(), "infrastructure", file)
    with open(path) as f:
        return json.load(f)


def get_self_id():
    try:
        return os.uname().nodename
    except AttributeError:
        return socket.gethostname()