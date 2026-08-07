# Phase 5  State Manager 

**Goal:** Filter raw AI predictions so one flickering frame doesn't trigger false alarms.

**Input:** Dict from Phase 4 — `{"eat": 0.35, "seatbelt": 0.58, ...}`

**Output:** Stable activity state + start time → feeds Phase 6 (alerts) and Phase 7 (analytics)

---

I need this because

My logs show the model flickers:

```text
seatbelt (57%) → sunglasses (39%) → seatbelt (48%) → eat (35%)
```

Raw predictions jump every 0.5 seconds. The State Manager **smooths** this before any alert fires.

---

## Our TODO checklist


| Step | What i built                                                   | Status |
| ---- | -------------------------------------------------------------- | ------ |
| 1    | Add `state_manager` settings to `config.yaml`                  | ✅      |
| 2    | Createed`src/phase5/state_manager.py` — basic threshold filter | ✅      |
| 3    | Added per-class confidence thresholds                          | ✅      |
| 4    | Addedd temporal smoothing (class-specific windows)             | ✅      |
| 5    | Added activity tracking (current state + start time)           | ✅      |
| 6    | Connected Phase 4 → Phase 5 in `test_phase5.py`                | ✅      |


---



## Design decisions (locked for v1)


| Setting            | Value                     | Why                           |
| ------------------ | ------------------------- | ----------------------------- |
| Default threshold  | 50% to enter a state      | Below this = "normal_driving" |
| Phone-like classes | Shorter smoothing window  | Fast detection (Phase 5 v2)   |
| Eat / magazine     | Longer smoothing window   | Slower actions                |
| Hysteresis         | Enter at 50%, exit at 35% | Stops flicker at boundary     |




### Class-specific smoothing windows (predictions to look back)


| Class      | Window        | ~seconds at 2 preds/sec |
| ---------- | ------------- | ----------------------- |
| eat        | 3 predictions | ~1.5 sec                |
| seatbelt   | 3             | ~1.5 sec                |
| jacket     | 5             | ~2.5 sec                |
| sunglasses | 3             | ~1.5 sec                |
| magazine   | 5             | ~2.5 sec                |


---



