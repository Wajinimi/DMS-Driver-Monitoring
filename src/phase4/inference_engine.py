#Now this is my Phase 4.I want to run my Swin model on clips from Phase 2

import logging
import numpy as numpy
import torch 
import torchvision.models.video as video_models

logger = logging.getLogger(__name__)


class InferenceEngine:
    def __init__(self, weights_path, num_classes=5, device="mps", class_names=None):
        self._device = torch.device(device)  #still using my mps device since i have apple GPUU
        self._class_names = class_names or [] #i am kepping the class names for later
        self._model = self._load_model(weights_path, num_classes) #i am loading my model weights and preparing it for inference
        logger.info("I loaded my Swin model on %s", self._device)


    def _load_model(self, weights_path, num_classes):
        #i am building m model without pretrained weighs so i can replace classification head to match my task
        model = video_models_swin3d_t(weights=None)
        #i am readinh how many input features the current head uses so i can construct new head with correct inpit size
        in_features = model.head.in_features
        #i am creating new classification head with correct input size and output size for my task
        model.head = torch.nn.Linear(in_features, num_classes)

        #i am loading my trained weights and loading them to my model
        weights = torch.load(weights_path, map_location = sef._device)
        model.load_state_dict(weights)
        #i am moving my model to my device
        model.to(self._device)
        #switching to evaluation mode so i can run inference
        model.eval()
        return model


    #i am converting my phase 2 output (16, 224, 224, 3) Numpy into PyTorch input (1,3,16,224,224)
    def clip_to_tensor(self, clip_np):
        tensor = torch.from_numpy(clip_np).permute(3, 0, 1, 2)
        tensor = tensor.unsqueeze(0)
        return tensor.to(self._device)

    #i am running inference and returning a dict of class --> probability
    def predict(self, clip_np):
        tensor = self.clip_to_tensor(clip_np)

        with torch.no_grad():
            outputs = self._model(tensor)
            probs = torch.softmax(outputs, dim=1)[0]

        result = {}
        for i, name in enumerate(self._class_names):
            result[name] = probs[i].item()
        return result

    #i am building my swin3d_t model with the same head swap as my notebook
    def _load_model(self, weights_path, num_classes):
        model = video_models.swin3d_t(weights=None)
        in_features = model.head.in_features
        model.head = torch.nn.Linear(in_features, num_classes)
        weights = torch.load(weights_path, map_location=self._device)
        model.load_state_dict(weights)
        model.to(self._device)
        model.eval()
        return model

