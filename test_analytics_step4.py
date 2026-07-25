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

# I simulate: normal → eat for 4s → normal → magazine for 7s
t0 = time.time()
db.update_state("normal_driving", 0.3, t0)

t1 = time.time()
db.update_state("eat", 0.72, t1)
time.sleep(0.5)
db.update_state("eat", 0.65, t1)

t2 = time.time()
db.update_state("normal_driving", 0.4, t2)

t3 = time.time()
db.update_state("magazine", 0.91, t3)
time.sleep(0.5)
db.update_state("magazine", 0.95, t3)

t4 = time.time()
db.update_state("normal_driving", 0.35, t4)

summary = db.end_trip()
print("Summary:", summary)

conn = sqlite3.connect(cfg["db_path"])
rows = conn.execute(
    "SELECT activity, duration_sec, max_confidence FROM activities WHERE trip_id = ?",
    (trip_id,),
).fetchall()
conn.close()

print("Activity rows:", rows)
print("Expected: 2 rows (eat + magazine), normal_driving not saved")
db.close()