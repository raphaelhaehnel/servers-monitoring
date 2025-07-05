import time

import paramiko

from infrastructure.config_parser import ConfigParser


def ssh_echo_test(config: ConfigParser, host: str, commands: set[str]):
    # 1) Create client and auto‑add host key (since our server auto‑generates)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # 2) Connect
    print(f"Connecting to {host}:{config.SSH_PORT} as {config.SSH_USERNAME}…")
    client.connect(hostname=host, port=config.SSH_PORT, username=config.SSH_USERNAME, password=config.SSH_PASSWORD)
    print("Connected!")

    # 3) Open a shell channel
    chan = client.invoke_shell()
    time.sleep(0.5)  # give server time to send its welcome banner

    # 4) Read initial banner
    if chan.recv_ready():
        banner = chan.recv(1024).decode('utf-8')
        print("Server banner:", banner.strip())

    # Prepare dict to collect responses
    responses: dict[str, str] = {}

    # 5) Send a few messages and print echoes
    for command in commands:
        print(f"--> {command}")
        chan.send(command + "\n")
        time.sleep(0.2)  # wait for echo

        # Read all available data for this command
        buffer = []
        while chan.recv_ready():
            chunk = chan.recv(1024).decode('utf-8')
            buffer.append(chunk)

        response = "".join(buffer).strip()
        responses[command] = response

    # 6) Close channel and connection
    chan.close()
    client.close()
    print("Disconnected.")

    return responses
