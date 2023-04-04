import time
import json
import numpy as np
import carla
from carla import Transform, Location, Rotation

"""
A class that spawns and unspawns hazards provided in the parameters file according to the location of the ego vehicle.
"""
class HazardGenerator():
    def __init__(self, client, vehicle, blueprint_library, params, log_path):
        self.client = client
        self.world = client.get_world()
        self.vehicle = vehicle
        self.blueprint_library = blueprint_library
        self.params = params
        self.log_path = log_path

        self.proximity_buffer = 10

        self.library = params['hazards']
        self.hazard_actor_list = []

        self.current_hazard = None
        self.elapsed_time = 0

        self.start_time = time.time()
        self.upcoming_hazard = None
        self.active = False

        np.random.seed()
        self.cycle_hazard_order = np.random.choice(np.arange(len(self.library)), len(self.library), replace=False)
        print("Hazard order: {}".format([self.library[g][0]['id'] for g in self.cycle_hazard_order]))
        self.cycle_num = 0
        self.num_hazards_spawned = 0

    def start_cycle(self):
        """moves forward to the next hazard from the library"""
        self.cycle_num += 1
        self.activate_next_hazard()

    def activate_next_hazard(self):
        """sets the next hazard that can be triggered"""
        if self.cycle_num <= len(self.library):
            self.upcoming_hazard = self.library[self.cycle_hazard_order[self.cycle_num - 1]][0]
            self.active = True
        else:
            print("Can't activate next hazard because there isn't one.")

    def spawn_hazard(self):
        '''display a hazard.'''
        self.current_hazard = self.upcoming_hazard
        blueprint = self.blueprint_library.filter((self.upcoming_hazard["blueprint_id"]).lower())[0]
        hazard_loc = Location(x=self.upcoming_hazard['location'][0], y=self.upcoming_hazard['location'][1], z=self.upcoming_hazard['location'][2])
        hazard_rot = Rotation(pitch=self.upcoming_hazard['rotation'][0], yaw=self.upcoming_hazard['rotation'][1], roll=self.upcoming_hazard['rotation'][2])
        spawned_hazard = self.world.spawn_actor(blueprint, Transform(hazard_loc, hazard_rot)) # , attach_to=self.vehicle
        self.hazard_actor_list.append(spawned_hazard)
        print("Spawned hazard: {}.".format(self.upcoming_hazard["id"]))
        self.upcoming_hazard = None
        self.num_hazards_spawned += 1
        return

    def destroy_hazard(self):
        '''destroy the current hazard'''
        print("Destroyed hazard: {}.".format(self.current_hazard["id"]))
        self.current_hazard = None
        self.client.apply_batch([carla.command.DestroyActor(x) for x in self.hazard_actor_list])
        self.active = False
        return

    def update(self, current_location):
        '''advance one time step'''
        self.elapsed_time += 1

        if self.cycle_num > 0 and self.active and self.upcoming_hazard is not None:
            # check if vehicle is at (or near within a certain buffer) the trigger point
            distance = abs(current_location.x - self.upcoming_hazard['trigger_point'][0]) + abs(current_location.y - self.upcoming_hazard['trigger_point'][1]) + abs(current_location.z - self.upcoming_hazard['trigger_point'][2]) 
            if distance < self.proximity_buffer:
                self.client.start_recorder(r"{}\cycle={}_hazard_id={}.log".format(self.log_path, self.cycle_num, self.upcoming_hazard["id"]))
                # print("started recording to {}".format(r"{}\cycle={}_hazard_id={}.log".format(self.log_path, self.cycle_num, self.upcoming_hazard["id"])))
                self.spawn_hazard()
        elif self.active:
            # check if vehicle is at (or near within a certain buffer) the trigger point
            distance = abs(current_location.x - self.current_hazard['stop_point'][0]) + abs(current_location.y - self.current_hazard['stop_point'][1]) + abs(current_location.z - self.current_hazard['stop_point'][2]) 
            if distance < self.proximity_buffer:
                self.destroy_hazard()
                self.client.stop_recorder()



        

