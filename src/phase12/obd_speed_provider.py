# Phase 12 — I read vehicle speed (and a simple ignition proxy) from an OBD-II adapter
#
# PID 0x0D  SPEED  → km/h
# PID 0x0C  RPM    → used as ignition proxy (engine running ≈ RUN)
#
# OBD-II has no standard "ignition switch" PID. I treat:
#   adapter/ECU gone          → ignition OFF
#   RPM below run threshold   → ACC (key on, engine not running)
#   RPM at/above threshold    → RUN
#   RPM unavailable           → RUN if ECU answers, else OFF
#
# I use python-obd's Async connection so the live camera loop is not blocked
# waiting on the car. query() then returns the latest cached SPEED/RPM.

import logging
import time

from src.phase12.drive_context import DriveContext

logger = logging.getLogger(__name__)


def _to_kmh(value):
    """I convert a python-obd SPEED value (Pint Quantity or number) to km/h."""
    if value is None:
        return None
    if hasattr(value, "to"):
        try:
            return float(value.to("km/h").magnitude)
        except Exception:
            pass
    if hasattr(value, "magnitude"):
        return float(value.magnitude)
    return float(value)


def _to_number(value):
    """I pull a raw number from a python-obd RPM (or similar) response value."""
    if value is None:
        return None
    if hasattr(value, "magnitude"):
        return float(value.magnitude)
    return float(value)


class ObdSpeedProvider:
    """I connect to a USB/Bluetooth OBD adapter and poll SPEED + RPM."""

    def __init__(
        self,
        port=None,
        baudrate=None,
        timeout=0.2,
        delay_cmds=0.25,
        rpm_run_threshold=400.0,
        connection=None,
        clock=None,
    ):
        # port=None lets python-obd auto-scan USB then Bluetooth serial ports
        self._port = port or None
        self._baudrate = baudrate
        self._timeout = timeout
        # delay between async watch loops (seconds) — do not hammer the ECU
        self._delay_cmds = delay_cmds
        self._rpm_run_threshold = float(rpm_run_threshold)
        # tests inject a fake connection; production leaves this None
        self._connection = connection
        self._owns_connection = connection is None
        self._clock = clock or time.time
        self._started = False
        self._last_speed_kmh = None
        self._last_rpm = None
        self._last_ignition = DriveContext.IGNITION_OFF
        self._last_error = None
        self._obd_module = None

    @property
    def connected(self):
        """True when python-obd reports an open adapter/ECU link."""
        if self._connection is None:
            return False
        checker = getattr(self._connection, "is_connected", None)
        if checker is None:
            return False
        try:
            return bool(checker())
        except Exception:
            return False

    def connect(self):
        """
        I open the adapter and start the background SPEED/RPM watch loop.

        Returns True on success. Does not raise on missing hardware — caller
        can fall back to mock.
        """
        if self._connection is None:
            try:
                import obd
            except ImportError:
                self._last_error = "python-obd is not installed (pip install obd)"
                logger.error(self._last_error)
                return False
            self._obd_module = obd
            kwargs = {
                "timeout": self._timeout,
                "delay_cmds": self._delay_cmds,
            }
            if self._port:
                kwargs["portstr"] = self._port
            if self._baudrate:
                kwargs["baudrate"] = self._baudrate
            try:
                self._connection = obd.Async(**kwargs)
            except Exception as exc:
                self._last_error = str(exc)
                logger.error("I could not open OBD adapter: %s", exc)
                self._connection = None
                return False

        if not self.connected:
            self._last_error = "OBD adapter did not connect (plug in USB, ignition ON)"
            logger.error(self._last_error)
            return False

        obd_mod = self._obd_module
        if obd_mod is None:
            import obd as obd_mod

        try:
            self._watch_command(obd_mod.commands.SPEED)
            self._watch_command(obd_mod.commands.RPM)
            starter = getattr(self._connection, "start", None)
            if starter is not None:
                starter()
            self._started = True
            logger.info(
                "OBD connected (port=%s, protocol=%s)",
                self._port or "auto",
                getattr(self._connection, "protocol_name", lambda: "?")(),
            )
            return True
        except Exception as exc:
            self._last_error = str(exc)
            logger.error("I could not start OBD watch loop: %s", exc)
            return False

    def _watch_command(self, command):
        watch = getattr(self._connection, "watch", None)
        if watch is None:
            return
        supported = getattr(self._connection, "supported_commands", None)
        force = True
        if supported is not None and command in supported:
            force = False
        watch(command, force=force)

    def poll(self):
        """
        I read the latest cached SPEED and RPM.

        Returns a dict: speed_kmh, rpm, ignition, connected.
        Safe to call every camera frame (Async query does not wait on the car).
        """
        reading = {
            "speed_kmh": None,
            "rpm": None,
            "ignition": DriveContext.IGNITION_OFF,
            "connected": self.connected,
        }
        if not reading["connected"]:
            self._last_speed_kmh = None
            self._last_rpm = None
            self._last_ignition = DriveContext.IGNITION_OFF
            return reading

        obd_mod = self._obd_module
        if obd_mod is None:
            try:
                import obd as obd_mod
            except ImportError:
                return reading

        speed_kmh = self._query_kmh(obd_mod.commands.SPEED)
        rpm = self._query_number(obd_mod.commands.RPM)
        ignition = self._infer_ignition(rpm, speed_kmh)

        self._last_speed_kmh = speed_kmh
        self._last_rpm = rpm
        self._last_ignition = ignition

        reading["speed_kmh"] = speed_kmh
        reading["rpm"] = rpm
        reading["ignition"] = ignition
        return reading

    def apply_to(self, drive_context):
        """I push the latest OBD reading into DriveContext (call before update())."""
        reading = self.poll()
        drive_context.set_speed_kmh(reading["speed_kmh"])
        drive_context.set_ignition(reading["ignition"])
        return reading

    def close(self):
        """I stop the watch thread and close the serial port."""
        if self._connection is None:
            return
        try:
            stopper = getattr(self._connection, "stop", None)
            if stopper is not None and self._started:
                stopper()
        except Exception as exc:
            logger.warning("OBD stop() failed: %s", exc)
        try:
            closer = getattr(self._connection, "close", None)
            if closer is not None and self._owns_connection:
                closer()
        except Exception as exc:
            logger.warning("OBD close() failed: %s", exc)
        self._started = False
        if self._owns_connection:
            self._connection = None

    def _query_kmh(self, command):
        response = self._safe_query(command)
        if response is None:
            return None
        is_null = getattr(response, "is_null", None)
        if callable(is_null) and is_null():
            return None
        return _to_kmh(getattr(response, "value", None))

    def _query_number(self, command):
        response = self._safe_query(command)
        if response is None:
            return None
        is_null = getattr(response, "is_null", None)
        if callable(is_null) and is_null():
            return None
        return _to_number(getattr(response, "value", None))

    def _safe_query(self, command):
        try:
            return self._connection.query(command)
        except Exception as exc:
            logger.debug("OBD query failed: %s", exc)
            return None

    def _infer_ignition(self, rpm, speed_kmh):
        # ECU answered with RPM — use engine running as RUN
        if rpm is not None:
            if rpm >= self._rpm_run_threshold:
                return DriveContext.IGNITION_RUN
            return DriveContext.IGNITION_ACC
        # No RPM PID on this car, but SPEED is answering — treat as RUN
        if speed_kmh is not None:
            return DriveContext.IGNITION_RUN
        # Connected with no usable PIDs — stay OFF so we do not start a fake trip
        return DriveContext.IGNITION_OFF
