import numpy as np
from src.phase2.sliding_buffer import SlidingBuffer

buffer = SlidingBuffer(
    clip_length=16,
    model_size=224,
    normalize="imagenet",
    imagenet_mean=[0.485, 0.456, 0.406],
    imagenet_std=[0.229, 0.224, 0.225],
)

fake = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
buffer.add_frame(fake)

frame = buffer._frames[0]
print("Shape:", frame.shape)
print("Min:", round(frame.min(), 3), "Max:", round(frame.max(), 3))