# Labeling phase — sample pack (AFTER classes are defined)

Use these **after** your taxonomy workshop. The discovery/recruitment Excel is separate.

| Phase | Workbook |
|-------|----------|
| Observe drivers, note behaviors | [`driver_recruitment_tracker.xlsx`](../driver_recruitment_tracker.xlsx) |
| **Label clips, build dataset** | [`dms_labeling_tracker.xlsx`](../dms_labeling_tracker.xlsx) |

---

## Workflow

```text
Observation logs (neutral text)
        ↓
Taxonomy workshop → Class_Taxonomy sheet
        ↓
Mark segments in full video → Segment_Log
        ↓
Export 16-frame clips → Clip_Registry
        ↓
QA review → Labeling_QA
        ↓
Check balance → Dataset_Split
        ↓
data/train/ and data/val/ folders → train Swin
```

---

## Sample files

| File | Shows |
|------|--------|
| [`01_class_taxonomy_SAMPLE.md`](01_class_taxonomy_SAMPLE.md) | How one class row should read |
| [`02_clip_registry_SAMPLE.md`](02_clip_registry_SAMPLE.md) | One fully labeled clip |
| [`03_folder_layout_SAMPLE.md`](03_folder_layout_SAMPLE.md) | `data/train/eat/`, `data/val/` layout |

---

## Sample classes in the Excel (placeholders — replace with yours)

`normal_driving`, `eat`, `drink`, `phone_hand`, `phone_call`, `texting`, `magazine`, `looking_away`, `passenger_talk`, `adjust_glasses`, `adjust_seatbelt`, `smoking`, `sunglasses_on`

Green rows in the Excel = filled examples only.
