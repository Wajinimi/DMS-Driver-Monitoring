# Phase 10  Recommendation Engine + Personal Baselines

**Locked:** Rule-based coaching. Every recommendation explains **which rule fired**.

**Input:** Phase 9 weekly report (`safety_score`, `band`, `top_contributors`, `behavior_pct`).

**Output:** List of coaching messages + trend flags vs personal baseline.

---

## TODO checklist

| Step | What we build | Status |
|------|---------------|--------|
| 1 | `coaching` section in `config.yaml` + `RecommendationEngine` skeleton | ✅ |
| 2 | Score-band rules (High risk / Fair / Good / Excellent) | ✅ |
| 3 | Top-contributor + behavior-specific tip rules | ✅ |
| 4 | Personal baseline — 4-week rolling avg per behavior (SQLite) | ✅ |
| 5 | Trend flags (`increased` / `improved` vs baseline) | ✅ |
| 6 | `generate_weekly_coaching(end_date)` — full report | ✅ |
| 7 | `/api/weekly-coaching` + dashboard coaching card | ✅ |
| 8 | `test_recommendation_engine.py` — simulation | ✅ |

---

## Example rules (v1)

| Condition | Message |
|-----------|---------|
| `score < 70` | "Your safety score was high risk this week. Focus on reducing [top behavior]." |
| `[behavior] in top 2` | Behavior-specific tip from config |
| `this_week[b] > baseline[b] × 1.30` | "[Behavior] increased compared to your usual pattern." |
| `score >= 90` and improved | "Excellent concentration — keep it up." |

---

## Success criteria

When Phase 10 is done:

1. Given a weekly score report, I get 1–3 explainable coaching messages
2. Baselines compare this week vs rolling 4-week average per behavior
3. Dashboard shows recommendations under the safety score card
