# Model Version 2 to Launch Next

I keep this folder separate from the Version 1 laptop DMS. I did not change the original `src/` files for this launch path.

**What is different from Version 1**

| | Version 1 (existing) | Version 2 (this folder) |
|--|----------------------|-------------------------|
| Speed | Keyboard `+` / `-` | Real OBD-II SPEED PID `0x0D` |
| Ignition | Keyboard `i` | OBD RPM as engine RUN / ACC |
| Classes | 5 (eat, seatbelt, jacket, sunglasses, magazine) | 10 classes below |
| Database | `data/dms_analytics.db` | `data/dms_v2_analytics.db` |

## 10 activity classes

1. `eating`
2. `drinking`
3. `texting`
4. `calling`
5. `distraction_outside` — looking outside the cabin
6. `distraction_in_car` — looking at in-car screens / instruments
7. `normal_driving`
8. `reaching_object`
9. `grooming_cosmetics`
10. `wearing_clothes_jacket`

## Hardware I need before a real run

1. OBDLink SX or EX **USB** in the car OBD port
2. USB into the Mac (USB-C adapter if needed)
3. Ignition **ON** (engine running is best)
4. FTDI VCP driver if `/dev/cu.usbserial*` does not appear
5. Optional: 10-class weights at `model_swin/drive_and_act_swin_v2.pth`

Until those weights exist I use dummy predictions (`normal_driving`) so I can still test OBD gating.

## Run

```bash
cd model_v2_launch_next
pip install -r requirements.txt
python3 test_obd_speed.py
python3 run_live.py
```

I do **not** map `+` / `-` / `i` to speed. ESC or `q` only quits the window.

If OBD fails to connect, I stop. I do not fall back to laptop keys.

Set an explicit serial port in `config.yaml` if auto-detect is wrong:

```yaml
drive_gating:
  obd:
    port: "/dev/cu.usbserial-XXXX"
    baudrate: 115200
```
