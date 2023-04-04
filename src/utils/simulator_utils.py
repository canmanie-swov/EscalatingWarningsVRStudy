## These are some of the functions that are useful when developing experiments in the DReyeVR+Carla VR simulator.
import time

import carla
import numpy as np
import DReyeVR_utils

def print_sensor_data(data, sensor):
    """Updates the sensor and prints all the sensor output to the console."""
    sensor.update(data)
    print(sensor.data) 

def set_autopilot_on_ego(world, traffic_manager):
    """Gets the ego vehicle and sets autopilot on it."""
    # Set autopilot
    ego_vehicle = DReyeVR_utils.find_ego_vehicle(world)
    if ego_vehicle is not None:
        ego_vehicle.set_autopilot(True, traffic_manager.get_port())
    print("Successfully set autopilot on ego vehicle")
    return ego_vehicle

def spawn_other_vehicles(client, params, world, traffic_manager, random_seed, force_num=None):
    """Spawns a number of vehicles into random spawn points on the world map and sets them to autopilot.

    Keyword arguments:
    client -- the Carla client
    max_vehicles -- the max number of vehicles to spawn (> 0)
    world -- the Carla world/map
    traffic_manager - the Carla traffic_manager
    """
    if force_num is None:
        max_vehicles = params["number_of_other_vehicles"]
    else:
        max_vehicles = force_num
    np.random.seed(random_seed)
    spawn_points = world.get_map().get_spawn_points()

    # if we don't shuffle, we end up generating all the traffic in near each other
    np.random.shuffle(spawn_points)
    
    blueprints = world.get_blueprint_library().filter("vehicle.*")
    blueprints = [x for x in blueprints if x.has_attribute('number_of_wheels') and int(x.get_attribute('number_of_wheels')) == 4]
    blueprints = [x for x in blueprints if not x.id.endswith('firetruck')]
    blueprints = [x for x in blueprints if not x.id.endswith('ambulance')]
    blueprints = sorted(blueprints, key=lambda bp: bp.id)

    SpawnActor = carla.command.SpawnActor
    SetAutopilot = carla.command.SetAutopilot
    FutureActor = carla.command.FutureActor

    vehicle_list = []
    batch = []
    for n, transform in enumerate(spawn_points):
        if n >= max_vehicles:
            break
        blueprint = np.random.choice(blueprints)
        if blueprint.has_attribute("color"):
            color = np.random.choice(blueprint.get_attribute("color").recommended_values)
            blueprint.set_attribute("color", color)
        if blueprint.has_attribute("driver_id"):
            driver_id = np.random.choice(
                blueprint.get_attribute("driver_id").recommended_values
            )
            blueprint.set_attribute("driver_id", driver_id)
        try:
            blueprint.set_attribute("role_name", "autopilot")
        except IndexError:
            pass

        batch.append(
            SpawnActor(blueprint, transform).then(
                SetAutopilot(FutureActor, True, traffic_manager.get_port())
            )
        )
    synchronous_master = False
    for response in client.apply_batch_sync(batch, synchronous_master):
        if response.error:
            print(f"ERROR: {response.error}")
        else:
            vehicle_list.append(response.actor_id)
    print(f"successfully spawned {len(vehicle_list)} vehicles")
    return vehicle_list

def _split_actors(world):
    actors = world.get_actors()
    vehicles = []
    traffic_lights = []
    speed_limits = []
    walkers = []
    stops = []
    static_obstacles = []
    for actor in actors:
        if 'vehicle' in actor.type_id:
            vehicles.append(actor)
        elif 'traffic_light' in actor.type_id:
            traffic_lights.append(actor)
        elif 'speed_limit' in actor.type_id:
            speed_limits.append(actor)
        elif 'walker' in actor.type_id:
            walkers.append(actor)
        elif 'stop' in actor.type_id:
            stops.append(actor)
        elif 'static.prop' in actor.type_id:
            static_obstacles.append(actor)
    return (vehicles, traffic_lights, speed_limits, walkers, stops, static_obstacles)

def get_traffic_lights(world):
    actors = world.get_actors()
    traffic_lights = []
    for actor in actors:
        if 'traffic_light' in actor.type_id:
            traffic_lights.append(actor)
    return traffic_lights