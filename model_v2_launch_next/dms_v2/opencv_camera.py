# Here i am using OpenCV library to talk to my camera
import logging
import cv2
import numpy as np 

logger = logging.getLogger(__name__)

class OpenCVCamera:
    "I am wrapping the OpenCV camera to make it easier to use"
    def __init__(self, source=0):
        #i am storing the source of the camera id as 0 as in my config file
        self._source = source
        self._cap = None



    def open(self):
        #asking openCV to open the camera for me
        self._cap =cv2.VideoCapture(self._source)
        if not self._cap.isOpened():
            logger.error("I coulld not open camera source: %s", self._source)
            return False
        logger.info("I have opened the camera source: %s", self._source)
        return True

    def read(self):
        if self._cap is None or not self._cap.isOpened():
            return False, None

        ret, frame = self._cap.read()
        if not ret or frame is None:
            return False, None
        return True, frame



    def release(self):
        if self._cap is not None:
            self._cap.release()
            self._cap = None
            logger.info("I havve released the camera")

    def is_opened(self):
        return self._cap is not None and self._cap.isOpened()

    def reconnect(self):  #this is for my watchdog in config file
        #i am closing the old connecion and ttrying again
        logger.warning("I am attempting to reconnect the camera...")
        self.release()
        return self.open()
