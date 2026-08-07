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

print("Step 10.1 OK RecommendationEngine created")
print("Tips loaded:", list(engine._behavior_tips.keys()))