# Driver Safety Score & Coaching System (Phase 9+)

**Decision (locked):** **Hybrid scoring** — weighted contributions internally, displayed as **Safety Score /100**.

**Research angle:** Explainable coaching (scores + trends + rules), not just classification.

---

## Why hybrid (not pure subtract-from-100)

| Approach | Driver sees | You can explain |
|----------|-------------|-----------------|
| Pure subtract | 87/100 | Hard to show *which* behaviors hurt most |
| Pure risk sum | 62 risk | Drivers expect “higher = safer” |
| **Hybrid** | **87/100** + “top contributors” | **Both** — simple grade + breakdown |

---

## Scoring formula

### Step 1 — Per behavior, compute contribution

For each distraction behavior `b` during a period (trip or week):

```text
contribution[b] = exposure[b] × weight[b]
```

**Exposure** (pick one — lock in Phase 9 Step 1):

| Option | Formula | Best for |
|--------|---------|----------|
| **A — Duration (recommended)** | seconds in behavior `b` | Fair across short/long trips |
| B — Event count | number of alert-eligible segments | Simple, ignores duration |
| C — Hybrid | `seconds × 0.7 + count × 0.3` | Research later |

Example weights (placeholder — add citations in `safety_score_weights.md`):

| Behavior | Weight (pts per second or per normalized unit) |
|----------|-----------------------------------------------|
| phone | 10 |
| microsleep / eyes closed >2s | 20 |
| looking_away | 8 |
| smoking | 4 |
| yawning | 5 |
| eating | 3 |
| drinking | 2 |

*Until Nigerian taxonomy is final, map your current classes (eat, magazine, …) to these weights.*

### Step 2 — Total risk points

```text
total_risk = sum(contribution[b] for all behaviors b)
```

### Step 3 — Normalize to 0–100 risk, then flip to safety score

```text
# Cap so one terrible trip doesn't break the scale
normalized_risk = min(100, total_risk × scale_factor)

safety_score = 100 - normalized_risk
```

**`scale_factor`** — tune on pilot data so a typical “good” week ≈ 85–95. Start with `scale_factor = 0.1` and adjust.

### Step 4 — Classification bands

| Safety Score | Label |
|--------------|-------|
| 90–100 | Excellent |
| 80–89 | Good |
| 70–79 | Fair |
| Below 70 | High risk |

---

## Worked example (weekly)

Driver week totals (exposure in **minutes** × weight per minute):

| Behavior | Minutes | Weight | Contribution |
|----------|---------|--------|--------------|
| phone | 2.0 | 10 | 20 |
| looking_away | 3.0 | 8 | 24 |
| eating | 1.5 | 3 | 4.5 |
| smoking | 0.5 | 4 | 2 |
| **Total risk** | | | **50.5** |

```text
normalized_risk = min(100, 50.5 × 0.1) = 5.05   # if scale_factor = 0.1
safety_score = 100 - 5.05 ≈ 95 → Excellent
```

*(Adjust `scale_factor` so realistic distraction weeks land in 70–90 range — calibrate on real data.)*

**Top contributors for report:** looking_away (24), phone (20).

---

## Safe driving percentage (separate from score)

For the weekly report bar / percentages:

```text
safe_driving_pct = (time in normal_driving) / (total trip time) × 100
behavior_pct[b] = (time in behavior b) / (total trip time) × 100
```

Score and percentages complement each other:
- **Percentages** = “what did I do?”
- **Score** = “how risky was it, weighted?”

---

## Personal baseline (Option 5 — Phase 10)

Per driver, store rolling 4-week average for each behavior.

```text
if this_week[b] > baseline[b] × 1.30:
    flag "increased significantly"
elif this_week[b] < baseline[b] × 0.85:
    flag "improved"
```

Recommendations combine: **score band** + **top contributors** + **personal trend**.

---

## Recommendation engine (Option 1 + 4 rules)

Example rules:

| Condition | Recommendation |
|-----------|----------------|
| score < 70 | "Your safety score was high risk this week. Focus on reducing [top behavior]." |
| looking_away in top 2 | "Keep eyes on the road at junctions; mount phone at eye level." |
| phone increased >30% vs baseline | "Phone use rose compared to your usual pattern." |
| score 90+ and improved | "Excellent concentration — keep it up." |

All rules log **which condition fired** (explainable).

---

## Pipeline placement

```text
Phase 7 SQLite (activities, duration, alerts)
        ↓
Phase 9  SafetyScoreEngine — trip + weekly score, contributors
        ↓
Phase 10 RecommendationEngine — rules + baselines
        ↓
Phase 8  Dashboard — score gauge, weekly report, trends
```

---

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 9 | Safety Score Engine | ✅ Done |
| 10 | Recommendation + personal baselines | ✅ Done |
| 11 | Dashboard score & weekly report UI | ⬜ |

---

## What we need before coding

1. Final behavior list (from Nigerian pilot) — weights table updated  
2. Lock exposure = duration (seconds) for v1  
3. Calibrate `scale_factor` on 5–10 real trips  

---

*Hybrid scoring: locked. Next step: Phase 9 Step 1 — config + `SafetyScoreEngine` skeleton.*
