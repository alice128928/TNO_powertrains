# ev_request.py
# ----------------
# This module reads electric vehicle (EV) configuration data from a YAML file and generates:
# - EV names and IDs
# - Battery capacities
# - Charging port powers
# - Availability schedules over time
# - Empty arrays for battery SoC and vehicle status (for simulation)
#
# Inputs:
# - YAML configuration file: contains ID, battery capacity, arrival/departure times, charging port power rating
#
# Outputs:
# - car_names: list of EV IDs
# - battery_caps: list of battery capacities [Wh]
# - charging_ports: list of charging power limits [W]
# - availability_arrays: list of availability status (2 = away, 3 = available) for each time step
# - battery_capacity_arrays: list of zero-initialized arrays to hold simulated battery state [Wh]
# - status_cars: list of zero-initialized arrays to track each EV's simulation status (charging,not charging)

import numpy as np
import yaml

# Simulation time configuration
hours_per_day = 24
num_days = 20
time_steps = hours_per_day * num_days  # total time steps in the simulation

def time_to_index(hour_str):
    """
    Convert a time string in 'HH:MM' format or integer to an hour index (0-23).

    Parameters:
    - hour_str (str or int): Time value as string (e.g. '08:00') or integer (e.g. 8)

    Returns:
    - int: Hour index
    """
    if isinstance(hour_str, int):
        return hour_str
    elif ":" in hour_str:
        h, m = map(int, hour_str.split(":"))
        return h + m // 60
    else:
        return int(hour_str)

def ev_generate_from_config(config_path='configurations/ev_config.yaml'):
    """
    Reads EV configuration from YAML and initializes simulation structures.

    Parameters:
    - config_path (str): Path to YAML configuration file

    Returns:
    - car_names (list[str]): List of car identifiers
    - battery_caps (list[float]): Battery capacities in kWh
    - charging_ports (list[float]): Charging port limits in W
    - availability_arrays (list[np.ndarray]): Availability per hour (2 = away, 3 = at home)
    - battery_capacity_arrays (list[np.ndarray]): Zero-initialized arrays to store SoC per hour
    - status_cars (list[np.ndarray]): Zero-initialized status arrays per car
    """
    car_names = []
    battery_caps = []
    charging_ports = []
    availability_arrays = []
    battery_capacity_arrays = []
    status_cars = []

    # Load YAML config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    cars = config.get("InitializationSettings", {}).get("cars", [])
    #loading characteristics of each car
    for car in cars:
        car_id = car["id"]
        battery_capacity = car["battery_capacity"]
        arrival_time = time_to_index(car["arrival_time"])
        departure_time = time_to_index(car["departure_time"])
        charging_port = car["charging_port"]

        #the components at each index corresponds to the same car. for example at index 1,
        #we can find the name of the car, its battery capacity and the charging port it belongs to
        car_names.append(car_id)
        battery_caps.append(battery_capacity)
        charging_ports.append(charging_port)

        # Create daily availability array (2 = not home, 3 = home and available for charging)
        daily_avail = np.full(hours_per_day, 2, dtype=int)
        if arrival_time < departure_time:
            # Normal daytime availability
            daily_avail[arrival_time:departure_time] = 3
        else:
            # Overnight availability
            daily_avail[arrival_time:] = 3
            daily_avail[:departure_time] = 3

        # Repeat daily pattern for full simulation horizon
        full_avail = np.tile(daily_avail, num_days)
        availability_arrays.append(full_avail)

        # Initialize empty arrays for simulation (e.g., SoC, status over time)
        battery_capacity_arrays.append(np.zeros(time_steps))  # SoC in Wh
        status_cars.append(np.zeros(time_steps))  # could represent charging status

    return car_names, battery_caps, charging_ports, availability_arrays, battery_capacity_arrays, status_cars
