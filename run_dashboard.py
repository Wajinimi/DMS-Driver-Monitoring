import socket
import subprocess
import sys

import yaml

from src.phase8.dashboard_server import app


def port_in_use(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def pids_on_port(port):
    result = subprocess.run(
        ["lsof", "-ti", f":{port}"],
        capture_output=True,
        text=True,
    )
    return [pid.strip() for pid in result.stdout.strip().split("\n") if pid.strip()]


if __name__ == "__main__":
    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    cfg = config["dashboard"]
    host, port = cfg["host"], cfg["port"]

    if port_in_use(host, port):
        pids = pids_on_port(port)
        print(f"Port {port} is already in use (PID: {', '.join(pids) or 'unknown'}).")
        print("Stop the old server first:")
        print("  python3 stop_dashboard.py")
        print("Or press Ctrl+C in the terminal where run_dashboard.py is running.")
        sys.exit(1)

    print("Open http://%s:%s in your browser" % (host, port))
    app.run(host=host, port=port, debug=True, use_reloader=False)
