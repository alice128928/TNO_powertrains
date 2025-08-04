
# run_cosimulation.py
# -------------------
# This script performs the full setup and execution of an energy system co-simulation.
#
# 💡 Functionality:
# - Collects user inputs for wind turbines, solar panels, EVs, and system-level parameters
# - Saves configurations to YAML files
# - Loads and initializes models (wind, solar, EV, battery, controller, grid, pricing)
# - Executes time-step-based co-simulation using a Manager class
#
# 📂 Output:
# - YAML files in ./configurations/
# - Simulation managed via the cosim_framework.Manager

"""Run the co-simulation."""
from functools import partial
import yaml
import os
from datetime import datetime

from controller_ems import controller_multiple_cars
from cosim_framework import Manager, Model
from grid import electric_grid_function
from load_configurations import load_configurations
from price_market import give_price
from battery_storage import BatteryStorage
# --- Step 1: Input turbine data interactively ---1
turbines = []

print("Enter wind turbine data (type 'q' at any time to stop):\n")

while True:
    try:
        hub_height_input = input("Enter hub height (in meters): ")
        if hub_height_input.lower() == 'q':
            break
        hub_height = float(hub_height_input)

        power_input = input("Enter nominal power (in watts): ")
        if power_input.lower() == 'q':
            break
        nominal_power = float(power_input)

        number_input = input("Enter number of turbines of this type: ")
        if number_input.lower() == 'q':
            break
        number_of_turbines = int(number_input)

        turbines.append({
            "hub_height": hub_height,
            "nominal_power": nominal_power,
            "number_of_turbines": number_of_turbines
        })

        print("Turbine added!\n")

    except ValueError:
        print("Invalid input, please enter numeric values.\n")
        continue

# --- Step 1.5: Input solar panel data interactively ---
solar_panels = []

print("Enter solar panel data (type 'q' at any time to stop):\n")

while True:
    try:
        latitude_input = input("Enter latitude: ")
        if latitude_input.lower() == 'q':
            break
        latitude = float(latitude_input)

        longitude_input = input("Enter longitude: ")
        if longitude_input.lower() == 'q':
            break
        longitude = float(longitude_input)

        altitude_input = input("Enter altitude (in meters): ")
        if altitude_input.lower() == 'q':
            break
        altitude = int(altitude_input)

        tilt_input = input("Enter surface tilt (in degrees): ")
        if tilt_input.lower() == 'q':
            break
        surface_tilt = int(tilt_input)

        number_input = input("Enter number of panels: ")
        if number_input.lower() == 'q':
            break
        number_of_panels = int(number_input)

        solar_panels.append({
            "latitude": latitude,
            "longitude": longitude,
            "altitude": altitude,
            "surface_tilt": surface_tilt,
            "number_of_panels": number_of_panels
        })

        print("☀️  Solar panel configuration added!\n")

    except ValueError:
        print("Invalid input, please enter numeric values.\n")
        continue

# --- Step 1.6: Input EV data interactively ---
ev_cars = []

print("Enter EV data (type 'q' at any time to stop):\n")

while True:
    try:
        car_id = input("Enter car ID: ")
        if car_id.lower() == 'q':
            break

        battery_capacity = input("Enter battery capacity (in Wh): ")
        if battery_capacity.lower() == 'q':
            break
        battery_capacity = float(battery_capacity)

        port_energy_str = input("Enter the charging port value: ")
        if port_energy_str.lower() == 'q':
            break
        charging_port = float(port_energy_str)

        arrival_time_str = input("Enter arrival time (HH:MM): ")
        if arrival_time_str.lower() == 'q':
            break
        arrival_time = datetime.strptime(arrival_time_str, "%H:%M").strftime("%H:%M")

        departure_time_str = input("Enter departure time (HH:MM): ")
        if departure_time_str.lower() == 'q':
            break
        departure_time = datetime.strptime(departure_time_str, "%H:%M").strftime("%H:%M")

        ev_cars.append({
            "id": car_id,
            "battery_capacity": battery_capacity,
            "arrival_time": arrival_time,
            "departure_time": departure_time,
            "charging_port": charging_port
        })

        print("🚗 EV configuration added!\n")

    except ValueError:
        print("Invalid input. Time should be in HH:MM format and numbers must be valid.\n")
        continue

# --- Step 1.7: Input system configuration data interactively ---
config_array = []
print("Enter system-level configuration data (type 'q' at any time to stop):\n")


while True:
    try:
        storage_input = input("Enter battery storage capacity (in Wh): ")
        if storage_input.lower() == 'q':
            break
        storage_capacity = float(storage_input)

        grid_input = input("Enter grid capacity (in W): ")
        if grid_input.lower() == 'q':
            break
        grid_capacity = float(grid_input)

        money_input = input("Enter initial budget (in $): ")
        if money_input.lower() == 'q':
            break
        initial_money = float(money_input)

        max_price_input = input("Enter maximum price ($/kWh): ")
        if max_price_input.lower() == 'q':
            break
        price_high = float(max_price_input)

        min_price_input = input("Enter minimum price ($/kWh): ")
        if min_price_input.lower() == 'q':
            break
        price_low = float(min_price_input)

        config_array.append({
            "storage": storage_input,
            "grid_capacity": grid_input,
            "money_input": money_input,
            "max_price_input": max_price_input,
            "min_price_input": min_price_input
        })
        print("✅ System configuration added!\n")
        break

    except ValueError:
        print("Invalid input. Please enter numeric values.\n")
        continue


# --- Save configurations ---
wind_config_data = {
    "InitializationSettings": {
        "config_id": "config 1"
    },
    "wind_turbines": turbines
}

solar_config_data = {
    "InitializationSettings": {
        "config_id": "config 1"
    },
    "solar_panels": solar_panels
}

ev_config_data = {
    "InitializationSettings": {
        "config_id": "config 1",
        "cars": ev_cars
    }
}


controller_config_add = {
    "InitializationSettings": {
        "config_id": "config 1",
        "configs": config_array
    }
}

os.makedirs("configurations", exist_ok=True)

with open("configurations/turbine_config.yaml", "w") as f:
    yaml.dump(wind_config_data, f, default_flow_style=False)

with open("configurations/solar_config.yaml", "w") as f:
    yaml.dump(solar_config_data, f, default_flow_style=False)

with open("configurations/ev_config.yaml", "w") as f:
    yaml.dump(ev_config_data, f, default_flow_style=False)

with open("configurations/controller_add_config.yaml", "w") as f:
    yaml.dump(controller_config_add, f, default_flow_style=False)


# --- Load and run simulation ---
configurations_folder_path = 'configurations'
controller_config,settings_configs = load_configurations(configurations_folder_path)
shared_config = settings_configs["config 1"]


from wind_plant import power_wind
from solar_panel import solar_Power
from ev_battery_state import ev_state

electric_grid_model = Model(electric_grid_function)
controller_model = Model(partial(controller_multiple_cars, controller_settings=controller_config))
wind_plant_model = Model(power_wind)
solar_panel_model = Model(solar_Power)
ev_model = Model(ev_state)
price_market = Model(give_price)
storage_battery = Model(BatteryStorage)
models = [
    electric_grid_model,
    controller_model,
    wind_plant_model,
    solar_panel_model,
    ev_model,
    price_market,
    storage_battery,
]
manager = Manager(models, shared_config)
manager.run_simulation()
