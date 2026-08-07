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
print("Safety score:", report["safety_score"], "/100 —", report["band"])
print("Contributions:", report["contributions"])
print("Top contributors (from report):", report["top_contributors"])

top = engine.get_top_contributors(
    report["contributions"],
    n=3,
    total_risk=report["total_risk"],
)
print("Top contributors (direct call):", top)
