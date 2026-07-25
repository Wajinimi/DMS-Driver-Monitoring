import yaml

from src.phase5.state_manager import StateManager

with open("config.yaml") as f:
    config = yaml.safe_load(f)

sm = config["state_manager"]

manager = StateManager(
    default_threshold = sm["default_threshold"],
    exit_threshold = sm["exit_threshold"],
    normal_class = sm["normal_class"],
    smoothing_windows = sm["smoothing_windows"],
)

#i am simulating flickering predictions like myPhase 4 logs
sequence = [
    {"eat": 0.10, "seatbelt": 0.72, "jacket": 0.05, "sunglasses": 0.08, "magazine": 0.05},
    {"eat": 0.15, "seatbelt": 0.25, "jacket": 0.20, "sunglasses": 0.30, "magazine": 0.10},  # below 50%
    {"eat": 0.10, "seatbelt": 0.65, "jacket": 0.10, "sunglasses": 0.10, "magazine": 0.05},
    {"eat": 0.08, "seatbelt": 0.70, "jacket": 0.08, "sunglasses": 0.09, "magazine": 0.05},
    {"eat": 0.10, "seatbelt": 0.68, "jacket": 0.07, "sunglasses": 0.10, "magazine": 0.05}, #seatblet has high confidence 3 times in a row
    {"eat": 0.60, "seatbelt": 0.15, "jacket": 0.10, "sunglasses": 0.10, "magazine": 0.05},
    {"eat": 0.65, "seatbelt": 0.10, "jacket": 0.10, "sunglasses": 0.10, "magazine": 0.05},
    {"eat": 0.70, "seatbelt": 0.08, "jacket": 0.07, "sunglasses": 0.10, "magazine": 0.05}, #eat has high conifence 3 times in a row too
]

for i, probs in enumerate(sequence):
    start_time, activity, conf, duration = manager.update(probs)
    top = max(probs, key=probs.get)
    print(f"Frame {i+1}: raw={top} ({probs[top]:.0%}) → state={activity} | duration={duration:.1f}s")