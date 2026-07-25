"""
I'm checking that my trained weights load correctly before building Phase 4.
"""
import yaml
import torch
import torchvision.models.video as video_models

with open("config.yaml") as f:
    config = yaml.safe_load(f)

pt = config["pytorch"]
mdl = config["model"]

device = torch.device(pt["device"])
print(f"I'm using device: {device}")

# I'm building the same architecture I used in my notebook.
model = video_models.swin3d_t(weights=None)
in_features = model.head.in_features
model.head = torch.nn.Linear(in_features, mdl["num_classes"])

# I'm loading my trained weights.
weights = torch.load(pt["weights_path"], map_location=device)
model.load_state_dict(weights)
model.to(device)
model.eval()

print("Success! I loaded my Swin model with 5 classes.")
print(f"Class names: {mdl['class_names']}")