import numpy as np
from src.phase2.sliding_buffer import SlidingBuffer

buffer = SlidingBuffer(clip_length=16, model_size=224, normalize="0to1")

# I'm faking a Phase 1 frame (640x480, values 0-255).
fake_frame = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
buffer.add_frame(fake_frame)

frame = buffer._frames[0]

print("Shape:", frame.shape)
print("Data type:", frame.dtype)
print("Min value:", frame.min())
print("Max value:", frame.max())