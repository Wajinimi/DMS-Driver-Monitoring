import os
import sqlite3
import yaml

from src.phase7.analytics_logger import AnalyticsLogger

with open("config.yaml") as f:
    config = yaml.safe_load(f)

cfg = config["analytics"]

logger = AnalyticsLogger(
    db_path=cfg["db_path"],
    distraction_activities=cfg["distraction_activities"],
)

#checking the database file exists and has our 3 tables
conn = sqlite3.connect(cfg["db_path"])
tables = conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
).fetchall()
conn.close()

print("Step 2 OK  tables:", [t[0] for t in tables])
print("DB file exists:", os.path.exists(cfg["db_path"]))

