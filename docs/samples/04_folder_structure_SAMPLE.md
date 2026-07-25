# DATA FOLDER STRUCTURE (SAMPLE)

How files on disk should match Excel IDs.

```
data/
├── raw/                          # Full session videos
│   ├── DRV-001/
│   │   ├── SES-001.mp4
│   │   └── SES-002.mp4
│   ├── DRV-002/
│   │   ├── SES-003.mp4
│   │   └── SES-004.mp4
│   └── DRV-003/
│       └── SES-005.mp4
│
├── clips/                        # Short extracts for labeling
│   ├── LOG-001.npy               # or .mp4 — 16-frame clips later
│   ├── LOG-002.npy
│   └── ...
│
├── consent_scans/                # Signed PDFs (private — not in git)
│   ├── DRV-001_consent.pdf
│   ├── DRV-002_consent.pdf
│   └── DRV-003_consent.pdf
│
└── recruitment/
    └── driver_recruitment_tracker.xlsx
```

---

## ID rules

| ID type | Format | Example |
|---------|--------|---------|
| Volunteer | DRV-### | DRV-001 |
| Session | SES-### | SES-003 |
| Activity log | LOG-### | LOG-007 |

Always use the **same IDs** in Excel, filenames, and notes.
