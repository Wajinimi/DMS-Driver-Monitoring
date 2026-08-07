"""Stop the Flask dashboard if it is still running on the configured port."""

import subprocess
import sys

import yaml

with open("config.yaml") as f:
    port = yaml.safe_load(f)["dashboard"]["port"]

result = subprocess.run(
    ["lsof", "-ti", f":{port}"],
    capture_output=True,
    text=True,
)
pids = [pid.strip() for pid in result.stdout.strip().split("\n") if pid.strip()]

if not pids:
    print(f"No process is using port {port}.")
    sys.exit(0)

for pid in pids:
    subprocess.run(["kill", pid], check=False)

print(f"Stopped dashboard on port {port} (PID: {', '.join(pids)})")
