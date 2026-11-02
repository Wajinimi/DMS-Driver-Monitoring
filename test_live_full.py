# Live full-stack test — I run webcam → model → alerts → SQLite → score → coaching
# Phase 12 adds speed + ignition gating before the model runs.
import logging
import time

import cv2
import yaml

from src.phase1.video_streamer import VideoStreamer
from src.phase2.sliding_buffer import SlidingBuffer
from src.phase4.async_inference import AsyncInference
from src.phase4.inference_engine import InferenceEngine
from src.phase5.state_manager import StateManager
from src.phase6.alert_trigger import AlertTrigger
from src.phase7.analytics_logger import AnalyticsLogger
from src.phase12.drive_context import DriveContext
from src.phase12.trip_summary_builder import build_trip_report, format_terminal_report
from src.phase12.trip_summary_overlay import show_trip_summary_overlay

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

WINDOW_NAME = "DMS Live Full Test"


def draw_overlay(frame, activity, duration, alert, drive_context):
    """I draw driver state, drive gating status, and any active alert on the preview."""
    display = frame.copy()

    # Phase 12 status line (STANDBY vs MONITORING, speed, ignition)
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

    if drive_context.monitoring_active:
        cv2.putText(
            display,
            f"State: {activity} ({duration:.1f}s)",
            (10, 56),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )
    else:
        cv2.putText(
            display,
            "DMS standby — reach 15 km/h to start monitoring",
            (10, 56),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 165, 255),
            2,
        )

    help_y = display.shape[0] - 12
    if drive_context.mock_enabled:
        cv2.putText(
            display,
            "q=quit | +/-=speed | i=ignition RUN/OFF",
            (10, help_y - 18),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (200, 200, 200),
            1,
        )
    cv2.putText(
        display,
        "Press 'q' to quit and save trip",
        (10, help_y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (200, 200, 200),
        1,
    )

    if alert is not None:
        cv2.rectangle(display, (0, 0), (display.shape[1], 60), (0, 0, 200), -1)
        cv2.putText(
            display,
            f"ALERT: {alert['message']}",
            (10, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )
    return display


def present_trip_summary(config, trip_summary, frame):
    """I print and show the same trip summary in terminal + on-screen overlay."""
    if not trip_summary:
        return

    ts_cfg = config.get("trip_summary", {})
    bundle = build_trip_report(
        config,
        trip_summary,
        max_tips=ts_cfg.get("max_tips", 2),
    )
    print("\n" + format_terminal_report(bundle) + "\n")
    show_trip_summary_overlay(
        frame,
        bundle,
        WINDOW_NAME,
        display_sec=ts_cfg.get("display_sec", 12),
    )


def handle_mock_keys(key, drive_context):
    """
    I map keyboard keys to fake speed/ignition on the laptop.

    Real car: replace this with OBD/CAN readings in DriveContext.set_speed_kmh().
    """
    if not drive_context.mock_enabled:
        return False

    if key in (ord("+"), ord("=")):
        drive_context.adjust_mock_speed(5)
        logger.info("Mock speed -> %.0f km/h", drive_context.speed_kmh or 0)
        return True

    if key == ord("-"):
        drive_context.adjust_mock_speed(-5)
        logger.info("Mock speed -> %.0f km/h", drive_context.speed_kmh or 0)
        return True

    if key == ord("i"):
        drive_context.toggle_mock_ignition_run_off()
        logger.info("Mock ignition -> %s", drive_context.ignition)
        return True

    return False


def on_monitoring_stopped(state_manager, analytics):
    """I clean up when we leave MONITORING mode so parked time is not scored."""
    analytics.pause_tracking()
    state_manager.reset()


def main():
    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    cam = config["camera"]
    buf = config["buffer"]
    mdl = config["model"]
    pt = config["pytorch"]
    sm_cfg = config["state_manager"]
    at_cfg = config["alert_trigger"]
    an_cfg = config["analytics"]
    dg_cfg = config["drive_gating"]
    mock_cfg = dg_cfg.get("mock", {})

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

    engine = InferenceEngine(
        weights_path=pt["weights_path"],
        num_classes=mdl["num_classes"],
        device=pt["device"],
        class_names=mdl["class_names"],
    )

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
    )

    drive_context = DriveContext(
        enabled=dg_cfg.get("enabled", True),
        activate_speed_kmh=dg_cfg.get("activate_speed_kmh", 15),
        deactivate_speed_kmh=dg_cfg.get("deactivate_speed_kmh", 5),
        deactivate_hold_sec=dg_cfg.get("deactivate_hold_sec", 10),
        require_ignition_run=dg_cfg.get("require_ignition_run", True),
        mock_enabled=mock_cfg.get("enabled", False),
        mock_default_speed_kmh=mock_cfg.get("default_speed_kmh", 0),
        mock_default_ignition=mock_cfg.get("default_ignition", DriveContext.IGNITION_RUN),
    )

    if not streamer.start():
        logger.error("I could not start the camera — check webcam permission and source 0.")
        async_engine.stop()
        analytics.close()
        return

    mode = "shadow" if at_cfg["shadow_mode"] else "LIVE"
    logger.info(
        "Live full test — %s alerts. Mock keys: +/- speed, i ignition. Press 'q' to quit.",
        mode,
    )

    clips_submitted = 0
    last_logged_ms = None
    latest_activity = sm_cfg["normal_class"]
    latest_duration = 0.0
    latest_alert = None
    alert_banner_until = 0.0
    trip_summary = {}
    was_monitoring = False
    last_preview_frame = None

    try:
        while streamer._running:
            # --- Phase 12: read vehicle state every loop ---
            drive_context.update()

            # Trip starts only after monitoring turns ON (speed >= 15 km/h)
            if drive_context.monitoring_active and analytics.active_trip_id is None:
                trip_id = analytics.start_trip()
                logger.info("Trip started because monitoring turned ON: %s", trip_id)

            # When monitoring turns OFF, flush parked time out of scores
            if was_monitoring and not drive_context.monitoring_active:
                on_monitoring_stopped(state_manager, analytics)

            # Ignition OFF ends the trip and shows the summary card
            if (
                drive_context.enabled
                and drive_context.ignition == DriveContext.IGNITION_OFF
                and analytics.active_trip_id is not None
            ):
                logger.info("Ignition OFF — ending trip.")
                ended = analytics.end_trip() or {}
                if ended:
                    present_trip_summary(config, ended, last_preview_frame)

            was_monitoring = drive_context.monitoring_active

            preview = streamer.get_frame()
            if preview is not None:
                last_preview_frame = preview.copy()
                if time.time() < alert_banner_until and latest_alert is not None:
                    shown = draw_overlay(
                        preview, latest_activity, latest_duration, latest_alert, drive_context
                    )
                else:
                    shown = draw_overlay(
                        preview, latest_activity, latest_duration, None, drive_context
                    )
                cv2.imshow(WINDOW_NAME, shown)

            frame = streamer.consume_frame()
            if frame is not None and drive_context.monitoring_active:
                # --- Only run the model when monitoring is ON ---
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

                    # AlertTrigger gets speed too (second gate inside monitoring)
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
                    raw_prob = probs[raw_class]
                    logger.info(
                        "Raw: %s (%.0f%%) → Stable: %s | %.1fs | %.0fms | %s",
                        raw_class,
                        raw_prob * 100,
                        activity,
                        duration,
                        ms,
                        drive_context.status_line(),
                    )

            key = cv2.waitKey(1) & 0xFF
            if key != 255:
                handle_mock_keys(key, drive_context)
            if key == ord("q"):
                logger.info("I pressed 'q' — saving trip and shutting down.")
                break

    finally:
        if analytics.active_trip_id is not None:
            trip_summary = analytics.end_trip() or {}

        if trip_summary:
            present_trip_summary(config, trip_summary, last_preview_frame)

        streamer.stop()
        async_engine.stop()
        cv2.destroyAllWindows()
        analytics.close()
        logger.info("I submitted %d clips.", clips_submitted)


if __name__ == "__main__":
    main()
