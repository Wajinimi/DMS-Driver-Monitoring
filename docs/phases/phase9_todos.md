# Phase 9 — Safety Score Engine (we build this together)

**Locked:** Hybrid scoring — weighted contributions → **Safety Score /100**.

**Input:** Phase 7 `activities` table (behavior, `duration_sec`, timestamps).

**Output:** Trip score, weekly score, top contributors, classification band.

---

## TODO checklist

| Step | What we build | Status |
|------|---------------|--------|
| 1 | `safety_score` section in `config.yaml` (weights, bands, scale_factor) | ✅ |
| 2 | `src/phase9/safety_score_engine.py` — contribution math | ✅ |
| 3 | `compute_trip_score(trip_id)` | ✅ |
| 4 | `compute_weekly_score(end_date)` — 7-day window | ✅ |
| 5 | `get_top_contributors()` — for reports | ✅ |
| 6 | `test_safety_score.py` — simulation with fake activities | ✅ |
| 7 | Wire weekly score into dashboard API | ✅ |

---

## Success criteria

When Phase 9 is done:

1. Given a trip in SQLite, I get `{safety_score: 87, band: "Good", contributors: [...]}`
2. Given a week, I get safe_driving % + behavior % + overall score
3. Formula matches `docs/safety_coaching_system.md`
