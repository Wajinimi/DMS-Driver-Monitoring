
import logging
import time

import cv2
import yaml

from src.phase1.video_streamer import VideoStreamer
from src.phase2.sliding_buffer import SlidingBuffer
from src.phase4.async_inference import AsyncInference
from src.phase4.inference_engine import InferenceEngine
from src.phase5.state_manager import StateManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    # oading all my settings from config.yaml so nothing is hardcoded
    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    cam = config["camera"]
    buf = config["buffer"]
    mdl = config["model"]
    pt = config["pytorch"]
    sm_cfg = config["state_manager"]

    # Phase 1: starting the video streamer (webcam, 15 FPS, 640x480)
    streamer = VideoStreamer(
        target_fps=cam["target_fps"],
        frame_width=cam["frame_width"],
        frame_height=cam["frame_height"],
        watchdog_timeout_ms=cam["watchdog_timeout_ms"],
    )

    # Phase 2: creating the sliding buffer (16 frames, ImageNet norm)
    buffer = SlidingBuffer(
        clip_length=buf["clip_length"],
        stride=buf["stride"],
        model_size=mdl["model_size"],
        normalize=mdl["normalize"],
        imagenet_mean=mdl["imagenet_mean"],
        imagenet_std=mdl["imagenet_std"],
    )

    # Phase 4: I'm loading my Swin model for inference
    engine = InferenceEngine(
        weights_path=pt["weights_path"],
        num_classes=mdl["num_classes"],
        device=pt["device"],
        class_names=mdl["class_names"],
    )

    # running inference in a background thread so the camera never waits
    async_engine = AsyncInference(engine)
    async_engine.start()

    # Phase 5: I'm creating the state manager (threshold + smoothing).
    state_manager = StateManager(
        default_threshold=sm_cfg["default_threshold"],
        exit_threshold=sm_cfg["exit_threshold"],
        normal_class=sm_cfg["normal_class"],
        smoothing_windows=sm_cfg["smoothing_windows"],
    )

    if not streamer.start():
        logger.error("I could not start the camera.")
        async_engine.stop()
        return

    logger.info("Phase 5 live — webcam + model + state manager. Press 'q' to quit.")

    clips_submitted = 0
    last_logged_ms = None

    try:
        while streamer._running:
            # peeking at the latest frame for the preview window only
            preview = streamer.get_frame()
            if preview is not None:
                cv2.imshow("DMS Phase 5 — Stable State", preview)

            # taking one real frame off the queue for Phase 2
            frame = streamer.consume_frame()
            if frame is not None:
                buffer.add_frame(frame)

                # submitting a new clip when the buffer is ready (every 0.5 sec)
                if buffer.should_emit_clip():
                    clip = buffer.get_clip()
                    async_engine.submit_clip(clip)
                    clips_submitted += 1

            # Ichecking if the inference thread has a new result for me
            result = async_engine.get_latest_result()
            if result is not None:
                ms = result["inference_time_ms"]

                # I am only processing each inference result once (avoid duplicate logs)
                if ms != last_logged_ms:
                    last_logged_ms = ms
                    probs = result["probabilities"]

                    # I'm passing raw probabilities to Phase 5 for smoothing
                    start_time, activity, conf, duration = state_manager.update(probs)

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
        logger.info("I submitted %d clips and finished Phase 5 test.", clips_submitted)


if __name__ == "__main__":
    main()
