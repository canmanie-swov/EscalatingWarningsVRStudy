import time
import json
import numpy as np
import carla
from carla import Transform, Location, Rotation

class NDRTScheduler():
    def __init__(self, client, vehicle, params, NDRT_library):
        self.client = client
        self.world = client.get_world()
        self.vehicle = vehicle
        self.period = params['NDRT_period'] # value in timesteps that determines the NDRT cycle length

        self.library = NDRT_library
        self.NDRT_actor_list = []

        self.current_task_id = None
        self.elapsed_time = 0

        self.blank_time = params['NDRT_blank_time'] # number of timesteps that a blank screen will be visible
        self.blank_screen_buffer = self.blank_time
        self.blank = False

        self.start_time = time.time()
        self.display_random_task()

    def display_random_task(self):
        '''pick a random task and display it'''
        self.current_task_id = np.random.randint(len(self.library))
        icon_location = Transform(Location(x=0.8192, y=-0.0052, z=0.7370), Rotation(pitch=0, yaw=138.6, roll=75))
        icon_NDRT = self.world.spawn_actor(self.library[self.current_task_id], icon_location, attach_to=self.vehicle)
        self.NDRT_actor_list.append(icon_NDRT)
        return

    def undisplay_current_task(self):
        '''make the current task invisible'''
        self.current_task_id = None
        self.client.apply_batch([carla.command.DestroyActor(x) for x in self.NDRT_actor_list])
        return

    def update(self):
        '''advance one time step'''
        self.elapsed_time += 1

        if self.elapsed_time % self.period == 0:
            # un-display the current task
            self.undisplay_current_task()
            self.blank = True

        if self.blank:
            if self.blank_screen_buffer > 0:
                self.blank_screen_buffer -= 1
            else:
                # display the next task
                self.display_random_task()
                self.blank_screen_buffer = self.blank_time
                self.blank = False

