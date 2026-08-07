# Phase 6  Alert Trigger )

**Goal:** Turn stable activity + duration from Phase 5 into actionable alerts  without spamming the driver.

**Input:** `(activity, duration, confidence)` from `StateManager.update()`

**Output:** Alert dict (or `None`) → feeds Phase 7 (analytics)

---

## Why i need this

Phase 5 gave  me:

```text
Stable: magazine | duration: 8.0s
```

That is **information**. Phase 6 decides **when to act**:

- Only after the behavior lasts long enough (duration threshold)
- Not again for 10 seconds (cooldown)
- In shadow mode first, log only, no beep yet

---



## Our TODO checklist


| Step | What i want to build                                              | Status |
| ---- | ---------------------------------------------------------- | ------ |
| 1    | Add `alert_trigger` settings to `config.yaml`              | ✅      |
| 2    | Create `src/phase6/alert_trigger.py` — duration thresholds | ✅      |
| 3    | Add cooldown + shadow mode                                 | ✅      |
| 4    | Add speed gating (off on laptop)                           | ✅      |
| 5    | Simulation test `test_alert_trigger.py`                    | ✅      |
| 6    | Live pipeline `test_phase6.py`                             | ✅      |


---



## Design decisions (locked for v1)


| Setting                       | Value                             | Why                                                  |
| ----------------------------- | --------------------------------- | ---------------------------------------------------- |
| `shadow_mode: true`           | Log alerts, don't beep            | Safe testing on laptop                               |
| `cooldown_seconds: 10`        | Same class can't re-alert for 10s | Stops spam                                           |
| `magazine: 3.0`               | 3 seconds sustained               | Matches your Phase 5 test (2.5s smoothing + 3s hold) |
| `speed_gating_enabled: false` | Off on laptop                     | No GPS yet turn on in the car                        |




### Duration thresholds (seconds)


| Class      | Threshold | Rationale                           |
| ---------- | --------- | ----------------------------------- |
| eat        | 2.0       | Quick distraction                   |
| seatbelt   | 5.0       | Slower action avoid false positives |
| jacket     | 4.0       | Putting on/removing jacket          |
| sunglasses | 3.0       | Medium                              |
| magazine   | 3.0       | Reading my logs hit 8s reliably     |


