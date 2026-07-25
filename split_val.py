"""
I'm moving 20% of clips from train to val — one split per class.
Run once only! Running twice will move more data out of train.
"""
import os
import random
import shutil

random.seed(42)  # same split every time

TRAIN_ROOT = "data/train"
VAL_ROOT = "data/val"
SPLIT = 0.2  # 20% goes to validation

for cls in os.listdir(TRAIN_ROOT):
    cls_train = os.path.join(TRAIN_ROOT, cls)
    if not os.path.isdir(cls_train):
        continue

    cls_val = os.path.join(VAL_ROOT, cls)
    os.makedirs(cls_val, exist_ok=True)

    clips = [
        d for d in os.listdir(cls_train)
        if os.path.isdir(os.path.join(cls_train, d))
    ]
    random.shuffle(clips)

    n_val = max(1, int(len(clips) * SPLIT))
    print(f"{cls}: moving {n_val} of {len(clips)} clips to val")

    for clip in clips[:n_val]:
        src = os.path.join(cls_train, clip)
        dst = os.path.join(cls_val, clip)
        shutil.move(src, dst)

print("Done! Run check_dataset.py again to verify.")