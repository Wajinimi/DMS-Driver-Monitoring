# Phase 6 — I play a different tone per activity so the driver can tell alerts apart.
import logging
import os
import platform
import subprocess

logger = logging.getLogger(__name__)

DEFAULT_MAC_SOUND = "/System/Library/Sounds/Glass.aiff"


def play_alert_sound(activity, activity_sounds=None, default_sound=None):
    """I pick the tone for this activity and play it without blocking the camera loop."""
    sounds = activity_sounds or {}
    path = sounds.get(activity) or default_sound or DEFAULT_MAC_SOUND

    if not os.path.exists(path):
        logger.warning("I could not find sound file: %s", path)
        path = DEFAULT_MAC_SOUND

    try:
        if platform.system() == "Darwin":
            subprocess.Popen(
                ["afplay", path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info("I played '%s' alert sound for activity '%s'", os.path.basename(path), activity)
        else:
            print("\a", end="", flush=True)
            logger.info("I played terminal bell for activity '%s'", activity)
    except Exception as err:
        logger.warning("I could not play alert sound for %s: %s", activity, err)
