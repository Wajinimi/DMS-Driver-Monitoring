# pHASE 8- Serving the driver dashboard in my web browser

import logging
import os
from flask import Flask, render_template, request
import yaml
from src.phase7.analytics_logger import AnalyticsLogger
from src.phase9.safety_score_engine import SafetyScoreEngine
from src.phase10.recommendation_engine import RecommendationEngine

logger = logging.getLogger(__name__)
_template_dir = os.path.join(os.path.dirname(__file__), "templates")
app = Flask(__name__, template_folder=_template_dir)

with open("config.yaml") as f:
    _config = yaml.safe_load(f)

_analytics = AnalyticsLogger( #creating an instance of the AnalyticsLogger class so i can access the analytics data
    db_path = _config["dashboard"]["db_path"],
    distraction_activities = _config["analytics"]["distraction_activities"],
)

_score_cfg = _config["safety_score"] #this is the configuration for the safety score engine from my Phase9
_score_engine = SafetyScoreEngine(
    weights = _score_cfg["weights"],
    scale_factor = _score_cfg["scale_factor"],
    bands = _score_cfg["bands"],
    exposure_unit = _score_cfg["exposure_unit"],
    db_path = _config["dashboard"]["db_path"],
)

#This is from pHASE 10, I WANT TO BUILD THE COACHING ENGINE that turns the score report into tips
_coach_cfg = _config["coaching"]
_coach_engine = RecommendationEngine(
    behavior_tips = _coach_cfg["behavior_tips"],
    baseline_weeks = _coach_cfg["baseline_weeks"],
    increase_threshold = _coach_cfg["increase_threshold"],
    improve_threshold = _coach_cfg["improve_threshold"],
    db_path = _config["dashboard"]["db_path"],
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


# ENDPOINT 3: Weekly safety score report (Phase 9)
@app.route("/api/weekly-report")
def api_weekly_report():
    end_date = request.args.get("end_date")
    report = _score_engine.compute_weekly_score(end_date=end_date)
    return report

#MMy ENDPOIT 4 : This is the full week coaching report from phase 10
@app.route("/api/weekly-coaching")
def api_weekly_coaching():
    end_date = request.args.get("end_date") #this will read optional end date from my browser
    weekly_report = _score_engine.compute_weekly_score(end_date=end_date) # i am getting the ohase 9 scorec report first
    coaching = _coach_engine.generate_weekly_coaching(weekly_report, end_date=end_date) #i pass the report into pHASE 10 to add recommendations + trends
    return coaching