# This is my Phase 5. I want to filter out the raw AI preedictions before insights or analytics or alerts
import logging
import time

logger = logging.getLogger(__name__)

class StateManager : #i am building a state manager class that will help me manage the state of the driver 
    def __init__(self, default_threshold = 0.50, exit_threshold = 0.35, normal_class = "normal_driving", smoothing_windows = None) :
        self._default_threshold = default_threshold
        self._exit_threshold = exit_threshold
        self._normal_class = normal_class
        self._current_activity = normal_class
        self._smoothing_windows = smoothing_windows or {}
        self._history = []  # i am storing the last several filtered predictions so that i can check for consistency
        self._activity_start_time = None
        logger.info("I started the State Managger") 


    #i want to find the activity with the highest probability orr confidence score
    def _get_top_class(self, probabilities): #this function will take a dictionary of class probabilities and return the activity with the highest confidence score
        top_class = max(probabilities, key = probabilities.get)
        top_prob = probabilities[top_class]
        return top_class, top_prob


    #i want to apply confidence thresholds, if the top class is below 50%, i will say it is normal drivinng
    def filter_threshold(self, probabilities):
        top_class, top_prob = self._get_top_class(probabilities)
        if top_prob < self._default_threshold:
            return self._normal_class, top_prob
        return top_class, top_prob

    #i want to process one prediction from phase4, apply thresholds, and then check if enough recent predictions agree
    #if they do, i wiwll switch state, and also start the Activity Duration Timer
    def update(self, probabilities): #this function will take a dictionary of probabilities and return the activity, confidence and duration
        filtered, conf = self.filter_threshold(probabilities) #i am filtering the predictions to get the top class and conffidence score
        self._history.append(filtered) #i am appending the filtered prediction to the history

        window = int(self._smoothing_windows.get(filtered, 3)) #i am gettting the smoothing window for the current activity and defaulting to 3
        recent = self._history[-window:] #getting the recent predictions

        if len(recent) >= window and all(x == filtered for x in recent): #checking if the recent preidictions are all the same as the filtered prediction
            if filtered != self._current_activity: #checking if the filtered prediction is diferent from thee current activitiy
                self._current_activity = filtered #updating the current activity
                self._activity_start_time = time.time() #also updating the activity start time
                logger.info("I switched to '%s' at %s", filtered, self._activity_start_time)

        duration = 0.0 #i am setting the duration to 0.0
        if self._activity_start_time is not None: #i want to caclulate rhe duration of the current activity
            duration = time.time() - self._activity_start_time

        return self._activity_start_time, self._current_activity, conf, duration


