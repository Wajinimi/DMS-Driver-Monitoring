# Model Version 2 — I read vehicle speed and an ignition proxy from a real OBD-II adapter
# PID 0x0D  SPEED  → km/h
# PID 0x0C  RPM    →  use this as ignition (engine running ≈ RUN)
# OBD-II has no standard ignition-switch PID. I treat:
#   adapter/ECU gone          → ignition OFF
#   RPM below run threshold   → ACC (key on, engine not running)
#   RPM at/above threshold    → RUN
#   RPM missing, SPEED present → RUN


import glob
import logging
import time

from dms_v2.drive_context import DriveContext

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
    """pull a raw number from a python-obd RPM response"""
    if value is None:
        return None
    if hasattr(value, "magnitude"):
        return float(value.magnitude)
    return float(value)


def list_mac_serial_ports():
    ports = []
    for pattern in ("/dev/cu.usbserial*", "/dev/cu.usbmodem*", "/dev/cu.OBD*", "/dev/cu.SLAB*"):
        ports.extend(sorted(glob.glob(pattern)))
    return ports


class ObdSpeedProvider:
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
    
        self._port = port or None
        self._baudrate = baudrate
        self._timeout = timeout
        self._delay_cmds = delay_cmds
        self._rpm_run_threshold = float(rpm_run_threshold)
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

        I return True on success. I do not raise if the dongle is unplugged —
        the live runner should refuse to start rather than fake speed with keys.
        """
        if self._connection is None:
            try:
                import obd
            except ImportError:
                self._last_error = "python-obd is not installed (pip install obd)"
                logger.error("I cannot start OBD: %s", self._last_error)
                return False
            self._obd_module = obd

            port = self._port
            if not port:
                mac_ports = list_mac_serial_ports()
                if mac_ports:
                    # I pick the first USB serial device I find so Mac auto-detect is less flaky
                    port = mac_ports[0]
                    self._port = port
                    logger.info("I auto-selected OBD serial port %s", port)

            kwargs = {
                "timeout": self._timeout,
                "delay_cmds": self._delay_cmds,
            }
            if port:
                kwargs["portstr"] = port
            if self._baudrate:
                kwargs["baudrate"] = self._baudrate
            try:
                self._connection = obd.Async(**kwargs)
            except Exception as exc:
                self._last_error = str(exc)
                logger.error("I could not open the OBD adapter: %s", exc)
                self._connection = None
                return False

        if not self.connected:
            self._last_error = (
                "OBD adapter did not connect. I need USB plugged in and ignition ON."
            )
            logger.error(self._last_error)
            return False

        obd_mod = self._obd_module
        if obd_mod is None:
            import obd as obd_mod
            self._obd_module = obd_mod

        try:
            self._watch_command(obd_mod.commands.SPEED)
            self._watch_command(obd_mod.commands.RPM)
            starter = getattr(self._connection, "start", None)
            if starter is not None:
                starter()
            self._started = True
            logger.info(
                "I connected to OBD (port=%s, protocol=%s)",
                self._port or "auto",
                getattr(self._connection, "protocol_name", lambda: "?")(),
            )
            return True
        except Exception as exc:
            self._last_error = str(exc)
            logger.error("I could not start the OBD watch loop: %s", exc)
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

        I return a dict: speed_kmh, rpm, ignition, connected.
        I am safe to call every camera frame because Async query is cached.
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
                self._obd_module = obd_mod
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
        """I push the latest OBD reading into DriveContext before update()."""
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
        # I use RPM as engine-on when the car supports it
        if rpm is not None:
            if rpm >= self._rpm_run_threshold:
                return DriveContext.IGNITION_RUN
            return DriveContext.IGNITION_ACC
        # Some cars answer SPEED but not RPM I still treat that as RUN
        if speed_kmh is not None:
            return DriveContext.IGNITION_RUN
        return DriveContext.IGNITION_OFF
