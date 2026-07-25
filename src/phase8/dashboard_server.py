# pHASE 8- Serving the driver dashboard in my web browser

import logging
import os

from flask import Flask, render_template
import yaml
from src.phase7.analytics_logger import AnalyticsLogger

logger = logging.getLogger(__name__)
_template_dir = os.path.join(os.path.dirname(__file__), "templates")
app = Flask(__name__, template_folder=_template_dir)

with open("config.yaml") as f:
    _config = yaml.safe_load(f)

_analytics = AnalyticsLogger( #creating an instance of the AnalyticsLogger class so i can access the analytics data
    db_path = _config["dashboard"]["db_path"],
    distraction_activities = _config["analytics"]["distraction_activities"],
)

@app.route("/health") #creating a health check edpoint to check if the server is running
def health(): #this function will return a simple ok response
    return {"status": "ok", "phase": 8}

@app.route("/")  #this is to serve the dahsboard HTML page
def dashboard():
    return render_template("dashboard.html")

#ENDPOINT 1: Get the last 7 days summary of activities
@app.route("/api/week")
def api_week():
    days = _analytics.get_last_7_days_summary()
    return {"days": days}
    
#ENDPOINT 2 : Get the per-activity distraction minutes for a specific day
@app.route("/api/day/<date_str>")
def api_day(date_str):
    activities = _analytics.get_activity_breakdown_for_day(date_str)
    return {"date": date_str, "activities": activities}
