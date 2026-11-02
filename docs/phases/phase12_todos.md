# Phase 12 — Speed + ignition gating

**Goal:** Only run the DMS pipeline (model, alerts, analytics) when the vehicle is actually driving.

---

## TODO checklist

| Step | What we build | Status |
|------|---------------|--------|
| 1 | `DriveContext` — ON at 15 km/h, OFF below 5 km/h for 10s | ✅ |
| 2 | `drive_gating` in `config.yaml` | ✅ |
| 3 | Gate `test_live_full.py` + mock keyboard (+/-, i) | ✅ |
| 4 | `test_drive_context.py` | ✅ |
| 5 | End-of-trip score in post-session print | ✅ |
| 6 | OBD-II / CAN speed provider (real car) | ⬜ |
| 7 | On-screen trip summary overlay | ✅ |
| 8 | `generate_trip_coaching()` — trip tips without weekly trends | ✅ |

---

## Mock keys (laptop)

| Key | Action |
|-----|--------|
| `+` or `=` | Speed +5 km/h |
| `-` | Speed −5 km/h |
| `i` | Toggle ignition RUN / OFF |
| `q` | Quit and save trip |

**Test flow:** press `+` three times (0→15) to turn monitoring ON, then act out distractions.

---

## Config defaults (urban Nigeria)

```yaml
activate_speed_kmh: 15
deactivate_speed_kmh: 5
deactivate_hold_sec: 10
require_ignition_run: true
```
