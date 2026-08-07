import yaml
from src.phase10.recommendation_engine import RecommendationEngine

with open("config.yaml") as f:
    config = yaml.safe_load(f)

cfg = config["coaching"]
engine = RecommendationEngine(
    behavior_tips=cfg["behavior_tips"],
    baseline_weeks=cfg["baseline_weeks"],
    increase_threshold=cfg["increase_threshold"],
    improve_threshold=cfg["improve_threshold"],
    db_path=config["analytics"]["db_path"],
)

baseline = engine.compute_personal_baseline(end_date="2026-07-25")

print("Baseline window:", baseline["baseline_start"], "→", baseline["baseline_end"])
print("Weeks averaged:", baseline["weeks"])
print("Avg sec/week per behavior:", baseline["avg_seconds_per_week"])