# Phase 11 Step 1  i am testing the email formatter, not sending yet

import yaml
from src.phase9.safety_score_engine import SafetyScoreEngine
from src.phase10.recommendation_engine import RecommendationEngine
from src.phase11.weekly_report_formatter import WeeklyReportFormatter

with open("config.yaml") as f:
    config = yaml.safe_load(f)

score_engine = SafetyScoreEngine(
    weights=config["safety_score"]["weights"],
    scale_factor=config["safety_score"]["scale_factor"],
    bands=config["safety_score"]["bands"],
    exposure_unit=config["safety_score"]["exposure_unit"],
    db_path=config["analytics"]["db_path"],
)
coach_engine = RecommendationEngine(
    behavior_tips=config["coaching"]["behavior_tips"],
    baseline_weeks=config["coaching"]["baseline_weeks"],
    increase_threshold=config["coaching"]["increase_threshold"],
    improve_threshold=config["coaching"]["improve_threshold"],
    db_path=config["analytics"]["db_path"],
)

weekly = score_engine.compute_weekly_score(end_date="2026-07-25")
coaching = coach_engine.generate_weekly_coaching(weekly, end_date="2026-07-25")

formatter = WeeklyReportFormatter(
    driver_name="John",
    dashboard_url="http://127.0.0.1:5050",
)

print("SUBJECT:")
print(formatter.format_subject(coaching))
print()
print("BODY:")
print(formatter.format_plain_text(coaching))