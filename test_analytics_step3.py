import sqlite3
import time
import yaml

from src.phase7.analytics_logger import AnalyticsLogger

with open("config.yaml") as f:
    config = yaml.safe_load(f)

cfg = config["analytics"]

db = AnalyticsLogger(
    db_path=cfg["db_path"],
    distraction_activities=cfg["distraction_activities"],
)

trip_id = db.start_trip()
print("Started:", trip_id)

time.sleep(1)  # I pretend this is a 1-second drive

summary = db.end_trip()
print("Summary:", summary)

#verifying the row landed in SQLite
conn = sqlite3.connect(cfg["db_path"])
row = conn.execute(
    "SELECT trip_id, start_time, end_time, total_distraction_sec, alert_count FROM trips WHERE trip_id = ?",
    (trip_id,),
).fetchone()
conn.close()

print("DB row:", row)
db.close()