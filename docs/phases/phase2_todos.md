# Phase 2 — Sliding Buffer 

**MY Goal:** Take single frames from Phase 1 and organize them into 16-frame chunks, preprocessed and ready for our TensorFlow Swin model.

---

## What Phase 2 receives from Phase 1

- Frames at **15 FPS**
- Size **640×480** (RGB)
- From `streamer.get_frame()` or the queue inside `VideoStreamer`

## What Phase 2 must output (for TensorFlow later)

- **16 frames** per clip
- Resized to **224×224**
- Normalized pixels (i will lock exact values in config)
- Tensor shape: `[1, 16, 224, 224, 3]`  batch, time, height, width, channels (TensorFlow style)

---



## My TODO checklist


| Step | What we build                                          | Status |
| ---- | ------------------------------------------------------ | ------ |
| 1    | Add preprocessing settings to `config.yaml`            | ✅      |
| 2    | Create `sliding_buffer.py` — FIFO deque of 16 frames   | ✅      |
| 3    | Resize to 224×224 + normalize on each frame            | ✅      |
| 4    | Sliding stride — new clip every 8 frames (50% overlap) | ✅      |
| 5    | Convert 16 frames to a NumPy tensor                    | ✅      |
| 6    | Connect Phase 1 → Phase 2 in a test script             | ✅      |
| 7    | Log clip readiness without AI (stub Phase 4)           | ✅      |


---



## My Step-by-step build order



### Step 1 — Config

I am adding `buffer` section to `config.yaml`:

- `clip_length: 16`
- `stride: 8`
- `model_size: 224`
- `normalize: "0to1"` 



### Step 2 — FIFO buffer

I aam using `collections.deque(maxlen=16)`  when frame 17 arrives, frame 1 drops off

### Step 3 — Preprocess

Each frame: resize 640×480 → 224×224, divide pixels by 255.0

### Step 4 — Stride

I am not converting to tensor every frame  only every 8 new frames (half overlap)

### Step 5 — Tensor

I am stacking 16 preprocessed frames into shape `(16, 224, 224, 3)`

### Step 6 — Test

`test_buffer.py`: run Phase 1 + Phase 2 together, print "Clip ready!" with tensor shape

### Step 7 — Ready for Phase 4

When Phase 3 gives mee a TensorFlow SavedModel, Phase 4 feeds this tensor in.

---



