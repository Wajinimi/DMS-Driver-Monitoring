import numpy as np
from src.phase2.sliding_buffer import SlidingBuffer

buffer = SlidingBuffer(clip_length=16, stride=8, model_size=224, normalize="0to1")

for i in range(30):
    fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    buffer.add_frame(fake_frame)

    if buffer.should_emit_clip():
        print(f"Clip ready at frame {i + 1}!")