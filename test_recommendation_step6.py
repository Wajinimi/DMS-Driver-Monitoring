# Phase 10 Step 6 — I test the full weekly coaching report (score + tips + trends)
import yaml

from src.phase10.recommendation_engine import RecommendationEngine
from src.phase9.safety_score_engine import SafetyScoreEngine

# I load both Phase 9 (score) and Phase 10 (coaching) settings from config.yaml
with open("config.yaml") as f:
    config = yaml.safe_load(f)

score_cfg = config["safety_score"]
coach_cfg = config["coaching"]
db_path = config["analytics"]["db_path"]

# I build the safety score engine first — coaching needs its weekly report as input
score_engine = SafetyScoreEngine(
    weights=score_cfg["weights"],
    scale_factor=score_cfg["scale_factor"],
    bands=score_cfg["bands"],
    exposure_unit=score_cfg["exposure_unit"],
    db_path=db_path,
)

# I build the recommendation engine — it adds rules, tips, and trend messages
coach_engine = RecommendationEngine(
    behavior_tips=coach_cfg["behavior_tips"],
    baseline_weeks=coach_cfg["baseline_weeks"],
    increase_threshold=coach_cfg["increase_threshold"],
    improve_threshold=coach_cfg["improve_threshold"],
    db_path=db_path,
)

# I use end_date that matches our test trips in SQLite (Jul 23–25)
end_date = "2026-07-25"
weekly_report = score_engine.compute_weekly_score(end_date=end_date)
coaching = coach_engine.generate_weekly_coaching(weekly_report, end_date=end_date)

print("Week:", coaching["week_start"], "→", coaching["week_end"])
print("Score:", coaching["safety_score"], "/100 —", coaching["band"])
print("Trends:", coaching["trends"])
print("Recommendations:", len(coaching["recommendations"]))
print()

# I print each recommendation so I can see which rule fired
for rec in coaching["recommendations"]:
    print(rec["rule"], "→", rec["message"])

# I sanity-check we got score message + 2 behavior tips for our test data
assert coaching["has_data"] is True
assert coaching["safety_score"] == 93.5
assert len(coaching["recommendations"]) >= 3
rules = [r["rule"] for r in coaching["recommendations"]]
assert "excellent_score" in rules
assert "behavior_tip_magazine" in rules
assert "behavior_tip_eat" in rules
print("\nStep 10.6 OK — full coaching report generated.")
