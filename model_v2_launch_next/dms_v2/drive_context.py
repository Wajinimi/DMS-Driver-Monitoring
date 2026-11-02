# Model Version 2 — I decide when the DMS is allowed to monitor the driver
#
# turn ON  when OBD speed reaches activate_speed_kmh (default 15 km/h)
# stay ON  through slower speeds like 10 km/h (normal when slowing down)
# turn OFF when speed stays below deactivate_speed_kmh (default 5 km/h)
#            for deactivate_hold_sec seconds (default 10)
# require ignition RUN (from OBD RPM) before speed can turn monitoring on


import logging
import time
logger = logging.getLogger(__name__)


class DriveContext:
    """track vehicle speed + ignition from OBD and expose monitoring_active"""

    IGNITION_OFF = "OFF"
    IGNITION_ACC = "ACC"
    IGNITION_RUN = "RUN"

    def __init__(
        self,
        enabled=True,
        activate_speed_kmh=15.0,
        deactivate_speed_kmh=5.0,
        deactivate_hold_sec=10.0,
        require_ignition_run=True,
        clock=None,
    ):
        self._enabled = enabled
        # only turn monitoring ON after the car reaches this speed
        self._activate_speed_kmh = float(activate_speed_kmh)
        # only turn monitoring OFF after holding below this speed
        self._deactivate_speed_kmh = float(deactivate_speed_kmh)
        # wait this many seconds below 5 km/h so red lights do not flicker it off
        self._deactivate_hold_sec = float(deactivate_hold_sec)
        # require engine RUN (RPM) before monitoring can start
        self._require_ignition_run = require_ignition_run

        # start with unknown speed until the OBD adapter gives me a reading
        self._speed_kmh = None
        self._ignition = self.IGNITION_OFF
        self._monitoring_active = False
        self._below_deactivate_since = None
        self._clock = clock or time.time

        if not self._enabled:
            # still allow a lab override: gating off means always monitor
            self._monitoring_active = True

        logger.info(
            "started DriveContext (enabled=%s, ON>=%s km/h, OFF<%s km/h for %ss)",
            enabled,
            self._activate_speed_kmh,
            self._deactivate_speed_kmh,
            self._deactivate_hold_sec,
        )

    @property
    def enabled(self):
        return self._enabled

    @property
    def speed_kmh(self):
        return self._speed_kmh

    @property
    def ignition(self):
        return self._ignition

    @property
    def monitoring_active(self):
        """True when allowed to run the model, alerts, and analytics."""
        return self._monitoring_active

    def set_speed_kmh(self, speed_kmh):
        """store speed from the OBD provider. call update() after this."""
        if speed_kmh is None:
            self._speed_kmh = None
            return
        self._speed_kmh = max(0.0, float(speed_kmh))

    def set_ignition(self, ignition):
        """store ignition inferred from OBD RPM (or SPEED if RPM is missing)."""
        if ignition not in (self.IGNITION_OFF, self.IGNITION_ACC, self.IGNITION_RUN):
            raise ValueError("Unknown ignition state: %s" % ignition)
        self._ignition = ignition

    def update(self):
        """recalculate monitoring_active from the latest OBD speed + ignition."""
        if not self._enabled:
            self._monitoring_active = True
            return

        if self._require_ignition_run and self._ignition != self.IGNITION_RUN:
            if self._monitoring_active:
                logger.info("I turned monitoring OFF — ignition is %s (I need RUN)", self._ignition)
            self._monitoring_active = False
            self._below_deactivate_since = None
            return

        if self._speed_kmh is None:
            self._monitoring_active = False
            self._below_deactivate_since = None
            return

        now = self._clock()

        if not self._monitoring_active:
            if self._speed_kmh >= self._activate_speed_kmh:
                self._monitoring_active = True
                self._below_deactivate_since = None
                logger.info(
                    "turned monitoring ON — OBD speed %.1f km/h reached %.1f km/h",
                    self._speed_kmh,
                    self._activate_speed_kmh,
                )
            return

        if self._speed_kmh < self._deactivate_speed_kmh:
            if self._below_deactivate_since is None:
                self._below_deactivate_since = now
                logger.debug(
                    "I started the off-hold timer — speed %.1f km/h is below %.1f km/h",
                    self._speed_kmh,
                    self._deactivate_speed_kmh,
                )
            elif (now - self._below_deactivate_since) >= self._deactivate_hold_sec:
                self._monitoring_active = False
                self._below_deactivate_since = None
                logger.info(
                    "I turned monitoring OFF — speed stayed below %.1f km/h for %.0fs",
                    self._deactivate_speed_kmh,
                    self._deactivate_hold_sec,
                )
        else:
            self._below_deactivate_since = None

    def status_line(self):
        """build one overlay line with OBD speed and ignition."""
        if not self._enabled:
            return "Drive gating: disabled (always monitoring)"
        speed_text = "?" if self._speed_kmh is None else "%.0f" % self._speed_kmh
        mode = "MONITORING" if self._monitoring_active else "STANDBY"
        return "%s | ignition=%s | OBD speed=%s km/h" % (mode, self._ignition, speed_text)
