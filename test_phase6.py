

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


# i want to test the full AI pipeline from Phase to pHASE 6

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def draw_overlay(frame, activity, duration, alert):
    """I'm drawing the stable state and any active alert on the preview."""
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


def main():
    # I'm loading all settings from config.yaml
    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    cam = config["camera"]
    buf = config["buffer"]
    mdl = config["model"]
    pt = config["pytorch"]
    sm_cfg = config["state_manager"]
    at_cfg = config["alert_trigger"]

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

    if not streamer.start():
        logger.error("I could not start the camera.")
        async_engine.stop()
        return

    mode = "shadow" if at_cfg["shadow_mode"] else "LIVE"
    logger.info("Phase 6 live — %s alerts. Press 'q' to quit.", mode)

    clips_submitted = 0
    last_logged_ms = None
    latest_activity = sm_cfg["normal_class"]
    latest_duration = 0.0
    latest_alert = None
    alert_banner_until = 0.0

    try:
        while streamer._running:
            preview = streamer.get_frame()
            if preview is not None:
                if time.time() < alert_banner_until and latest_alert is not None:
                    shown = draw_overlay(preview, latest_activity, latest_duration, latest_alert)
                else:
                    shown = draw_overlay(preview, latest_activity, latest_duration, None)
                cv2.imshow("DMS Phase 6 — Alerts", shown)

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

                    alert = alert_trigger.check(activity, duration, conf)
                    if alert is not None:
                        latest_alert = alert
                        alert_banner_until = time.time() + 3.0

                    raw_class = max(probs, key=probs.get)
                    raw_prob = probs[raw_class]

                    logger.info(
                        "Raw: %s (%.0f%%) → Stable: %s | duration: %.1fs | inference: %.0fms",
                        raw_class,
                        raw_prob * 100,
                        activity,
                        duration,
                        ms,
                    )

            if cv2.waitKey(1) & 0xFF == ord("q"):
                logger.info("I pressed 'q' — shutting down.")
                break

    finally:
        streamer.stop()
        async_engine.stop()
        cv2.destroyAllWindows()
        logger.info("I submitted %d clips and finished Phase 6 test.", clips_submitted)




if __name__ == "__main__":
    main()

