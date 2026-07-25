import yaml

from src.phase5.state_manager import StateManager

with open("config.yaml") as f:
    config = yaml.safe_load(f) 

sm = config["state_manager"]
manager = StateManager(
    default_threshold = sm["default_threshold"], #i am using the default threshold from my configuration
    exit_threshold = sm["exit_threshold"], 
    normal_class = sm["normal_class"],
)

# Test 1: high confidence should pass through
probs1 = {"eat": 0.10, "seatbelt": 0.72, "jacket": 0.05, "sunglasses": 0.08, "magazine": 0.05}
activity, conf = manager.filter_threshold(probs1)
print(f"Test 1: {activity} ({conf:.0%})")   # expect: seatbelt (72%)

# Test 2: low confidence should become normal_driving
probs2 = {"eat": 0.25, "seatbelt": 0.30, "jacket": 0.20, "sunglasses": 0.15, "magazine": 0.10}
activity, conf = manager.filter_threshold(probs2)
print(f"Test 2: {activity} ({conf:.0%})")   # expect: normal_driving (30%)

# Test 3: exactly at threshold should be the top class
probs3 = {"eat": 0.50, "seatbelt": 0.20, "jacket": 0.10, "sunglasses": 0.10, "magazine": 0.10}
activity, conf = manager.filter_threshold(probs3)
print(f"Test 3: {activity} ({conf:.0%})")   # expect: eat (50%)
