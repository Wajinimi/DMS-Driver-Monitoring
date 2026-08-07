import yaml
from src.phase9.safety_score_engine import SafetyScoreEngine

with open("config.yaml") as f:
    config = yaml.safe_load(f)

cfg = config["safety_score"]


engine = SafetyScoreEngine(
    weights = cfg["weights"],
    scale_factor = cfg["scale_factor"],
    bands = cfg["bands"],
    exposure_unit = cfg["exposure_unit"],
)

#i want to simulate one week of distraction time (seconds)
week_durations = {
    "eat": 90.0,   #1.5 miniutes
    "magazine": 120.0,  # 2.0 minuts
    "sunglasses": 30.0, #0.5 minutes
}

result = engine.score_from_durations(week_durations)

print("Contributions:", result["contributions"])
print("Total Risk:", result["total_risk"])
print("Safety score:", result["safety_score"], "/100")
print("Band:", result["band"])


print("my exprected total_risk = 15.5, score = 97.7 Excellent")
