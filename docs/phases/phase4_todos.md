# Phase 4 — PyTorch Inference 

**Goal:** Load my Swin3D-T weights and run inference on live clips from Phase 2.

**Model file:** `model_swin/drive_and_act_swin_v1.pth`

---

## TODO checklist


| Step | What we build                                                  | Status |
| ---- | -------------------------------------------------------------- | ------ |
| 1    | Verify `.pth` weights load into `swin3d_t`                     | ✅      |
| 2    | Create `src/phase4/inference_engine.py` load model             | ✅      |
| 3    | Add `clip_to_tensor()` NumPy clip → PyTorch `[1,3,16,224,224]` | ✅      |
| 4    | Add `predict()` return 5 classs probabilities                  | ✅      |
| 5    | Connect Phase 1 + 2 + 4 in `test_phase4.py`                    | ✅      |
| 6    | Async inference thread (production pattern)                    | ✅      |


---



## Tensor shapes to remember


| Stage                | Shape                     |
| -------------------- | ------------------------- |
| Phase 2 `get_clip()` | `(16, 224, 224, 3)` NumPy |
| PyTorch model input  | `(1, 3, 16, 224, 224)`    |
| Model output         | `(1, 5)` probabilities    |


---



## Class order which i must set to match training


| Index | Class      |
| ----- | ---------- |
| 0     | eat        |
| 1     | seatbelt   |
| 2     | jacket     |
| 3     | sunglasses |
| 4     | magazine   |


