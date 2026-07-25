# I want to test my Phase 1 and pHade 2 together on my live webcam

import logging
import time
import cv2
import yaml
from src.phase1.video_streamer import VideoStreamer
from src.phase2.sliding_buffer import SlidingBuffer

logging.basicConfig(
    level= logging.INFO,
    format = "%(asctime)s | %(levelname)s | %(message)s",
    datefmt = "%H:%M:%S",
)
logger = logging.getLogger(__name__)

def main():
    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    cam = config["camera"]
    buf = config["buffer"]

    # I'm starting Phase 1 — the camera.
    streamer = VideoStreamer(
        target_fps=cam["target_fps"],
        frame_width=cam["frame_width"],
        frame_height=cam["frame_height"],
        watchdog_timeout_ms=cam["watchdog_timeout_ms"],
    )

    # I m starting Phase 2 — the sliding buffer.
    buffer = SlidingBuffer(
        clip_length=buf["clip_length"],
        stride=buf["stride"],
        model_size=buf["model_size"],
        normalize=buf["normalize"],
    )

    if not streamer.start():
        logger.error("I could not start the camera.")
        return

    logger.info("Phase 1 + 2 running. Click preview, press 'q' to quit.")
    clips_made = 0

    try:
        while streamer._running:
            #The job here is to look at the lastest frame frm Phase 1
            preview = streamer.get_frame()
            if preview is not None:
                cv2.imshow("DMS Phase 1 +2", preview)

            #The job here is to take the latest frame from phase 1 after looking
            frame = streamer.consume_frame()
            if frame is not None:
                buffer.add_frame(frame)
                if buffer.should_emit_clip():
                    clip = buffer.get_clip()
                    clips_made += 1
                    logger.info("Clip #%d ready! shape=%s | buffer=%d frames", clips_made, clip.shape, buffer.buffer_size(),)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
                
    finally:
        streamer.stop()
        cv2.destroyAllWindows()
        logger.info("I made %d clips total.", clips_made)


if __name__ == "__main__":
    main()