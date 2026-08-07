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

report = {
    "has_data": True,
    "safety_score": 93.5,
    "band": "Excellent",
    "top_contributors": [
        {"behavior": "magazine", "contribution": 32.58},
        {"behavior": "eat", "contribution": 10.52},
    ],
}

tips = engine._behavior_tips_rules(report)
print("Tips returned:", len(tips))
for rec in tips:
    print(rec["rule"], "→", rec["message"])