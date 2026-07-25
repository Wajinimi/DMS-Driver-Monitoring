# This is my Phase 2 which is responsible for collecting frames into a silding window for myy model

import logging
from collections import deque
import numpy as np
import cv2

logger = logging.getLogger(__name__)

class SlidingBuffer:
    def __init__(self, clip_length=16, stride=8, model_size=224, normalize="0to1", imagenet_mean=None, imagenet_std=None):
        self._clip_length = clip_length #I am storing the number of frames my mddel is expecting
        self._frames = deque(maxlen=clip_length) #i am using deque with maxlen so the oldest frame drop off automatically when it gets to frame 17
        self._frames_added = 0 #i am starting my counter at 0 so i know how many frames i have added
        self._model_size = model_size #i am sorting out the model sizze to 224 x 224 pixels which my model is expting
        self._normalize = normalize #the normalizayion would be between 0 and 1 so all pixel values remain on the same scale
        self._stride = stride 
        self._imagenet_mean = np.array(imagenet_mean if imagenet_mean else [0.485, 0.456, 0.406], dtype=np.float32)
        self._imagenet_std = np.array(imagenet_std if imagenet_std else [0.229, 0.224, 0.225], dtype=np.float32)


    def _preprocess_frame(self, frame):
        resized = cv2.resize(
            frame,
            (self._model_size, self._model_size),
            interpolation=cv2.INTER_AREA,
        )

        # I'm converting BGR (OpenCV) to RGB before normalizing.
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        pixels = rgb.astype(np.float32) / 255.0

        if self._normalize == "0to1":
            return pixels

        if self._normalize == "imagenet":
            # I'm applying the same normalization my PyTorch notebook used.
            return (pixels - self._imagenet_mean) / self._imagenet_std

        return pixels
 

    def add_frame(self, frame):   #adding one raw frame frome phase 1 into my buffer and keep appending new frames as they come in
        processed = self._preprocess_frame(frame) 
        self._frames.append(processed)
        self._frames_added += 1

    def is_ready(self): # i am checking if i have enough frames to make a clip
        return len(self._frames) == self._clip_length #if the number of frames in the buffer is equal to the clip length, then i am ready to make a clip

    def buffer_size(self):  #to retirn how many frames that are currently stored
        return len(self._frames)

    def frames_added_total(self): # i am counting total frames recived since start of the program
        return self._frames_added

    def should_emit_clip(self): # i am checking if it is time to send a new clip to the model
        if not self.is_ready():
            return False
        return self._frames_added % self._stride == 0

    def get_clip(self): # i am stacking the 16 frames into a numpy array and into a a clip tensor
        if not self.is_ready():
            return None
        clip = np.stack(list(self._frames), axis=0) #Im turning the deque into a list, then stacking along a new axis
        return clip

