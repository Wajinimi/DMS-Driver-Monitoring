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

# Fake weekly reports to test each band
cases = [
    {"name": "High risk", "report": {
        "has_data": True, "safety_score": 65.0, "band": "High risk",
        "top_contributors": [{"behavior": "magazine"}],
    }},
    {"name": "Fair", "report": {
        "has_data": True, "safety_score": 75.0, "band": "Fair",
        "top_contributors": [{"behavior": "eat"}],
    }},
    {"name": "Good", "report": {
        "has_data": True, "safety_score": 85.0, "band": "Good",
        "top_contributors": [{"behavior": "magazine"}],
    }},
    {"name": "Excellent", "report": {
        "has_data": True, "safety_score": 93.5, "band": "Excellent",
        "top_contributors": [{"behavior": "magazine"}],
    }},
    {"name": "No data", "report": {
        "has_data": False, "safety_score": None, "band": "No data",
        "top_contributors": [],
    }},
]

for case in cases:
    recs = engine._score_band_rules(case["report"])
    print(case["name"] + ":", recs[0]["rule"], "→", recs[0]["message"])