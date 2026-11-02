# Phase 12 — this would decide when the DMS is allowed to monitor the drive
#

#   Turn ON  when speed reaches activate_speed_kmh (default 15 km/h)
#   Stay ON  through slower speeds like 10 km/h which is normal when slowing down)
#   Turn OFF when speed stays below deactivate_speed_kmh (default 5 km/h)
#              for deactivate_hold_sec seconds (default 10)
#   Ignition must be RUN before speed can turn monitoring on

import logging
import time

logger = logging.getLogger(__name__)


class DriveContext:
    """I track vehicle speed + ignition and expose monitoring_active."""

    # i am using plain strings so config.yaml and logs are easy to read
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
        mock_enabled=False,
        mock_default_speed_kmh=0.0,
        mock_default_ignition=IGNITION_RUN,
        clock=None,
    ):
        
        self._enabled = enabled # config values (from config.yaml drive_gating)
        self._activate_speed_kmh = float(activate_speed_kmh) #Speed must reach this before monitoring turns ON e.g. 15 km/h
        #Speed must stay below this long enough before monitoring turns OFF e.g. 5 km/h
        self._deactivate_speed_kmh = float(deactivate_speed_kmh)
        # How many seconds below deactivate speed before it turns OFF (red-light flicker fix)
        self._deactivate_hold_sec = float(deactivate_hold_sec)
        # If True, ignition must be RUN before monitoring can ever turn ON
        self._require_ignition_run = require_ignition_run
        # True on laptop when i fake speed/ignition with keyboard keys
        self._mock_enabled = mock_enabled

        # live vehicle state (updated by OBD/CAN later, or mock keys on my laptop)
        self._speed_kmh = float(mock_default_speed_kmh) if mock_enabled else None
        self._ignition = mock_default_ignition if mock_enabled else self.IGNITION_OFF

        # computed output 
        self._monitoring_active = False

        # When speed drops below deactivate_speed_kmh, then it stores when that started
        # If speed stays low long enough, monitoring turns OFF
        self._below_deactivate_since = None

        # this qill allow tests to inject a fake clock; production uses time.time
        self._clock = clock or time.time

        if not self._enabled:
            # Backward compatible: when gating is disabled, the pipeline always runs
            self._monitoring_active = True

        logger.info(
            "DriveContext started (enabled=%s, ON>=%s km/h, OFF<%s km/h for %ss, mock=%s)",
            enabled,
            self._activate_speed_kmh,
            self._deactivate_speed_kmh,
            self._deactivate_hold_sec,
            mock_enabled,
        )

    @property
    def enabled(self):
        """True when speed/ignition gating is turned on in config."""
        return self._enabled

    @property
    def mock_enabled(self):
        """True when laptop keyboard is allowed to change speed/ignition."""
        return self._mock_enabled

    @property
    def speed_kmh(self):
        """Current vehicle speed in km/h, or None if unknown."""
        return self._speed_kmh

    @property
    def ignition(self):
        """Current ignition state: OFF, ACC, or RUN."""
        return self._ignition

    @property
    def monitoring_active(self):
        """
        True when the full DMS pipeline may run (model, alerts, analytics)

        When False, test_live_full.py skips inference and does not log distractions
        """
        return self._monitoring_active

    def set_speed_kmh(self, speed_kmh):
        """
        i am setting speed from a sensor (OBD/CAN) or from mock my keyboard input

        Call update() after changing speed so monitoring_active is recalculated
        """
        if speed_kmh is None:
            self._speed_kmh = None
            return
        self._speed_kmh = max(0.0, float(speed_kmh))

    def set_ignition(self, ignition):
        """
        settin ignition from a sensor or mock keyboard input

        Call update() after changing ignition
        """
        if ignition not in (self.IGNITION_OFF, self.IGNITION_ACC, self.IGNITION_RUN):
            raise ValueError(f"Unknown ignition state: {ignition}")
        self._ignition = ignition

    def adjust_mock_speed(self, delta_kmh):
        """I nudge mock speed up/down (used by +/- keys in test_live_full.py)"""
        if not self._mock_enabled:
            return
        current = self._speed_kmh or 0.0
        self.set_speed_kmh(current + delta_kmh)

    def toggle_mock_ignition_run_off(self):
        """flippping between RUN and OFF for laptop testing (i key)"""
        if not self._mock_enabled:
            return
        if self._ignition == self.IGNITION_RUN:
            self.set_ignition(self.IGNITION_OFF)
        else:
            self.set_ignition(self.IGNITION_RUN)

    def update(self):
        """
        recalculateing monitoring_active from the latest speed + ignition

        Call this once per main loop iteration (every frame is fine)
        """
        if not self._enabled:
            self._monitoring_active = True
            return

        # Rule 1: ignition must be RUN (engine on) 
        if self._require_ignition_run and self._ignition != self.IGNITION_RUN:
            if self._monitoring_active:
                logger.info("Monitoring OFF — ignition is %s (need RUN)", self._ignition)
            self._monitoring_active = False
            self._below_deactivate_since = None
            return

        #  Rule 2: without a speed reading, stay OFF (safe default) 
        if self._speed_kmh is None:
            self._monitoring_active = False
            self._below_deactivate_since = None
            return

        now = self._clock()

        if not self._monitoring_active:
            # Currently OFF  only turn ON when speed reaches activate threshold (15 km/h)
            if self._speed_kmh >= self._activate_speed_kmh:
                self._monitoring_active = True
                self._below_deactivate_since = None
                logger.info(
                    "Monitoring ON — speed %.1f km/h reached activate threshold %.1f km/h",
                    self._speed_kmh,
                    self._activate_speed_kmh,
                )
            return

        # Currently ON stay ON at 10 km/h, 9 km/h, etc until slow stop rule fires
        if self._speed_kmh < self._deactivate_speed_kmh:
            if self._below_deactivate_since is None:
                # Speed just dropped below 5 km/h start the hold timer now
                self._below_deactivate_since = now
                logger.debug(
                    "Speed %.1f km/h below %.1f km/h — hold timer started",
                    self._speed_kmh,
                    self._deactivate_speed_kmh,
                )
            elif (now - self._below_deactivate_since) >= self._deactivate_hold_sec:
                # Speed stayed below 5 km/h long enough  turn OFF
                self._monitoring_active = False
                self._below_deactivate_since = None
                logger.info(
                    "Monitoring OFF — speed stayed below %.1f km/h for %.0fs",
                    self._deactivate_speed_kmh,
                    self._deactivate_hold_sec,
                )
        else:
            # Speed is back at or above 5 km/h , cancel the off timer e.g. green light
            self._below_deactivate_since = None

    def status_line(self):
        """One short line for the webcam overlay."""
        if not self._enabled:
            return "Drive gating: disabled (always monitoring)"

        speed_text = "?" if self._speed_kmh is None else f"{self._speed_kmh:.0f}"
        mode = "MONITORING" if self._monitoring_active else "STANDBY"
        return f"{mode} | ignition={self._ignition} | speed={speed_text} km/h"
