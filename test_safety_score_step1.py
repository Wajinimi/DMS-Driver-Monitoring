import yaml
from src.phase9.safety_score_engine import SafetyScoreEngine

with open("config.yaml") as f:
    config = yaml.safe_load(f)

cfg = config["safety_score"] #this is the configuration for the safety score engine
engine = SafetyScoreEngine(
    weights = cfg["weights"],
    scale_factor = cfg["scale_factor"],
    bands = cfg["bands"],
    exposure_unit = cfg["exposure_unit"],

)
print("Step 1 is OK - SafetyScoreEngine creatted")
print("Weights:", cfg["weights"])
print("Bands:", cfg["bands"])
