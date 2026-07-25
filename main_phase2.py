"""
I'm running Phase 2 of the Driver Safety System.
Usage: python3 main_phase2.py
"""
import logging
import time

import cv2
import yaml

from src.phase1.video_streamer import VideoStreamer
from src.phase2.sliding_buffer import SlidingBuffer

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

    if not streamer.start():
        logger.error("I could not start the camera.")
        return

    logger.info("Phase 2 running. Click preview, press 'q' to quit.")
    clips_made = 0
    last_log = time.monotonic()

    try:
        while streamer._running:
            preview = streamer.get_frame()
            if preview is not None:
                cv2.imshow("DMS Phase 2 — Sliding Buffer", preview)

            frame = streamer.consume_frame()
            if frame is not None:
                buffer.add_frame(frame)

                if buffer.should_emit_clip():
                    clip = buffer.get_clip()
                    clips_made += 1

            now = time.monotonic()
            if now - last_log >= 2.0:
                logger.info(
                    "Clips made: %d | Buffer: %d frames | Last clip shape: %s",
                    clips_made,
                    buffer.buffer_size(),
                    clip.shape if clips_made > 0 else "none",
                )
                last_log = now

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        streamer.stop()
        cv2.destroyAllWindows()
        logger.info("Phase 2 finished. I made %d clips total.", clips_made)


if __name__ == "__main__":
    main()