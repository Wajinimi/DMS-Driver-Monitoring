# Live full-stack test — I run webcam → model → alerts → SQLite → score → coaching
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
from src.phase9.safety_score_engine import SafetyScoreEngine
from src.phase10.recommendation_engine import RecommendationEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def draw_overlay(frame, activity, duration, alert):
    """I draw the stable state and any active alert on the webcam preview."""
    display = frame.copy()
    cv2.putText(
        display,
        f"State: {activity} ({duration:.1f}s)",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2,
    )
    cv2.putText(
        display,
        "Press 'q' to quit and save trip",
        (10, display.shape[0] - 12),
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


def print_post_session_report(config, trip_summary):
    """I compute and print the weekly score + coaching after the live trip ends."""
    db_path = config["analytics"]["db_path"]
    score_cfg = config["safety_score"]
    coach_cfg = config["coaching"]

    score_engine = SafetyScoreEngine(
        weights=score_cfg["weights"],
        scale_factor=score_cfg["scale_factor"],
        bands=score_cfg["bands"],
        exposure_unit=score_cfg["exposure_unit"],
        db_path=db_path,
    )
    coach_engine = RecommendationEngine(
        behavior_tips=coach_cfg["behavior_tips"],
        baseline_weeks=coach_cfg["baseline_weeks"],
        increase_threshold=coach_cfg["increase_threshold"],
        improve_threshold=coach_cfg["improve_threshold"],
        db_path=db_path,
    )

    weekly = score_engine.compute_weekly_score()
    coaching = coach_engine.generate_weekly_coaching(weekly)

    print("\n" + "=" * 60)
    print("TRIP SAVED")
    print("  trip_id:", trip_summary.get("trip_id"))
    print("  duration_sec:", round(trip_summary.get("duration_sec", 0), 1))
    print("  distraction_sec:", round(trip_summary.get("total_distraction_sec", 0), 1))
    print("  alerts:", trip_summary.get("alert_count", 0))

    print("\nWEEKLY SCORE (current 7-day window)")
    print("  week:", weekly["week_start"], "→", weekly["week_end"])
    if weekly["has_data"]:
        print("  score:", weekly["safety_score"], "/100 —", weekly["band"])
        print("  top contributors:", weekly.get("top_contributors", []))
    else:
        print("  no score yet (need trip time logged this week)")

    print("\nCOACHING")
    for rec in coaching.get("recommendations", []):
        print(" ", rec["rule"], "→", rec["message"])

    print("\nNext: python3 run_dashboard.py → refresh browser to see charts + coaching")
    print("=" * 60 + "\n")


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

    if not streamer.start():
        logger.error("I could not start the camera — check webcam permission and source 0.")
        async_engine.stop()
        analytics.close()
        return

    trip_id = analytics.start_trip()
    mode = "shadow" if at_cfg["shadow_mode"] else "LIVE"
    logger.info(
        "Live full test — trip %s, %s alerts. Window: 'DMS Live Full Test'. Press 'q' to quit.",
        trip_id,
        mode,
    )

    clips_submitted = 0
    last_logged_ms = None
    latest_activity = sm_cfg["normal_class"]
    latest_duration = 0.0
    latest_alert = None
    alert_banner_until = 0.0
    trip_summary = {}

    try:
        while streamer._running:
            preview = streamer.get_frame()
            if preview is not None:
                if time.time() < alert_banner_until and latest_alert is not None:
                    shown = draw_overlay(preview, latest_activity, latest_duration, latest_alert)
                else:
                    shown = draw_overlay(preview, latest_activity, latest_duration, None)
                cv2.imshow("DMS Live Full Test", shown)

            frame = streamer.consume_frame()
            if frame is not None:
                buffer.add_frame(frame)
                if buffer.should_emit_clip():
                    clip = buffer.get_clip()
                    async_engine.submit_clip(clip)
                    clips_submitted += 1

            result = async_engine.get_latest_result()
            if result is not None:
                ms = result["inference_time_ms"]
                if ms != last_logged_ms:
                    last_logged_ms = ms
                    probs = result["probabilities"]

                    start_time, activity, conf, duration = state_manager.update(probs)
                    latest_activity = activity
                    latest_duration = duration
                    analytics.update_state(activity, conf, start_time)

                    alert = alert_trigger.check(activity, duration, conf)
                    if alert is not None:
                        latest_alert = alert
                        alert_banner_until = time.time() + 3.0
                        analytics.log_alert(alert)
                        logger.info("ALERT: %s", alert["message"])

                    raw_class = max(probs, key=probs.get)
                    raw_prob = probs[raw_class]
                    logger.info(
                        "Raw: %s (%.0f%%) → Stable: %s | %.1fs | %.0fms",
                        raw_class,
                        raw_prob * 100,
                        activity,
                        duration,
                        ms,
                    )

            if cv2.waitKey(1) & 0xFF == ord("q"):
                logger.info("I pressed 'q' — saving trip and shutting down.")
                break

    finally:
        streamer.stop()
        async_engine.stop()
        cv2.destroyAllWindows()

        trip_summary = analytics.end_trip() or {}
        analytics.close()
        logger.info("I submitted %d clips.", clips_submitted)

        if trip_summary:
            print_post_session_report(config, trip_summary)


if __name__ == "__main__":
    main()
