# Phase 6 — I turn stable driver state into alerts (with cooldown and shadow mode)
import logging
import time

from src.phase6.alert_notifier import play_alert_sound

logger = logging.getLogger(__name__)

# i want to decide when a sustained distraction is worth alerting on so i am crating a class to do that
class AlertTrigger:

    def __init__(
        self,
        duration_thresholds=None, #i am setting the duration thresholds for each activiiy
        cooldown_seconds=10, #i am setting the cooldown seconds for each activity
        shadow_mode=True, #i am setting the shadow mode for my laptop settings for now
        normal_class="normal_driving", #i am calling it normal activity when nothing is confident enough
        min_speed_kmh=0, #i am setting the minimumu speed for alerting
        speed_gating_enabled=False,
        messages=None,
        audio_enabled=True,
        activity_sounds=None,
        default_sound=None,
    ):
        self._duration_thresholds = duration_thresholds or {}
        self._cooldown_seconds = cooldown_seconds
        self._shadow_mode = shadow_mode
        self._normal_class = normal_class
        self._min_speed_kmh = min_speed_kmh
        self._speed_gating_enabled = speed_gating_enabled
        self._messages = messages or {}
        self._audio_enabled = audio_enabled
        self._activity_sounds = activity_sounds or {}
        self._default_sound = default_sound
        self._last_alert_time = {}  # I track when I last alerted per activity
        mode = "SHADOW" if shadow_mode else "LIVE"
        logger.info(
            "I started the Alert Trigger (%s, cooldown=%ss, audio=%s)",
            mode,
            cooldown_seconds,
            audio_enabled and not shadow_mode,
        )

    def _default_message(self, activity, duration):
        return f"Driver activity '{activity}' sustained for {duration:.1f}s"

    def _is_cooled_down(self, activity):
        last_time = self._last_alert_time.get(activity, 0.0)
        return (time.time() - last_time) >= self._cooldown_seconds

    def _passes_speed_gate(self, speed_kmh):
        if not self._speed_gating_enabled:
            return True
        if speed_kmh is None:
            return False
        return speed_kmh >= self._min_speed_kmh


    #i want to check if the activity has lasted long enough, passed the speed gate, and is not on cooldown, so it can fire alert again
    def check(self, activity, duration, confidence, speed_kmh=None):
        if activity == self._normal_class:
            return None

        if activity not in self._duration_thresholds:
            return None

        threshold = self._duration_thresholds[activity]
        if duration < threshold:
            return None

        if not self._passes_speed_gate(speed_kmh):
            return None

        if not self._is_cooled_down(activity):
            return None

        message = self._messages.get(activity, self._default_message(activity, duration))
        alert = {
            "activity": activity,
            "duration": duration,
            "confidence": confidence,
            "threshold": threshold,
            "shadow_mode": self._shadow_mode,
            "message": message,
            "timestamp": time.time(),
        }

        self._last_alert_time[activity] = alert["timestamp"]
        self._dispatch(alert)
        return alert

    def _dispatch(self, alert):
        if self._shadow_mode:
            logger.warning(
                "SHADOW ALERT | %s | %.1fs (threshold %.1fs) | conf %.0f%%",
                alert["activity"],
                alert["duration"],
                alert["threshold"],
                alert["confidence"] * 100,
            )
            return

        logger.warning(
            "ALERT FIRED | %s | %s",
            alert["activity"],
            alert["message"],
        )
        if self._audio_enabled:
            play_alert_sound(
                alert["activity"],
                self._activity_sounds,
                self._default_sound,
            )
