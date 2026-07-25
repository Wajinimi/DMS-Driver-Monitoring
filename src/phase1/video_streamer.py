# Now this is my Phase 1 which is responsbiel for talking to the camera and getting the videos
import logging
import time
import cv2
import numpy as np
from .opencv_camera import OpenCVCamera
import threading
from collections import deque

logger = logging.getLogger(__name__)

class VideoStreamer:
    def __init__(self, target_fps=15, frame_width = 640, frame_height = 480, watchdog_timeout_ms = 2000):
        self._camera = OpenCVCamera()
        self._target_fps = target_fps
        self._interval = 1.0 / target_fps #this is the ms between frames, value will come from config file later
        self._frame_width = frame_width
        self._frame_height = frame_height
        self._running = False
        self._frame_queue = deque(maxlen=30)
        self._queue_lock = threading.Lock()
        self._thread = None
        self._watchdog_timeout_s = watchdog_timeout_ms / 1000.0
        self._last_frame_time = time.monotonic()




#MY STARTING CODE BLOCK
    def start(self): #i defined a method called start which is the intrcution i use to begin the video stream
        if not self._camera.open(): #i ma opening the camera, if it fails, i stopp here
           return False #this returns Flase
        self._running = True #this sets the flag to True that it is running
        self._last_frame_time = time.monotonic()
        self._thread = threading.Thread(target=self._capture_loop, daemon = True) #creating a background thread that will run the cappture loop for me
        self._thread.start() #then i am startinf the thread so it can begin grabbing frames
        logger.info("i started the video streamer at %s FPS", self._target_fps) #this help me log the message
        return True

#MY STOPPING CODE BLOCK
    def stop(self):  #this method is stop, which i would use to stop the video streamer
        self._running = False #this sets the flag to false so the loop can stop
        if self._thread is not None: # i am checking whether i created a background thread
            self._thread.join(timeout=3.0) #i will wait for the thread to finish cleanly, but only for 3 seconds
            self._thread = None #Then i am clearing the thread reference so i know i am not using it anymore
        self._camera.release() #i am releasing the camera so it is no longer in use
        logger.info("I havee stopped the video streamer")
        

#THIS METHOD IS TO ENSURE THAT THW CAMERA CAPTURE DOES NOT BLOCK EVERYTHING OTHER
    def _capture_loop(self):  #i defined the method called _capture_loop
        next_sample_at =time.monotonic() #i set the first time i want to grab a frame

        while self._running:  # i want to keep looping as long as the streamer is running
            ret, frame = self._camera.read()  #i am reading the frame from the camerz
            if not ret or frame is None:  #if the frame is not read or is None,i will sleep for 10ms and continue the loop agIN
                self._handle_camera_fault()
                time.sleep(0.01)
                continue

            now = time.monotonic()  #checking the current time whethet it is time to sample again
            self._last_frame_time = now
            if now >= next_sample_at: #if it is time to sample again, i will procees the frame 
                processed = self._process_frame(frame)  #i am processing the frame to save my RAM before the AI pipeline sees it
                with self._queue_lock:  # i am lokcing my queue so no 2 parts of the program try to change it at the same time
                    self._frame_queue.append(processed) #then i am appending ghe processed frames to the queue
                next_sample_at += self._interval  #i am moving the next sample time forward by one frame interval


    #THIS METHOD IS TO LOG ERROR IF IT DOESNT REEIVCE GOOD FRAMES AFTER 2 SECONDS
    def _handle_camera_fault(self):  #defining method to check if the camera has stopped giving good frames
        elapsed = time.monotonic() - self._last_frame_time #calculating how long it has been since i last reviced a good frame
        if elapsed < self._watchdog_timeout_s: # checking whethet the time is still withing the allowed timeout window
            return

        logger.error("Camera watchdog: I have noot recieved a frame for %.1f seconds", elapsed)
        if self._camera.reconnect(): #trying to reconnect to the camera
            self._last_frame_time = time.monotonic() #if reconnection is successful, thhen i am restting the last-frame timer to now
            logger.info("i reconnected to the camera")
        else:
                logger.error("i failed to reconnect to the camera again") 
                time.sleep(1.0) # waiting for 1 seconf before trying again so i dont retry too fast





    def get_frame(self): #i want to give the latest frame to Phase 2 or my test script
        with self._queue_lock: #I am lokcing the queue agan before reading from it
            if not self._frame_queue:  # i am checking if there are no frames avaialable
                return None  #then help retuen nothing if there is nothing available to retuen
            return self._frame_queue[-1].copy() #i retuen the most recent frame but i copy it so the caller cannot accidentally change the queue data


    def consume_frame(self): #i am taking one frame out of the queue so phase 2 can use it, FIFO style
        with self._queue_lock:
            if not self._frame_queue:
                return None
            return self._frame_queue.popleft()

    
    def get_queue_size(self):  #this method will tell me how many frames are currently waiting in the queue
        with self._queue_lock:  #i am locking the queue before checking its size
            return len(self._frame_queue)  #rthen i am returning the number of frames currently stored

        
    def _process_frame(self, frame):
        # I am resizing to save RAM before the AI pipeline sees this frame.
        return cv2.resize(
            frame,
            (self._frame_width, self._frame_height),
            interpolation=cv2.INTER_AREA,
        )



    def run_once(self): #this is the method that will show frames to me while the streamer is running
        frames_shown = 0 #i am creating a counter and start it at 0 this will help keep track how many frames i have displayed

        while self._running: #keep showing the frames as ling as the  streamer is still running
            frame = self.get_frame() # i am asking for the latest frame from the queue
            if frame is not None:  #checking whether i actually recieved a frame
                cv2.imshow("DMS Phase 1", frame) #i open a window and display that frame so i can see the video
                frames_shown += 1 #i am increasing my counter by 1 because i have displayed 1 frame

            if cv2.waitKey(1) & 0xFF == ord("q"): #this will help the pogram check if i pressed q so it can quit
                break

        cv2.destroyAllWindows() #i am closing the window when i am done
        logger.info("I showeed %d frames total", frames_shown)

    