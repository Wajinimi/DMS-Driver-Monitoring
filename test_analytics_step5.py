import sqlite3
import time
import yaml
from src.phase7.analytics_logger import AnalyticsLogger


with open("config.yaml") as f:
    config = yaml.safe_load(f)

cfg = config["analytics"] #loadding the analytics config fromm my configuration
db = AnalyticsLogger(
    db_path = cfg["db_path"],
    distraction_activities = cfg["distraction_activities"],
) #i created an instance of my AnalyticsLoger class

#now starting a new trip
trip_id = db.start_trip() 

#faking 2 phase 6 alrts like my live test logs
db.log_alert({
    "activity": "eat",
    "duration": 2.1,
    "confidence": 0.52,
    "threshold": 2.0,
    "shadow_mode": True,
    "message": "Please avoid eating while driving",
    "timestamp": time.time(),
})
time.sleep(.02) #pretending a 20ms delay between alarts


db.log_alert({
    "activity": "magazine",
    "duration": 3.1,
    "confidence": 0.82,
    "threshold": 3.0,
    "shadow_mode":True,
    "message": "Please put reading material down while dribving",
    "timestamp": time.time(),
})

summary = db.end_trip()
print("Summary:",summary)

conn = sqlite3.connect(cfg["db_path"])
rows = conn.execute(
    """SELECT activity, duration_at_alert, shadow_mode
    FROM alerts
    WHERE trip_id = ?
    ORDER BY id
    """,
    (trip_id,),
).fetchall()
conn.close()

print("Alert rows:", rows)
print("Expected: alert_count=2, two rows with shadow_mode=1")
db.close()

