# Phase 10 Step 8  I amc running a full simulation of the Recommendation Engine
import yaml
from src.phase10.recommendation_engine import RecommendationEngine
from src.phase9.safety_score_engine import SafetyScoreEngine

PASS = 0
FAIL = 0

def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print("  PASS  " + name)
    else:
        FAIL += 1
        msg = "  FAIL  " + name
        if detail:
            msg += " — " + detail
        print(msg)

with open("config.yaml") as f:
    config = yaml.safe_load(f)

score_cfg = config["safety_score"]
coach_cfg = config["coaching"]
db_path = config["analytics"]["db_path"]

score_engine = SafetyScoreEngine(
    weights=score_cfg["weights"],
    scale_factor=score_cfg["scale_factor"],
    bands=score_cfg["bands"],
    exposure_unit=score_cfg["exposure_unit"],
    db_path=db_path,
)

coach_engine = RecommendationEngine(
    behavior_tips=coach_cfg["behavior_tips"],
    baseline_weeks=coach_cfg["baseline_weeks"],
    increase_threshold=coach_cfg["increase_threshold"],
    improve_threshold=coach_cfg["improve_threshold"],
    db_path=db_path,
)

print("Phase 10 — Recommendation Engine (full simulation)")

# 1 Score band rules 
print("\n1) Score band rules")
fake_high_risk = {
    "has_data": True, "safety_score": 65.0, "band": "High risk",
    "top_contributors": [{"behavior": "magazine"}],
}
recs = coach_engine._score_band_rules(fake_high_risk)
check("high risk rule fires", recs[0]["rule"] == "high_risk_score")

# 2 Behavior tips 
print("\n2) Behavior tips")
fake_excellent = {
    "has_data": True,
    "top_contributors": [
        {"behavior": "magazine"},
        {"behavior": "eat"},
    ],
}
tips = coach_engine._behavior_tips_rules(fake_excellent)
check("two tips returned", len(tips) == 2)

# 3 Trend comparison 
print("\n3) Trend flags (synthetic)")
this_week = {"magazine": 130.0, "eat": 80.0}
baseline = {"magazine": 100.0, "eat": 100.0}
trends = coach_engine._compare_trends(this_week, baseline)
check("magazine increased", any(t["behavior"] == "magazine" and t["trend"] == "increased" for t in trends))
check("eat improved", any(t["behavior"] == "eat" and t["trend"] == "improved" for t in trends))

# 4 Full coaching report from my real DB) 
print("\n4) Full coaching report (SQLite)")
end_date = "2026-07-25"
weekly = score_engine.compute_weekly_score(end_date=end_date)
coaching = coach_engine.generate_weekly_coaching(weekly, end_date=end_date)

check("has_data true", coaching["has_data"] is True)
check("score 93.5", coaching["safety_score"] == 93.5)
check("at least 3 recommendations", len(coaching["recommendations"]) >= 3)

rules = [r["rule"] for r in coaching["recommendations"]]
check("excellent_score in rules", "excellent_score" in rules)
check("behavior_tip_magazine in rules", "behavior_tip_magazine" in rules)

print("\nSample recommendations:")
for rec in coaching["recommendations"]:
    print(" ", rec["rule"], "→", rec["message"][:60] + "...")

print("\n" + "=" * 50)
print("Results: " + str(PASS) + " passed, " + str(FAIL) + " failed")
if FAIL:
    raise SystemExit(1)
print("All Phase 10 simulations passed.")