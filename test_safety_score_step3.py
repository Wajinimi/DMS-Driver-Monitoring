import sqlite3
import yaml

from src.phase9.safety_score_engine import SafetyScoreEngine

with open("config.yaml") as f:
    config = yaml.safe_load(f)

cfg = config["safety_score"]
db_path = config["analytics"]["db_path"]

engine = SafetyScoreEngine(
    weights=cfg["weights"],
    scale_factor=cfg["scale_factor"],
    bands=cfg["bands"],
    exposure_unit=cfg["exposure_unit"],
    db_path=db_path,
)

conn = sqlite3.connect(db_path)
trip_row = conn.execute(
    "SELECT trip_id FROM trips ORDER BY start_time DESC LIMIT 1"
).fetchone()
conn.close()

if trip_row is None:
    print("No trips in database — run test_phase7.py first")
else:
    trip_id = trip_row[0]
    result = engine.compute_trip_score(trip_id)
    print("Trip:", trip_id)
    print("Durations (sec):", result["activity_durations_sec"])
    print("Contributions:", result["contributions"])
    print("Safety score:", result["safety_score"], "/100 —", result["band"])