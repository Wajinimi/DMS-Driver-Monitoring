#This is my pHASE 9 step 7.3, i want to verfiy api/weekly-report while dashboard is running


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
        print("Could not connect to the dashboard at", BASE)
        print("Start it first in another terminal (and leave it running):")
        print("  cd '/Users/dell/DMS Cursor'")
        print("  python3 run_dashboard.py")
        print("Error:", err.reason)
        sys.exit(1)


def main():
    health = fetch("/health")
    print("Health:", health)

    report = fetch("/api/weekly-report?end_date=2026-07-25")
    print("Week:", report["week_start"], "→", report["week_end"])
    print("Score:", report["safety_score"], "/100 —", report["band"])
    print("Top contributors:", report["top_contributors"])

    assert report["has_data"] is True
    assert report["safety_score"] == 93.5
    assert report["top_contributors"][0]["behavior"] == "magazine"
    print("\nAll API checks passed.")


if __name__ == "__main__":
    main()
    
