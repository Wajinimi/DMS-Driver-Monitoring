"""
I'm simulating Phase 5 output to test Phase 6 without the webcam.
Usage: python3 test_alert_trigger.py
"""
import yaml

from src.phase6.alert_trigger import AlertTrigger

with open("config.yaml") as f:
    config = yaml.safe_load(f)

at_cfg = config["alert_trigger"]

trigger = AlertTrigger(
    duration_thresholds=at_cfg["duration_thresholds"],
    cooldown_seconds=at_cfg["cooldown_seconds"],
    shadow_mode=True,  # I keep simulation in shadow mode so no beep during tests
    normal_class=config["state_manager"]["normal_class"],
    min_speed_kmh=at_cfg["min_speed_kmh"],
    speed_gating_enabled=at_cfg["speed_gating_enabled"],
    messages=at_cfg["messages"],
)

print("--- Test 1: normal_driving never alerts ---")
result = trigger.check("normal_driving", duration=10.0, confidence=0.9)
print(f"Result: {result}\n")

print("--- Test 2: magazine below threshold (2.5s) ---")
result = trigger.check("magazine", duration=2.5, confidence=0.91)
print(f"Result: {result}\n")

print("--- Test 3: magazine at threshold (3.0s) — should SHADOW ALERT ---")
result = trigger.check("magazine", duration=3.0, confidence=0.91)
print(f"Result activity: {result['activity'] if result else None}\n")

print("--- Test 4: same magazine 1s later — cooldown blocks ---")
result = trigger.check("magazine", duration=4.0, confidence=0.90)
print(f"Result: {result}\n")

print("--- Test 5: eat at 2.0s — should alert (different class) ---")
result = trigger.check("eat", duration=2.0, confidence=0.72)
print(f"Result activity: {result['activity'] if result else None}\n")

print("Done — check logs above for SHADOW ALERT lines.")
