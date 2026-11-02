# Phase 12 — I test ObdSpeedProvider 
from src.phase12.drive_context import DriveContext
from src.phase12.obd_speed_provider import ObdSpeedProvider, _to_kmh


class FakeQuantity:
    def __init__(self, magnitude, unit="kph"):
        self.magnitude = magnitude
        self._unit = unit

    def to(self, unit):
        if unit in ("km/h", "kph"):
            if self._unit == "mph":
                return FakeQuantity(self.magnitude * 1.60934, "kph")
            return FakeQuantity(self.magnitude, "kph")
        return self


class FakeResponse:
    def __init__(self, value):
        self.value = value

    def is_null(self):
        return self.value is None


class FakeCommand:
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return getattr(other, "name", None) == self.name

    def __hash__(self):
        return hash(self.name)


class FakeCommands:
    SPEED = FakeCommand("SPEED")
    RPM = FakeCommand("RPM")


class FakeObdModule:
    commands = FakeCommands()


class FakeAsync:
    def __init__(self, speed=0, rpm=800, connected=True):
        self.speed = speed
        self.rpm = rpm
        self._connected = connected
        self.supported_commands = {FakeCommands.SPEED, FakeCommands.RPM}
        self.started = False
        self.stopped = False
        self.closed = False

    def is_connected(self):
        return self._connected

    def protocol_name(self):
        return "fake"

    def watch(self, command, callback=None, force=False):
        return None

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True

    def close(self):
        self.closed = True

    def query(self, command):
        name = getattr(command, "name", str(command))
        if name == "SPEED":
            if self.speed is None:
                return FakeResponse(None)
            return FakeResponse(FakeQuantity(self.speed, "kph"))
        if name == "RPM":
            if self.rpm is None:
                return FakeResponse(None)
            return FakeResponse(FakeQuantity(self.rpm, "rpm"))
        return FakeResponse(None)


def test_speed_and_run_from_rpm():
    fake = FakeAsync(speed=42, rpm=900)
    provider = ObdSpeedProvider(connection=fake, rpm_run_threshold=400)
    provider._obd_module = FakeObdModule()
    assert provider.connect() is True
    reading = provider.poll()
    assert reading["connected"] is True
    assert reading["speed_kmh"] == 42
    assert reading["rpm"] == 900
    assert reading["ignition"] == DriveContext.IGNITION_RUN
    provider.close()
    assert fake.stopped is True
    assert fake.closed is False  # injected connection is not owned


def test_engine_off_is_acc():
    fake = FakeAsync(speed=0, rpm=0)
    provider = ObdSpeedProvider(connection=fake, rpm_run_threshold=400)
    provider._obd_module = FakeObdModule()
    provider.connect()
    reading = provider.poll()
    assert reading["speed_kmh"] == 0
    assert reading["ignition"] == DriveContext.IGNITION_ACC


def test_disconnected_is_off():
    fake = FakeAsync(speed=50, rpm=2000, connected=False)
    provider = ObdSpeedProvider(connection=fake)
    provider._obd_module = FakeObdModule()
    reading = provider.poll()
    assert reading["connected"] is False
    assert reading["speed_kmh"] is None
    assert reading["ignition"] == DriveContext.IGNITION_OFF


def test_apply_to_drive_context():
    fake = FakeAsync(speed=20, rpm=1500)
    provider = ObdSpeedProvider(connection=fake)
    provider._obd_module = FakeObdModule()
    provider.connect()
    ctx = DriveContext(
        enabled=True,
        mock_enabled=False,
        source_label="obd",
    )
    provider.apply_to(ctx)
    ctx.update()
    assert ctx.speed_kmh == 20
    assert ctx.ignition == DriveContext.IGNITION_RUN
    assert ctx.monitoring_active is True


def test_mph_converts_to_kmh():
    qty = FakeQuantity(62.137, "mph")
    kmh = _to_kmh(qty)
    assert 99 < kmh < 101


if __name__ == "__main__":
    test_speed_and_run_from_rpm()
    test_engine_off_is_acc()
    test_disconnected_is_off()
    test_apply_to_drive_context()
    test_mph_converts_to_kmh()
    print("All ObdSpeedProvider tests passed.")
