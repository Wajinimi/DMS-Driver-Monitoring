import numpy as np
from src.phase2.sliding_buffer import SlidingBuffer

buffer = SlidingBuffer(clip_length=16, stride=8, model_size=224, normalize="0to1")

for i in range(24):
    fake_frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
    buffer.add_frame(fake_frame)

    if buffer.should_emit_clip():
        clip = buffer.get_clip()
        print(f"Frame {i + 1}: clip shape = {clip.shape}, dtype = {clip.dtype}")
        print(f"         min = {clip.min():.3f}, max = {clip.max():.3f}")