# Clip registry row — SAMPLE (matches Excel `Clip_Registry` sheet)

One row = **one training clip** (16 frames, 224×224 after export).

---

## Example: CLP-0001 (eat, train)

| Column | Sample value |
|--------|----------------|
| Clip ID | CLP-0001 |
| Segment ID | SEG-001 |
| Session ID | SES-001 |
| Vol ID | DRV-001 |
| Source Video Path | `/data/raw/DRV-001/SES-001.mp4` |
| Clip File Path | `/data/train/eat/CLP-0001.npy` |
| Start Time (video) | 07:51:55 |
| End Time (video) | 07:52:08 |
| Frame Count | 16 |
| **Primary Class** | **eat** |
| Secondary Class | *(empty)* |
| Label Confidence | High |
| **Split** | **train** |
| Labeled By | Labeler_A |
| Label Date | 2026-09-01 |
| Reviewed (Y/N) | Y |
| Reviewer | Reviewer_1 |
| Include in Dataset (Y/N) | Y |
| Reject Reason | *(empty)* |
| Day/Night | Day |
| Road | Urban |
| Weather | Sunny |
| Passenger | N |
| Notes | From observation LOG-001 |

---

## When to set Include in Dataset = N

| Reject Reason example | Why |
|-----------------------|-----|
| Face occluded | Can't see driver |
| Wrong class | Mislabeled |
| Bad clip length | Not 16 frames |
| Camera shake | Unusable frames |
| Duplicate of CLP-0002 | Near-identical clip |

Rejected clips stay in the sheet for audit but **do not** go into `data/train/`.

---

## Split rules (typical)

| Split | % of clips | Use |
|-------|------------|-----|
| train | ~80% | Model learns |
| val | ~15% | Tune thresholds / early stopping |
| test | ~5% | Final report only — never train on test |

Split by **Vol ID** when possible (all of DRV-001 val, DRV-002 train) so the model doesn't memorize one person's face.
