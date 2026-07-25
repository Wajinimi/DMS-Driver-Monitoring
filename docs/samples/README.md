# Recruitment samples — how everything should look

These files show **filled examples with placeholders**. Copy the structure, replace with real data.

| File | What it is |
|------|------------|
| [`../driver_recruitment_tracker.xlsx`](../driver_recruitment_tracker.xlsx) | Main Excel — **yellow rows are samples** (3 drivers, 5 sessions, 8 activities) |
| [`01_volunteer_consent_form_SAMPLE.md`](01_volunteer_consent_form_SAMPLE.md) | Consent form filled for DRV-001 |
| [`02_observer_session_notes_SAMPLE.md`](02_observer_session_notes_SAMPLE.md) | One complete session write-up (SES-003) |
| [`03_activity_log_card_SAMPLE.md`](03_activity_log_card_SAMPLE.md) | Single-behavior cards → go into Activity_Log sheet |
| [`04_folder_structure_SAMPLE.md`](04_folder_structure_SAMPLE.md) | How video files match Vol / Session / Log IDs |

## Sample story in the Excel file

| Vol ID | Who (placeholder) | Sessions | Highlights |
|--------|-------------------|----------|------------|
| DRV-001 | Amaka, 34, glasses, Lagos sedan | SES-001, SES-002 | Day commute + night drive; drinking water, glasses adjust |
| DRV-002 | Chidi, 28, SUV, beard | SES-003, SES-004 | Passenger, rain highway; phone-to-ear note |
| DRV-003 | Fatima, 23, hijab, rural hatchback | SES-005 | Rear passenger, sunglasses, rural road |

## Workflow

1. Sign consent → **Consent_Checklist** + PDF in `consent_scans/`
2. Record drive → row in **Driving_Sessions** + video in `raw/DRV-xxx/`
3. Review video → rows in **Activity_Log** + optional clips in `clips/`
4. Update **Diversity_Targets** counts
5. After ~10 hours video → taxonomy workshop → name classes
