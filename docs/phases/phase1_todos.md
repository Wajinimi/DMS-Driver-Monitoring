# Phase 1 — Video Streamer 

**Goal:** Get frames from the webcam into memory at 15 FPS, resized to 640×480, without lagging.

---

## My TODO checklist


| Step | What we build                               | Status |
| ---- | ------------------------------------------- | ------ |
| 1    | Project folders + `requirements.txt`        | ✅      |
| 2    | `config.yaml` — settings outside code       | ✅      |
| 3    | `opencv_camera.py` — open webcam            | ✅      |
| 4    | `video_streamer.py` — FPS sampling + resize | ✅      |
| 5    | Thread + bounded queue                      | ✅      |
| 6    | Camera watchdog                             | ✅      |
| 7    | `main_phase1.py` — test preview             | ✅      |


---

### 1a. Creating these folders inside `DMS Cursor`:

```text
src/
src/phase1/
docs/phases/
```

### 1b. Create empty `__init__.py` files

Create two empty files (can be blank for now):

- `src/__init__.py`
- `src/phase1/__init__.py`



### 1c. Create `requirements.txt` in the project root

I am going to Open a new file called `requirements.txt` and type these liness

```text
opencv-python>=4.8.0
numpy>=1.24.0
PyYAML>=6.0
```



### 1d. Install the packages

Running these  in my  terminal:

```bash
cd "/Users/dell/DMS Cursor"
python3 -m pip install -r requirements.txt
```



