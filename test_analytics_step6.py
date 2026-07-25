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

# seed today's activities so the query has something to readd
trip_id = db.start_trip()
now = time.time()

conn = sqlite3.connect(cfg["db_path"])
conn.execute(
    """
    INSERT INTO activities
        (trip_id, activity, start_time, end_time, duration_sec, max_confidence)
    VALUES (?, ?, ?, ?, ?, ?)
    """,
    (trip_id, "eat", now - 120, now - 60, 60.0, 0.72),
)
conn.execute(
    """
    INSERT INTO activities
        (trip_id, activity, start_time, end_time, duration_sec, max_confidence)
    VALUES (?, ?, ?, ?, ?, ?)
    """,
    (trip_id, "magazine", now - 60, now, 120.0, 0.91),
)
conn.commit()
conn.close()

db.end_trip()

# Plot 1 data
week = db.get_last_7_days_summary()
print("Plot 1 — last 7 days:")
for day in week:
    print(f"  {day['weekday']} {day['date']}: {day['total_distraction_minutes']} min")

# Plot 2 data usingtoday's date from the last entry
today = week[-1]["date"]
breakdown = db.get_activity_breakdown_for_day(today)
print(f"\nPlot 2 — breakdown for {today}:")
for row in breakdown:
    print(f"  {row['activity']}: {row['minutes']} min")

db.close()