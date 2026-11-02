# Model Version 2 — run a 10-class Swin model on clips from the sliding buffer

import logging
import os
import torch
import torchvision.models.video as video_models

logger = logging.getLogger(__name__)


class DummyInferenceEngine:
    def __init__(self, class_names):
        self._class_names = list(class_names)
        logger.warning(
            "DummyInferenceEngine for now"
            "OBD gating still works; predictions are not real."
        )

    def predict(self, clip_np):
        result = {}
        for name in self._class_names:
            result[name] = 0.02
        if "normal_driving" in result:
            result["normal_driving"] = 0.82
        return result


class InferenceEngine:
    def __init__(self, weights_path, num_classes=10, device="mps", class_names=None):
        self._device = torch.device(device)
        self._class_names = class_names or []
        self._model = self._load_model(weights_path, num_classes)
        logger.info("I loaded my 10-class Swin model on %s", self._device)

    def _load_model(self, weights_path, num_classes):
        model = video_models.swin3d_t(weights=None)
        in_features = model.head.in_features
        model.head = torch.nn.Linear(in_features, num_classes)

        weights = torch.load(weights_path, map_location=self._device)
        model.load_state_dict(weights)
        model.to(self._device)
        model.eval()
        return model

    def clip_to_tensor(self, clip_np):
        #convert Phase 2 output (16, 224, 224, 3) into (1, 3, 16, 224, 224)
        tensor = torch.from_numpy(clip_np).permute(3, 0, 1, 2)
        tensor = tensor.unsqueeze(0)
        return tensor.to(self._device)

    def predict(self, clip_np):
        tensor = self.clip_to_tensor(clip_np)
        with torch.no_grad():
            outputs = self._model(tensor)
            probs = torch.softmax(outputs, dim=1)[0]

        result = {}
        for i, name in enumerate(self._class_names):
            result[name] = probs[i].item()
        return result


def build_inference_engine(config):
    pt = config["pytorch"]
    mdl = config["model"]
    weights_path = pt["weights_path"]
    allow_missing = pt.get("allow_missing_weights", True)

    if os.path.isfile(weights_path):
        return InferenceEngine(
            weights_path=weights_path,
            num_classes=mdl["num_classes"],
            device=pt["device"],
            class_names=mdl["class_names"],
        )

    if not allow_missing:
        raise FileNotFoundError("I cannot find v2 weights at %s" % weights_path)

    logger.warning("dummy predictions.", weights_path)
    return DummyInferenceEngine(mdl["class_names"])
