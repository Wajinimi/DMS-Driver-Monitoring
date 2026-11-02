#!/usr/bin/env python3
"""
Model Version 2 live runner 
"""
import logging
import os
import sys
import time

import cv2
import yaml


HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from dms_v2.alert_trigger import AlertTrigger
from dms_v2.analytics_logger import AnalyticsLogger
from dms_v2.async_inference import AsyncInference
from dms_v2.drive_context import DriveContext
from dms_v2.inference_engine import build_inference_engine
from dms_v2.obd_speed_provider import ObdSpeedProvider
from dms_v2.sliding_buffer import SlidingBuffer
from dms_v2.state_manager import StateManager
from dms_v2.trip_summary_builder import build_trip_report, format_terminal_report
from dms_v2.trip_summary_overlay import show_trip_summary_overlay
from dms_v2.video_streamer import VideoStreamer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

WINDOW_NAME = "DMS Model V2 — OBD"


def draw_overlay(frame, activity, duration, alert, drive_context, rpm=None):
    """draw OBD status, driver state, and any active alert on the preview."""
    display = frame.copy()
    status_color = (0, 255, 0) if drive_context.monitoring_active else (0, 165, 255)
    cv2.putText(
        display,
        drive_context.status_line(),
        (10, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        status_color,
        2,
    )

    rpm_text = "RPM: ?" if rpm is None else "RPM: %.0f" % rpm
    cv2.putText(
        display,
        rpm_text,
        (10, 52),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (200, 200, 200),
        1,
    )

    if drive_context.monitoring_active:
        cv2.putText(
            display,
            "State: %s (%.1fs)" % (activity, duration),
            (10, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 255, 0),
            2,
        )
    else:
        cv2.putText(
            display,
            "STANDBY — I wait for OBD speed >= 15 km/h and engine RUN",
            (10, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 165, 255),
            2,
        )

    cv2.putText(
        display,
        "ESC or q = quit (speed comes from OBD, not keyboard)",
        (10, display.shape[0] - 12),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (200, 200, 200),
        1,
    )

    if alert is not None:
        cv2.rectangle(display, (0, 0), (display.shape[1], 60), (0, 0, 200), -1)
        cv2.putText(
            display,
            "ALERT: %s" % alert["message"],
            (10, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2,
        )
    return display


def present_trip_summary(config, trip_summary, frame):
    if not trip_summary:
        return
    ts_cfg = config.get("trip_summary", {})
    bundle = build_trip_report(config, trip_summary, max_tips=ts_cfg.get("max_tips", 2))
    print("\n" + format_terminal_report(bundle) + "\n")
    show_trip_summary_overlay(
        frame,
        bundle,
        WINDOW_NAME,
        display_sec=ts_cfg.get("display_sec", 12),
    )


def on_monitoring_stopped(state_manager, analytics):
    analytics.pause_tracking()
    state_manager.reset()


def main():
    config_path = os.path.join(HERE, "config.yaml")
    with open(config_path) as f:
        config = yaml.safe_load(f)

    cam = config["camera"]
    buf = config["buffer"]
    mdl = config["model"]
    sm_cfg = config["state_manager"]
    at_cfg = config["alert_trigger"]
    an_cfg = config["analytics"]
    dg_cfg = config["drive_gating"]
    obd_cfg = dg_cfg.get("obd", {})

    # resolve relative paths from this folder, not from wherever my shell started
    os.chdir(HERE)
    if not os.path.isabs(an_cfg["db_path"]):
        an_cfg["db_path"] = os.path.join(HERE, an_cfg["db_path"])

    streamer = VideoStreamer(
        target_fps=cam["target_fps"],
        frame_width=cam["frame_width"],
        frame_height=cam["frame_height"],
        watchdog_timeout_ms=cam["watchdog_timeout_ms"],
    )

    buffer = SlidingBuffer(
        clip_length=buf["clip_length"],
        stride=buf["stride"],
        model_size=mdl["model_size"],
        normalize=mdl["normalize"],
        imagenet_mean=mdl["imagenet_mean"],
        imagenet_std=mdl["imagenet_std"],
    )

    engine = build_inference_engine(config)
    async_engine = AsyncInference(engine)
    async_engine.start()

    state_manager = StateManager(
        default_threshold=sm_cfg["default_threshold"],
        exit_threshold=sm_cfg["exit_threshold"],
        normal_class=sm_cfg["normal_class"],
        smoothing_windows=sm_cfg["smoothing_windows"],
    )

    alert_trigger = AlertTrigger(
        duration_thresholds=at_cfg["duration_thresholds"],
        cooldown_seconds=at_cfg["cooldown_seconds"],
        shadow_mode=at_cfg["shadow_mode"],
        normal_class=sm_cfg["normal_class"],
        min_speed_kmh=at_cfg["min_speed_kmh"],
        speed_gating_enabled=at_cfg["speed_gating_enabled"],
        messages=at_cfg["messages"],
        audio_enabled=at_cfg.get("audio_enabled", True),
        activity_sounds=at_cfg.get("activity_sounds"),
        default_sound=at_cfg.get("default_sound"),
    )

    analytics = AnalyticsLogger(
        db_path=an_cfg["db_path"],
        distraction_activities=an_cfg["distraction_activities"],
        normal_class=sm_cfg["normal_class"],
    )

    drive_context = DriveContext(
        enabled=dg_cfg.get("enabled", True),
        activate_speed_kmh=dg_cfg.get("activate_speed_kmh", 15),
        deactivate_speed_kmh=dg_cfg.get("deactivate_speed_kmh", 5),
        deactivate_hold_sec=dg_cfg.get("deactivate_hold_sec", 10),
        require_ignition_run=dg_cfg.get("require_ignition_run", True),
    )

    obd_provider = ObdSpeedProvider(
        port=obd_cfg.get("port") or None,
        baudrate=obd_cfg.get("baudrate"),
        timeout=obd_cfg.get("timeout", 0.2),
        delay_cmds=obd_cfg.get("poll_interval_sec", 0.25),
        rpm_run_threshold=obd_cfg.get("rpm_run_threshold", 400),
    )

    if not obd_provider.connect():
        logger.error(
            "I could not connect to OBD (%s). I will not fall back to laptop +/- keys.",
            obd_provider._last_error,
        )
        async_engine.stop()
        analytics.close()
        return

    if not streamer.start():
        logger.error("I could not start the camera.")
        obd_provider.close()
        async_engine.stop()
        analytics.close()
        return

    logger.info("I started Model V2 live OBD speed only. ESC or q to quit.")

    clips_submitted = 0
    last_logged_ms = None
    latest_activity = sm_cfg["normal_class"]
    latest_duration = 0.0
    latest_alert = None
    alert_banner_until = 0.0
    trip_summary = {}
    was_monitoring = False
    last_preview_frame = None
    last_rpm = None

    try:
        while streamer._running:
            reading = obd_provider.apply_to(drive_context)
            last_rpm = reading.get("rpm")
            drive_context.update()

            if drive_context.monitoring_active and analytics.active_trip_id is None:
                trip_id = analytics.start_trip()
                logger.info("I started a trip because OBD monitoring turned ON: %s", trip_id)

            if was_monitoring and not drive_context.monitoring_active:
                on_monitoring_stopped(state_manager, analytics)

            if (
                drive_context.ignition == DriveContext.IGNITION_OFF
                and analytics.active_trip_id is not None
            ):
                logger.info("I saw ignition OFF on OBD I am ending the trip.")
                ended = analytics.end_trip() or {}
                if ended:
                    present_trip_summary(config, ended, last_preview_frame)

            was_monitoring = drive_context.monitoring_active

            preview = streamer.get_frame()
            if preview is not None:
                last_preview_frame = preview.copy()
                if time.time() < alert_banner_until and latest_alert is not None:
                    shown = draw_overlay(
                        preview, latest_activity, latest_duration, latest_alert, drive_context, last_rpm
                    )
                else:
                    shown = draw_overlay(
                        preview, latest_activity, latest_duration, None, drive_context, last_rpm
                    )
                cv2.imshow(WINDOW_NAME, shown)

            frame = streamer.consume_frame()
            if frame is not None and drive_context.monitoring_active:
                buffer.add_frame(frame)
                if buffer.should_emit_clip():
                    clip = buffer.get_clip()
                    async_engine.submit_clip(clip)
                    clips_submitted += 1

            result = async_engine.get_latest_result()
            if result is not None and drive_context.monitoring_active:
                ms = result["inference_time_ms"]
                if ms != last_logged_ms:
                    last_logged_ms = ms
                    probs = result["probabilities"]
                    start_time, activity, conf, duration = state_manager.update(probs)
                    latest_activity = activity
                    latest_duration = duration
                    analytics.update_state(activity, conf, start_time)

                    alert = alert_trigger.check(
                        activity,
                        duration,
                        conf,
                        speed_kmh=drive_context.speed_kmh,
                    )
                    if alert is not None:
                        latest_alert = alert
                        alert_banner_until = time.time() + 3.0
                        analytics.log_alert(alert)
                        logger.info("ALERT: %s", alert["message"])

                    raw_class = max(probs, key=probs.get)
                    logger.info(
                        "Raw: %s (%.0f%%) → Stable: %s | %.1fs | %s",
                        raw_class,
                        probs[raw_class] * 100,
                        activity,
                        duration,
                        drive_context.status_line(),
                    )

            key = cv2.waitKey(1) & 0xFF
            # I only use the keyboard to quit. I do not map +/- to speed.
            if key in (ord("q"), 27):
                logger.info("I pressed quit — I am saving the trip and shutting down.")
                break

    finally:
        if analytics.active_trip_id is not None:
            trip_summary = analytics.end_trip() or {}
        if trip_summary:
            present_trip_summary(config, trip_summary, last_preview_frame)

        streamer.stop()
        async_engine.stop()
        obd_provider.close()
        cv2.destroyAllWindows()
        analytics.close()
        logger.info("I submitted %d clips.", clips_submitted)


if __name__ == "__main__":
    main()
