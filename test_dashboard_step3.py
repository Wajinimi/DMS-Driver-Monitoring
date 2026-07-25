import yaml
from src.phase8.dashboard_server import app

with open("config.yaml") as f:
    config = yaml.safe_load(f)

test_date = "2026-07-23"  # I pick a day that has data in my DB

with app.test_client() as client:
    resp = client.get("/api/day/%s" % test_date)
    data = resp.get_json()

print("Status:", resp.status_code)
print("Plot 2 for %s:" % data["date"])
for row in data["activities"]:
    print("  %s: %s min" % (row["activity"], row["minutes"]))