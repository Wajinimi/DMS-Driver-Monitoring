
import logging
import time
import yaml
import cv2

from src.phase1.video_streamer import VideoStreamer

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
    streamer = VideoStreamer(
        target_fps=cam["target_fps"],
        frame_width=cam["frame_width"],
        frame_height=cam["frame_height"],
        watchdog_timeout_ms=cam["watchdog_timeout_ms"],
    )

    if not streamer.start():
        logger.error("I could not start the video streamer.")
        return

    logger.info("Phase 1 running. Click preview window, press 'q' to quit.")
    last_log = time.monotonic()

    try:
        while streamer._running:
            frame = streamer.get_frame()
            if frame is not None:
                cv2.imshow("DMS Phase 1 — Driver Safety System", frame)

            now = time.monotonic()
            if now - last_log >= 2.0:
                logger.info("Queue size: %d | Frame shape: %s", streamer.get_queue_size(), frame.shape if frame is not None else "none")
                last_log = now

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        streamer.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()