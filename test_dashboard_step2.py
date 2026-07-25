import yaml

from src.phase8.dashboard_server import app

with open("config.yaml") as f:
    config = yaml.safe_load(f)

with app.test_client() as client:
    resp = client.get("/api/week")
    data = resp.get_json()

print("Status:", resp.status_code)
print("Plot 1 data (%d days):" % len(data["days"]))
for day in data["days"]:
    print("  %s %s: %s min" % (day["weekday"], day["date"], day["total_distraction_minutes"]))