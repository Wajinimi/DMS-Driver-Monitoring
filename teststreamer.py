import logging
import yaml
from src.phase1.video_streamer import VideoStreamer

logging.basicConfig(level=logging.INFO)

with open("config.yaml") as f:
    config = yaml.safe_load(f)

cam = config["camera"]
streamer = VideoStreamer(
    target_fps=cam["target_fps"],
    frame_width=cam["frame_width"],
    frame_height=cam["frame_height"],
    watchdog_timeout_ms=cam["watchdog_timeout_ms"],
)

if streamer.start():
    print("Running... click the preview window, then press 'q' to quit.")
    try:
        streamer.run_once()
    finally:
        streamer.stop()