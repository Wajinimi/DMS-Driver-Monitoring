# Phase 10 Step 5 — I test trend flags (increased / improved vs personal baseline)
import yaml

from src.phase10.recommendation_engine import RecommendationEngine

# I load coaching settings and db path from config.yaml
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

# I use fake numbers first so I can test logic without needing 4 weeks of real trips
this_week = {"magazine": 130.0, "eat": 80.0, "sunglasses": 100.0}
baseline = {"magazine": 100.0, "eat": 100.0, "sunglasses": 100.0}

trends = engine._compare_trends(this_week, baseline)
print("Synthetic trends:")
for t in trends:
    print(t["behavior"], t["trend"], "ratio=", t["ratio"])

# I expect magazine up 30% → increased, eat down 20% → improved, sunglasses unchanged → no flag
assert any(t["behavior"] == "magazine" and t["trend"] == "increased" for t in trends)
assert any(t["behavior"] == "eat" and t["trend"] == "improved" for t in trends)
assert not any(t["behavior"] == "sunglasses" for t in trends)
print("\nSynthetic checks passed.")

# I now hit the real DB — baseline window is empty today so trends may be []
real = engine.compute_trend_flags(end_date="2026-07-25")
print("Real DB trends:", real)
