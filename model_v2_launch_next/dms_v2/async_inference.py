#This is my Phase 4 Async Inference. I want to run my Swin model on clips so the camera doesnt have to wait for the model to finish processing ech frame

import logging
import threading
import time
from collections import deque

logger = logging.getLogger(__name__)

class AsyncInference:
    def __init__(self, engine, max_queue=5): #i am initializing my AsynInference class with my inference engine and a max queue size of 5
        self._engine = engine 
        self._clip_queue = deque(maxlen=max_queue) #i am using a dqeue to store my clips
        self._result_queue = deque(maxlen=max_queue) #i am using a deque to store my results
        self._lock = threading.Lock() #i am using a loxk to synchroize acecess to my queues
        self._running = False #i am tracking if my inference is running
        self._thread = None #i am tracking my inference thread
    

    def start(self): #i am startging my inferecne thread
        self._running = True  #i am setting my running flag to True
        #now i want to create a daemon thread that will run in the background and doesnt block the msin camera loop
        self._thread = threading.Thread(target=self._inference_loop, daemon = True)
        self._thread.start()
        logger.info("I started my async inference thread")


    def stop(self): #i am stopping my inference thread
        self._running = False #i am asking the loop to stop running
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None
        logger.info("I stopped async inference thread")


    def submit_clip(self, clip): # Now i want to submit a new clip to the inference thread
        with self._lock:
            self._clip_queue.append(clip)


    def get_latest_result(self): #i am getting the latest result from the predictions or None if not avaialable
        with self._lock:
            if not self._result_queue:
                return None
            return self._result_queue[-1]


    def _inference_loop(self): #this is the main loop that will run in the background
        while self._running:  #this should run unitl the running flag is false
            clip = None
            with self._lock: #using lock to synchronize access to the queues
                if self._clip_queue:
                    clip = self._clip_queue.popleft() #i am getting the lastest clip from the queue
            if clip is None:
                time.sleep(0.01) #i am sleeping for a short time to avoid busy waiting
                continue
            start = time.monotonic() #tracking the start time of the inference
            probs = self._engine.predict(clip) #running the inference on rhe clip
            elapsed_ms = (time.monotonic() - start) * 1000 #calculating the elapses time in milliseconds
            with self._lock:
                self._result_queue.append({
                    "probabilities": probs,
                    "inference_time_ms": elapsed_ms,
                })


           
                    