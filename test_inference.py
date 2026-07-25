import logging
import numpy as np
import yaml
from src.phase4.inference_engine import InferenceEngine

logging.basicConfig(level=logging.INFO)

with open("config.yaml") as f:
    config = yaml.safe_load(f)

mdl = config["model"]
pt = config["pytorch"]

engine = InferenceEngine(
    weights_path=pt["weights_path"],
    num_classes=mdl["num_classes"],
    device=pt["device"],
    class_names=mdl["class_names"],
)

# I'm faking a Phase 2 clip to test the pipeline.
fake_clip = np.random.rand(16, 224, 224, 3).astype(np.float32)
probs = engine.predict(fake_clip)

print("Predictions on random clip:")
for name, prob in probs.items():
    print(f"  {name}: {prob:.3f}")