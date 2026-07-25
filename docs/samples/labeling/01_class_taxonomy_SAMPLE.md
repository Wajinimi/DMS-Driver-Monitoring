# Class taxonomy row — SAMPLE (matches Excel `Class_Taxonomy` sheet)

After your workshop, **one row per class**. Every name in `Clip_Registry.primary_class` must appear here.

---

## Example: `phone_hand`

| Column | Sample value |
|--------|----------------|
| Class ID | 4 |
| Class Name (code) | `phone_hand` |
| Display Name | Phone in hand |
| Definition | Phone visible in hand; scrolling or holding — not necessarily a call |
| Example in video | Driver scrolling phone at lap level in slow traffic |
| Include in Training | Y |
| Is Distraction | Y |
| Alert Enabled | Y |
| Alert Duration (sec) | 2.0 |
| Smoothing Window | 3 |
| Alert Sound File | Ping.aiff |
| Target Clips (min) | 100 |
| Notes | High priority for Nigeria fleet |

---

## Example: `normal_driving`

| Column | Sample value |
|--------|----------------|
| Class Name | `normal_driving` |
| Definition | Eyes on road, hands on wheel, no secondary task |
| Include in Training | Y |
| Is Distraction | N |
| Alert Enabled | N |
| Target Clips (min) | 50 |
| Notes | Need many negative examples or model will over-alert |

---

## Rules

1. **Class Name** = folder name under `data/train/` and `data/val/`.
2. Do not rename a class after clips are labeled — create `phone_hand_v2` instead.
3. If two behaviors merge (e.g. `texting` + `phone_hand`), update taxonomy first, then re-label clips in QA.
