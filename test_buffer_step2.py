import numpy as np
from src.phase2.sliding_buffer import SlidingBuffer

buffer = SlidingBuffer(clip_length=16)

for i in range(20):
    fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    buffer.add_frame(fake_frame)
    print(
        f"Frame {i + 1}: buffer size = {buffer.buffer_size()}, ready = {buffer.is_ready()}"
    )