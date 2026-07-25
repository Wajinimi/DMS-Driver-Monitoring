# Phase 7 — Analytics Logger )

**Goal:** Save driver activity and alerts to SQLite  dashboard-ready for Phase 8.

**My Design choice :** Plot 1 bar height = **total minutes distracted** per day.

**Input:**

- State changes from Phase 5 (`activity`, `duration`, timestamps)
- Alerts from Phase 6 (`alert` dict)

**Output:**

- SQLite database at `data/dms_analytics.db`
- Query functions for Phase 8 dashboard

---

## Our TODO checklist


| Step | What we build                                                                | Status |
| ---- | ---------------------------------------------------------------------------- | ------ |
| 1    | `analytics` config + folder scaffold                                         | ✅      |
| 2    | SQLite schema (trips, activities, alerts)                                    | ✅      |
| 3    | `start_trip()` / `end_trip()`                                                | ✅      |
| 4    | `log_state_change()` : save activity segments                                | ✅      |
| 5    | `log_alert()` : save alert rows                                              | ✅      |
| 6    | Query API : `get_last_7_days_summary()` + `get_activity_breakdown_for_day()` | ✅      |
| 7    | Wire into `test_phase7.py` (live pipeline)                                   | ✅      |
| 8    | Quick query test : verify 7-day data shape                                   | ✅      |


---



## Database tables (preview)



### `trips`

One row per driving session (i will press q to quit)

### `activities`

One row per stable behavior segment (eat 4.3s, magazine 7.0s, etc.).

### `alerts`

One row per Phase 6 alert (shadow or live).

