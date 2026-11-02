# Phase 12 — I test DriveContext speed/ignition rules without the webcam
import yaml

from src.phase12.drive_context import DriveContext


def make_context(clock, **overrides):
    defaults = {
        "enabled": True,
        "activate_speed_kmh": 15.0,
        "deactivate_speed_kmh": 5.0,
        "deactivate_hold_sec": 10.0,
        "require_ignition_run": True,
        "mock_enabled": True,
        "mock_default_speed_kmh": 0.0,
        "mock_default_ignition": DriveContext.IGNITION_RUN,
        "clock": clock,
    }
    defaults.update(overrides)
    return DriveContext(**defaults)


def test_disabled_always_monitors():
    ctx = make_context(clock=lambda: 0.0, enabled=False)
    ctx.update()
    assert ctx.monitoring_active is True


def test_stays_off_until_15_kmh():
    ctx = make_context(clock=lambda: 0.0)
    for speed in (0, 5, 9, 10, 14.9):
        ctx.set_speed_kmh(speed)
        ctx.update()
        assert ctx.monitoring_active is False, f"should be OFF at {speed} km/h"


def test_turns_on_at_15_kmh():
    ctx = make_context(clock=lambda: 0.0)
    ctx.set_speed_kmh(15)
    ctx.update()
    assert ctx.monitoring_active is True


def test_stays_on_at_10_kmh_after_activation():
    ctx = make_context(clock=lambda: 0.0)
    ctx.set_speed_kmh(20)
    ctx.update()
    assert ctx.monitoring_active is True

    ctx.set_speed_kmh(10)
    ctx.update()
    assert ctx.monitoring_active is True


def test_turns_off_after_hold_below_5_kmh():
    times = [0.0]

    def clock():
        return times[0]

    ctx = make_context(clock=clock, deactivate_hold_sec=10.0)
    ctx.set_speed_kmh(20)
    ctx.update()

    ctx.set_speed_kmh(3)
    ctx.update()
    assert ctx.monitoring_active is True

    times[0] = 9.0
    ctx.update()
    assert ctx.monitoring_active is True

    times[0] = 10.0
    ctx.update()
    assert ctx.monitoring_active is False


def test_ignition_off_forces_standby():
    ctx = make_context(clock=lambda: 0.0)
    ctx.set_speed_kmh(30)
    ctx.update()
    assert ctx.monitoring_active is True

    ctx.set_ignition(DriveContext.IGNITION_OFF)
    ctx.update()
    assert ctx.monitoring_active is False


def test_config_loads():
    with open("config.yaml") as f:
        config = yaml.safe_load(f)
    dg = config["drive_gating"]
    assert dg["activate_speed_kmh"] == 15


if __name__ == "__main__":
    test_disabled_always_monitors()
    test_stays_off_until_15_kmh()
    test_turns_on_at_15_kmh()
    test_stays_on_at_10_kmh_after_activation()
    test_turns_off_after_hold_below_5_kmh()
    test_ignition_off_forces_standby()
    test_config_loads()
    print("All DriveContext tests passed.")
