# Phase 8 — Driver Dashboard 

**Goal:** Visualize Phase 7 SQLite data on a local dashboard (on bbrowser)

**Design choice :**  Plot 1 bar height = **total minutes distracted** per day.

---

## The two plots


| Plot       | What the driver sees                  | Data source                            |
| ---------- | ------------------------------------- | -------------------------------------- |
| **Plot 1** | 7 bars : today + last 6 days          | `get_last_7_days_summary()`            |
| **Plot 2** | Per-activity bars for one clicked day | `get_activity_breakdown_for_day(date)` |


---

## Architecture

```text
Browser (Chart.js bar charts)
        ↕ HTTP
Flask server (src/phase8/dashboard_server.py)
        ↕
AnalyticsLogger query methods (Phase 7)
        ↕
data/dms_analytics.db
```

The live driving pipeline (`test_phase7.py`) and the dashboard are **separate programs**, both read the same database.

---



## Our TODO checklist


| Step | What we build                                    | Status |
| ---- | ------------------------------------------------ | ------ |
| 1    | Config + install Flask + folder scaffold         | ✅      |
| 2    | `dashboard_server.py` — `/api/week` endpoint     | ✅      |
| 3    | `/api/day/<date>` endpoint                       | ✅      |
| 4    | `templates/dashboard.html` — Plot 1 bar chart    | ✅      |
| 5    | Click a bar → Plot 2 activity breakdown          | ✅      |
| 6    | `run_dashboard.py` — start server + open browser | ⬜      |
| 7    | Browser test with real DB data                   | ⬜      |


