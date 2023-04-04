# The algorithm used for distraction detection is based on AttenD
# ref:
# Katja Kircher and Christer Ahlström. 2013. The Driver Distraction Detection Algorithm AttenD.
# In Driver Distraction and Inattention: Advances in Research and Countermeasures, Michael Regan, Trent Victor, and John Lee (Eds.).
# Vol. 1. CRC Press, London, 327–348. http://ebookcentral.proquest.com/lib/delft/detail.action?docID=109410

import time
from collections import deque
import numpy as np

from src.DistractionAlarm import Alarm

"""
Keeps track of the distraction state of the driver.
"""
class DistractionMonitor():
    def __init__(self, client, vehicle, params, icon=None, icon_location=None, alarm_type="baseline"):
        self.start_time = time.time()
        self.alarm_type = alarm_type

        self.max_buffer = 60 # timesteps (timestep = approx 1/30th of a second)
        self.max_escalation_buffer = 30

        # the replete buffer is a small buffer that ensures that very short glances to the road do not mean driver is undistracted yet
        self.max_replete_buffer = 1 # number of timesteps before buffer starts to fill up again

        # the number of esalation levels can only be the number of given alarm sound files
        self.max_escalation=0 if alarm_type not in ['escalating', 'non-escalating'] else len(params[alarm_type]['sound_files']) - 1
        self.alarm = Alarm(client, vehicle, icon=icon, icon_location=icon_location,  alarm_type=self.alarm_type, escalation_levels=self.max_escalation, sound_paths=params[alarm_type]['sound_files'])

        self.escalation_level = 0
        self.buffer = self.max_buffer 
        self.escalation_buffer = self.max_escalation_buffer
        self.replete_buffer = self.max_replete_buffer

        # driver state
        self.driver_state = {"distracted": False}

    def update(self, gaze_target):
        """updates the monitor with one time step of gaze information"""
        if gaze_target is not None and "EyesOnRoad" in gaze_target:
            if self.replete_buffer == 0:
                # the buffer starts filling up again
                if self.buffer < self.max_buffer:
                    self.buffer += 1
                if self.escalation_buffer == self.max_escalation_buffer:
                    self.escalation_level = 0 # reset the escalation buffer if they are undistracted for long enough
                if self.escalation_buffer < self.max_escalation_buffer:
                    self.escalation_buffer += 1
                self.driver_state['distracted'] = False
            else:
                self.replete_buffer -= 1
        else:
            # the buffer depletes when they are not looking at the relevant area
            if self.buffer > 0:
                self.buffer -= 1
            self.replete_buffer = self.max_replete_buffer

        # when the buffer is empty, they are distraction
        if self.buffer == 0:
            self.driver_state['distracted'] = True
        
        if self.is_distracted():
            # sound the alarm
            self.alarm.play(self.escalation_level)

            # start depleting the escalation buffer because they are distracted
            if self.is_distracted and self.escalation_buffer > 0:
                self.escalation_buffer -= 1

            # escalate when the escalation buffer runs out
            if self.escalation_buffer == 0 and self.alarm_type=="escalating" and self.escalation_level < self.max_escalation:
                self.escalation_level += 1
        else:
            # force stop the alarm when they are no longer distracted
            self.alarm.stop()

    def is_distracted(self):
        """returns the distracted state of the driver"""
        return self.driver_state["distracted"]

