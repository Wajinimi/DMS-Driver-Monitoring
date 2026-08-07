# DMS — Driver Monitoring System

PyTorch pipeline: webcam → Swin3D → state smoothing → live alerts → SQLite → dashboard.

## Quick start

```bash
python3 -m pip install -r requirements.txt
# Copy model_swin/drive_and_act_swin_v1.pth (see model_swin/README.md)
python3 test_live_full.py
python3 run_dashboard.py   # http://127.0.0.1:5050
```

Set `pytorch.device` in `config.yaml`: `mps` (Apple GPU), `cuda` (NVIDIA), or `cpu`.

See [docs/SETUP_NEW_LAPTOP.md](docs/SETUP_NEW_LAPTOP.md) for moving to another machine.
