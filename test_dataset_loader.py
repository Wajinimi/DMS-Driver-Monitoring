import yaml
from src.phase3.dataset_loader import build_tf_dataset, load_clip, list_clips

with open("config.yaml") as f:
    config = yaml.safe_load(f)

mdl = config["model"]
class_names = mdl["class_names"]

# Test 1: list clips
clips = list_clips("data/train", class_names)
print(f"I found {len(clips)} training clips")

# Test 2: load one clip
clip_path, label = clips[0]
clip = load_clip(clip_path, mdl["clip_length"], mdl["model_size"],
                 mdl["imagenet_mean"], mdl["imagenet_std"])
print(f"One clip shape: {clip.shape}, label: {class_names[label]}")

# Test 3: TensorFlow dataset batch
ds, n = build_tf_dataset("data/train", class_names,
                         mdl["clip_length"], mdl["model_size"],
                         mdl["imagenet_mean"], mdl["imagenet_std"],
                         batch_size=2)
for batch_clips, batch_labels in ds.take(1):
    print(f"Batch clips shape: {batch_clips.shape}")
    print(f"Batch labels: {batch_labels.numpy()}")