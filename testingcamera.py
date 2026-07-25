import logging
from src.phase1.opencv_camera import OpenCVCamera

logging.basicConfig(level=logging.INFO)
camera = OpenCVCamera(source=0)

if camera.open():
    ret, frame = camera.read()
    if ret:
        print("Success! I got a frame. Shape:", frame.shape)

    else:
        print("I opened the camera but could not read a frame.")
    camera.release()
else:
        print("I cant opend the camera")
