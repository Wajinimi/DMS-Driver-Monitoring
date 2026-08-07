import yaml

from src.phase9.safety_score_engine import SafetyScoreEngine

with open("config.yaml") as f:
    config = yaml.safe_load(f)

cfg = config["safety_score"]
db_path = config["analytics"]["db_path"]

engine = SafetyScoreEngine(
    weights=cfg["weights"],
    scale_factor=cfg["scale_factor"],
    bands=cfg["bands"],
    exposure_unit=cfg["exposure_unit"],
    db_path=db_path,
)

report = engine.compute_weekly_score(end_date="2026-07-25")

print("Week:", report["week_start"], "→", report["week_end"])
print("Has data:", report["has_data"])
print("Total driving (min):", report["total_driving_minutes"])
print("Safe driving %:", report["safe_driving_pct"])
print("Behavior %:", report["behavior_pct"])
print("Safety score:", report["safety_score"], "/100 —", report["band"])
print("Contributions:", report["contributions"])

print()
print("Also try current week (may be empty if no recent trips):")
current = engine.compute_weekly_score()
print("  Week:", current["week_start"], "→", current["week_end"], "| has_data:", current["has_data"])