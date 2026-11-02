# Model Version 2 — testing OBD speed → DriveContext 
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from dms_v2.drive_context import DriveContext
from dms_v2.obd_speed_provider import ObdSpeedProvider, _to_kmh


class FakeResponse:
    def __init__(self, value, is_null=False):
        self.value = value
        self._is_null = is_null

    def is_null(self):
        return self._is_null


class FakeCommands:
    SPEED = "SPEED"
    RPM = "RPM"


class FakeObdModule:
    commands = FakeCommands()


class FakeAsyncConnection:
    def __init__(self, speed_kmh=0.0, rpm=800.0, connected=True):
        self.speed_kmh = speed_kmh
        self.rpm = rpm
        self._connected = connected
        self.supported_commands = {FakeCommands.SPEED, FakeCommands.RPM}

    def is_connected(self):
        return self._connected

    def watch(self, command, force=False):
        return None

    def start(self):
        return None

    def stop(self):
        return None

    def close(self):
        return None

    def protocol_name(self):
        return "FAKE"

    def query(self, command):
        if command == FakeCommands.SPEED:
            return FakeResponse(self.speed_kmh)
        if command == FakeCommands.RPM:
            return FakeResponse(self.rpm)
        return FakeResponse(None, is_null=True)


def test_to_kmh():
    assert _to_kmh(42) == 42.0
    assert _to_kmh(None) is None


def test_obd_applies_speed_and_rpm_to_drive_context():
    conn = FakeAsyncConnection(speed_kmh=40.0, rpm=1500.0)
    provider = ObdSpeedProvider(connection=conn)
    provider._obd_module = FakeObdModule()
    assert provider.connect() is True

    ctx = DriveContext()
    reading = provider.apply_to(ctx)
    ctx.update()

    assert reading["speed_kmh"] == 40.0
    assert reading["rpm"] == 1500.0
    assert reading["ignition"] == DriveContext.IGNITION_RUN
    assert ctx.monitoring_active is True
    provider.close()


def test_low_rpm_is_acc_and_stays_standby():
    conn = FakeAsyncConnection(speed_kmh=0.0, rpm=50.0)
    provider = ObdSpeedProvider(connection=conn, rpm_run_threshold=400)
    provider._obd_module = FakeObdModule()
    provider.connect()

    ctx = DriveContext()
    provider.apply_to(ctx)
    ctx.update()
    assert ctx.ignition == DriveContext.IGNITION_ACC
    assert ctx.monitoring_active is False
    provider.close()


def test_stays_off_until_fifteen_then_stays_on_at_ten():
    times = [0.0]

    def clock():
        return times[0]

    ctx = DriveContext(clock=clock)
    ctx.set_ignition(DriveContext.IGNITION_RUN)

    ctx.set_speed_kmh(10)
    ctx.update()
    assert ctx.monitoring_active is False

    ctx.set_speed_kmh(15)
    ctx.update()
    assert ctx.monitoring_active is True

    ctx.set_speed_kmh(10)
    ctx.update()
    assert ctx.monitoring_active is True


def test_disconnected_obd_turns_ignition_off():
    conn = FakeAsyncConnection(connected=False)
    provider = ObdSpeedProvider(connection=conn)
    provider._obd_module = FakeObdModule()
    reading = provider.poll()
    assert reading["connected"] is False
    assert reading["ignition"] == DriveContext.IGNITION_OFF
    assert reading["speed_kmh"] is None


if __name__ == "__main__":
    test_to_kmh()
    test_obd_applies_speed_and_rpm_to_drive_context()
    test_low_rpm_is_acc_and_stays_standby()
    test_stays_off_until_fifteen_then_stays_on_at_ten()
    test_disconnected_obd_turns_ignition_off()
    print("All Model V2 OBD tests passed.")
