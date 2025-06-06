import signal
import argparse

from front.front_launcher import launch_front
from infrastructure.interface import start_control_server
from infrastructure.utils import load_config, get_self_id, setup_logger
from infrastructure.discovery import Discovery
from infrastructure.election import LeaderElection
from infrastructure.server import MasterServer
from infrastructure.client import PeerClient

logger = setup_logger()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--manual-master', action='store_true', help='Force self as master')
    args = parser.parse_args()

    config = load_config()
    config['self_id'] = get_self_id()

    # Start discovery
    disc = Discovery(config)
    disc.start()

    # Leader election
    election = LeaderElection(config, disc, manual_master=args.manual_master)
    election.start()
    control_srv = start_control_server(election, port=8000)

    # Launch the Qt UI
    launch_front()

    # Start server (master)
    server = MasterServer(election, config)
    server.start()

    # Peer client
    client = PeerClient(election, config)

    def on_exit(signum, frame):
        logger.info("Shutting down...")
        election.resign()
        disc.stop()
        server.stop()
        control_srv.shutdown()
        control_srv.server_close()
        exit(0)

    signal.signal(signal.SIGINT, on_exit)
    signal.signal(signal.SIGTERM, on_exit)

    # Keep running
    try:
        import time

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        on_exit(None, None)