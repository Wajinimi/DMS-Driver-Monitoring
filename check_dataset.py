import os

for split in ["train", "val"]:
    root = f"data/{split}"
    if not os.path.exists(root):
        print(f"Missing: {root}")
        continue
    print(f"\n--- {split} ---")
    for cls in os.listdir(root):
        cls_path = os.path.join(root, cls)
        if not os.path.isdir(cls_path):
            continue
        clips = [d for d in os.listdir(cls_path) if os.path.isdir(os.path.join(cls_path, d))]
        print(f"  {cls}: {len(clips)} clips")