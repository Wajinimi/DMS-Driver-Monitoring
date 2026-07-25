# Dataset folder layout — SAMPLE (after labeling)

Matches `Clip File Path` column in Excel.

```
data/
├── raw/                              # Full sessions (from recruitment phase)
│   └── DRV-001/
│       └── SES-001.mp4
│
├── train/                            # ~80% of clips
│   ├── normal_driving/
│   │   ├── CLP-0005.npy
│   │   └── ...
│   ├── eat/
│   │   ├── CLP-0001.npy
│   │   └── ...
│   ├── phone_hand/
│   ├── magazine/
│   └── passenger_talk/
│
├── val/                              # ~15% — same class subfolders
│   ├── phone_hand/
│   │   └── CLP-0003.npy
│   └── magazine/
│       └── CLP-0006.npy
│
└── test/                             # Optional hold-out
    └── ...
```

---

## Link back to Excel

| On disk | Excel column |
|---------|----------------|
| `CLP-0001.npy` | Clip ID |
| `eat/` folder name | Primary Class |
| `train/` vs `val/` | Split |

---

## After export

Run your existing check:

```bash
python3 check_dataset.py
```

Target before training: **≥50 clips per important class**, balanced `train/` vs `val/`.
