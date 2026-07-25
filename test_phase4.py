"""
I'm testing the full pipeline: Phase 1 + 2 + 4 on my live webcam.
Usage: python3 test_phase4.py
"""
import logging
import time

import cv2
import yaml

from src.phase1.video_streamer import VideoStreamer
from src.phase2.sliding_buffer import SlidingBuffer
from src.phase4.async_inference import AsyncInference
from src.phase4.inference_engine import InferenceEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def main():
    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    cam = config["camera"]
    buf = config["buffer"]
    mdl = config["model"]
    pt = config["pytorch"]

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

    if not streamer.start():
        logger.error("I could not start the camera.")
        async_engine.stop()
        return

    logger.info("Full pipeline running. Click preview, press 'q' to quit.")
    clips_submitted = 0
    last_logged_ms = None

    try:
        while streamer._running:
            preview = streamer.get_frame()
            if preview is not None:
                cv2.imshow("DMS Phase 4 — Live AI", preview)

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
                    top_class = max(probs, key=probs.get)
                    top_prob = probs[top_class]
                    logger.info(
                        "Prediction: %s (%.1f%%) | inference: %.0fms",
                        top_class,
                        top_prob * 100,
                        ms,
                    )

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        streamer.stop()
        async_engine.stop()
        cv2.destroyAllWindows()
        logger.info("I submitted %d clips total.", clips_submitted)


if __name__ == "__main__":
    main()
