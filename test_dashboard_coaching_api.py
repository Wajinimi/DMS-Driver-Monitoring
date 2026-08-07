# Phase 10 Step 7 ,, I am  test /api/weekly-coaching while the dashboard is running
import json
import sys
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:5050"

def fetch(path):
    try:
        with urllib.request.urlopen(BASE + path, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.URLError as err:
        print("I could not connect — start the dashboard first:")
        print("  python3 run_dashboard.py")
        print("Error:", err.reason)
        sys.exit(1)

# I use end_date that matches our SQLite test trips
data = fetch("/api/weekly-coaching?end_date=2026-07-25")

print("Score:", data["safety_score"], "/100 —", data["band"])
print("Recommendations:", len(data["recommendations"]))
for rec in data["recommendations"]:
    print(rec["rule"], "→", rec["message"])

assert data["has_data"] is True
assert len(data["recommendations"]) >= 3
print("\nStep 10.7 API test passed.")