# This will run the experiment, pulling the parameters from 'pilot_parameters.json'

import os
import time
import argparse
import json
import carla
import configparser
import subprocess
from datetime import datetime
from pathlib import Path

from src import DistractionMonitor, NDRT, DReyeVR_agent, HazardGenerator
from src.utils import simulator_utils as utils
from src.utils import DReyeVR_utils

parameters_path = "experimental_parameters\\exp_parameters.json"

def parse_args(doc):
    argparser = argparse.ArgumentParser(description=doc)
    argparser.add_argument(
        "-c", "--condition", metavar="C", default="familiarization", help="Experimental condition"
    )
    argparser.add_argument(
        "-t", "--disable_takeover", metavar="T", default=False, help="Disable takeover?"
    )
    return argparser.parse_args()

def main():
    # This will open the packaged Carla simulator
    subprocess.Popen("PATH_TO_CARLA/Build/UE4Carla/0.9.13-dirty/WindowsNoEditor/CarlaUE4.exe -vr", shell=True)
    time.sleep(10)

    # Parse any args from command prompt
    args = parse_args(__doc__)
    exp_condition = args.condition

    # Load parameters from file
    with open(parameters_path, 'r') as file:
        params = json.load(file)
        print("Loaded parameters from {}".format(parameters_path))

    # Connect to Carla
    client = carla.Client(params['host'], params['port'])
    client.set_timeout(10.0)

    # Load the map
    world = client.load_world(params['map_name'])
    blueprint_library = world.get_blueprint_library()
    map = world.get_map()

    participantID = input("Enter the participant id: ")
    random_seed = input("Enter the random seed: ")
    # name file to save data to
    save_dir = r"{}\participant_ID={}".format(params["dir_to_save"], participantID)
    if not Path(save_dir).is_dir():
        os.mkdir(save_dir) # make the root directory to save to
    save_dir += r"\{}".format(exp_condition)
    if not Path(save_dir).is_dir():
        os.mkdir(save_dir) # make the new directory to save to
    else:
        print("ERROR: ID/CONDITION DIRECTORY ALREADY EXISTS. Are the participant ID and condition unique?")
        quit()
    file_dir = r"{}\data_log.txt".format(save_dir)
    file_to_save = open(file_dir, "a") 

    # see: https://carla.readthedocs.io/en/latest/python_api/ for carla.LaneType options
    # # Get waypoints
    waypoints = []
    waypoint_list = params['waypoint_coordinates']
    for loc in waypoint_list:
        wp = map.get_waypoint(carla.Location(x=loc[0], y=loc[1], z=loc[2]), project_to_road=True, lane_type=(carla.LaneType.Driving))
        waypoints.append(wp)

    settings = world.get_settings()
    settings.synchronous_mode = True # Enables synchronous mode
    settings.fixed_delta_seconds = 0.03 # Should be set to 1/fps
    world.apply_settings(settings)

    # Get ego vehicle Actor
    ego_vehicle = DReyeVR_utils.find_ego_vehicle(world)
    agent = DReyeVR_agent.DReyeVRAgent(vehicle=ego_vehicle)

    traffic_manager = client.get_trafficmanager(params['tm_port'])
    traffic_manager.set_global_distance_to_leading_vehicle(params['distance_to_leading_vehicle'])
    traffic_manager.set_synchronous_mode(True)
    traffic_manager.set_random_device_seed(random_seed)

    # move to better starting location
    start_location_proxy = carla.Location(x=params["starting_location"][0], y=params["starting_location"][1], z=params["starting_location"][2])
    start_wp = map.get_waypoint(start_location_proxy, project_to_road=True, lane_type=(carla.LaneType.Driving))
    start_location = start_wp.transform.location
    ego_vehicle.set_transform(carla.Transform(start_location, carla.Rotation(pitch=params["starting_rotation"][0], yaw=params["starting_rotation"][1], roll=params["starting_rotation"][2])))
    print("Moved ego vehicle to: {}".format(start_location))
    NDRT_target_phrase_icon = blueprint_library.filter(("NDRTTarget").lower())[0]
    NDRT_target_phrase_location = carla.Transform(carla.Location(x=0.2648, y=0.7097, z=0.8732), carla.Rotation(pitch=0.0005, yaw=-179.9996, roll=89.9999))
    world.spawn_actor(NDRT_target_phrase_icon, NDRT_target_phrase_location, attach_to=ego_vehicle)
    
    print("**IMPORTANT**: Click simulator screen to make it the active window. You have 3 seconds.")
    print("3...")
    time.sleep(1)
    print("2...")
    time.sleep(1) 
    print("1...")
    time.sleep(1) 

    # Generate other traffic
    utils.spawn_other_vehicles(client, params, world, traffic_manager, random_seed)
    traffic_manager.global_percentage_speed_difference(-25)

    traffic_lights = utils.get_traffic_lights(world)
    client.apply_batch([carla.command.DestroyActor(x) for x in traffic_lights])
    print("destroyed traffic lights")

    # Initiate distraction monitor
    eyes_icon = blueprint_library.filter(("static.prop.HMI_EyesOnRoad").lower())[0]
    icon_location = carla.Transform(carla.Location(x=params["icon_location"][0], y=params["icon_location"][1], z=params["icon_location"][2]),
                                    carla.Rotation(pitch=params["icon_rotation"][0], yaw=params["icon_rotation"][1], roll=params["icon_rotation"][2]))
    monitor = DistractionMonitor.DistractionMonitor(client, ego_vehicle, params, icon=eyes_icon, icon_location=icon_location, alarm_type=exp_condition)

    # Initialize NDRT scheduler
    NDRT_library = blueprint_library.filter(("NDRT_*").lower())
    NDRT_scheduler = NDRT.NDRTScheduler(client=client, vehicle=ego_vehicle, params=params, NDRT_library=NDRT_library)

    # Initialize hazard generator
    hazard_generator = HazardGenerator.HazardGenerator(client=client, vehicle=ego_vehicle, blueprint_library=blueprint_library, params=params, log_path=save_dir)

    file_to_save.write("[")
    def log_sensor_data(data):
        """Updates the sensor and prints all the sensor output and the below variables to the log file."""
        current_location = ego_vehicle.get_location()
        sensor.update(data)
        if elapsed_timesteps:
            file_to_save.write(",\n") # don't add the last comma if it's the first entry
        file_to_save.write('{}\n'.format("{"))
        file_to_save.write('"clock_time": "{}",\n'.format(datetime.utcnow().strftime("%Y%m%d-%H:%M:%S.%f")))
        file_to_save.write('"participant_id": "{}",\n'.format(participantID))
        file_to_save.write('"experimental_condition": "{}",\n'.format(exp_condition))
        file_to_save.write('"random_seed": "{}",\n'.format(random_seed))
        file_to_save.write('"ego_vehicle_location": "{}",\n'.format(current_location))
        for d in sensor.data.keys():
            file_to_save.write('"{}":"{}",\n'.format(d, sensor.data[d]))
        file_to_save.write('"current_cycle": "{}",\n'.format(hazard_generator.cycle_num))
        file_to_save.write('"NDRT_current_ID": "{}",\n'.format(NDRT_scheduler.current_task_id))
        file_to_save.write('"driver_distracted": "{}",\n'.format(monitor.is_distracted()))
        file_to_save.write('"alarm_active": "{}",\n'.format(monitor.alarm.is_level))
        # should also write if the alarm is going
        if hazard_generator.current_hazard is not None:
            file_to_save.write('"current_hazard": "{}"\n'.format(hazard_generator.current_hazard["id"]))
        else:
            file_to_save.write('"current_hazard": "{}"\n'.format(None))
        file_to_save.write("{}".format("}"))
        monitor.update(sensor.data['focus_actor_name']) # need to give it the current gaze target every step
        if exp_condition in ['baseline','escalating', 'non-escalating']:
            hazard_generator.update(current_location) # need to give it the vehicle location every step
    
    # Sensor
    sensor = DReyeVR_utils.DReyeVRSensor(world)
    # subscribe to DReyeVR sensor and use the above function to write to file
    sensor.ego_sensor.listen(log_sensor_data)

    elapsed_timesteps = 0
    waypoint_index = 0
    hazard_generator.start_cycle()
    try:
        while hazard_generator.cycle_num <= params["number_of_driving_cycles"]:
            world.tick()

            if elapsed_timesteps == 0 or agent.done():
                print("next destination {}".format(waypoint_list[waypoint_index]))
                plan = agent.trace_route(map.get_waypoint(ego_vehicle.get_location(), project_to_road=True, lane_type=(carla.LaneType.Driving)), waypoints[waypoint_index])
                agent.set_global_plan(plan, stop_waypoint_creation=True, clean_queue=True)
                agent.set_target_speed(90)
                if waypoint_index < len(waypoint_list) - 1:
                    waypoint_index += 1
                else:
                    print("starting new cycle {}".format(hazard_generator.cycle_num + 1))
                    hazard_generator.start_cycle()
                    traffic_manager.set_random_device_seed(random_seed+hazard_generator.cycle_num)
                    waypoint_index = 0
            ego_vehicle.apply_control(agent.run_step())
            NDRT_scheduler.update()
            elapsed_timesteps += 1
    except KeyboardInterrupt:
        pass
    file_to_save.write("]")
    file_to_save.close()

if __name__ == '__main__':
    try:
        main()
    finally:
        print('\ndone.')
        # Closes the Carla window
        subprocess.call("taskkill /f /im CarlaUE4-Win64-Shipping.exe", shell=True)