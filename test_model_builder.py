import yaml
from src.phase3.model_builder import build_video_model

with open("config.yaml") as f:
    config = yaml.safe_load(f)

mdl = config["model"]

model = build_video_model(
    num_classes=mdl["num_classes"],
    clip_length=mdl["clip_length"],
    height=mdl["model_size"],
    width=mdl["model_size"],
)

model.summary()

# I'm checking the model accepts the same shape Phase 2 produces.
import numpy as np
fake_clip = np.random.rand(1, 16, 224, 224, 3).astype(np.float32)
pred = model.predict(fake_clip, verbose=0)
print("Output shape:", pred.shape)
print("Probabilities sum:", pred.sum())
print("Sample probs:", pred[0])