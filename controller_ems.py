# controller_ems.py
# ------------------
# Energy Management System (EMS) Controller
#
# This module defines the logic for managing EV charging, grid interaction, storage behavior,
# and market participation across multiple electric vehicles (EVs) in a co-simulation.
#
# Inputs:
# - status: List of charging states (0 = not present, 1 = charging, 5 = plugged in but not charging)
# - power_charging_port: List of max port powers per EV (in W)
# - storage_obj: BatteryStorage object
# - money: Current budget ($)
# - time_step: Current simulation time step
# - battery_capacity: Array of battery levels over time for each EV
# - solar, wind: Power production in W
# - current_price: Market price at current timestep ($/Wh)
# - storage_capacity: Max storage energy (Wh)
# - grid_capacity: Max import/export capacity (W)
# - voltage: Current grid voltage (p.u.)
# - power_set_point: Desired system power output
# - ev_caps: Battery capacity per EV (Wh)
# - availability: EV presence array
# - controller_settings: YAML-style controller parameters
#
#  Outputs:
# - Updated money, storage state, new power set point, and battery capacities

import yaml
from battery_storage import BatteryStorage  # adjust import path if needed

def controller_multiple_cars(
    status, power_charging_port, storage_obj, money,
    time_step, battery_capacity, solar, wind,
    current_price, storage_capacity, grid_capacity,
    voltage, power_set_point, ev_caps, availability, controller_settings
):
    """Main EMS logic for charging multiple EVs, handling energy flows, grid limits, and pricing."""
    # 🔧 Fix SoC bug: propagate current battery values
    # ───── Update Non-Charging EVs ─────
    # ───── Final Update of Battery Capacities ─────
    # ───── Final Update of Battery Capacities ─────
    if time_step + 1 < len(battery_capacity[0]):
        for i in range(len(status)):
            if status[i][time_step] == 0:
                battery_capacity[i][time_step + 1] = 0  # EV left, reset battery
            elif status[i][time_step] == 5:
                battery_capacity[i][time_step + 1] = battery_capacity[i][time_step]  # Full, no charging
            elif status[i][time_step] != 1:
                # In case status is unknown (neither 0, 1, 5), carry over
                battery_capacity[i][time_step + 1] = battery_capacity[i][time_step]
            # Note: charging case (1) is handled earlier in the logic

    # ───── Load control settings from configuration file ─────
    with open("configurations/controller_add_config.yaml", "r") as f:
        config_data = yaml.safe_load(f)
    configs = config_data["InitializationSettings"]["configs"][0]
    price_high = float(configs["price_high"])
    price_low = float(configs["price_low"])

    # ───── Voltage-based Power Adjustment ─────
    voltage_min = controller_settings['ControllerSettings']['boundary_conditions']['minimum_voltage']
    voltage_max = controller_settings['ControllerSettings']['boundary_conditions']['maximum_voltage']
    p_adjust_step_size_voltage = controller_settings['ControllerSettings']['actions']['p_change_for_voltage']


    # Normalize ev_caps to a list
    if isinstance(ev_caps, (int, float)):
        ev_caps = [int(ev_caps)]
    else:
        ev_caps = [int(cap) for cap in ev_caps]


    # Voltage too low → increase  power; too high → decrease power
    if voltage < voltage_min:
        power_set_point += p_adjust_step_size_voltage
    elif voltage > voltage_max:
        power_set_point -= p_adjust_step_size_voltage

    # If voltage is outside safe bounds → terminate charging
    if not (voltage_min <= voltage <= voltage_max):
        return money, storage_obj, power_set_point, battery_capacity

    # ───── Charging Logic ─────
    charging_indices = [i for i in range(len(status)) if status[i][time_step] == 1]
    non_charging_indices = [i for i in range(len(status)) if status[i][time_step] in (0, 5)]
    total_power = solar + wind
    delta_t = 1  # 1 hour timestep

    #  No EVs charging
    if not charging_indices:
        if current_price > price_high:
            money += total_power * current_price
            return money, storage_obj, 0, battery_capacity

        elif current_price < price_low:
            if storage_obj.get_soc() >= storage_capacity:
                money += total_power * current_price
            else:
                room = storage_obj.get_remaining_capacity()
                to_store = min(total_power, room)
                storage_obj.charge(to_store, delta_t)
                if total_power > to_store:
                    money += (total_power - to_store) * current_price
        return money, storage_obj, 0, battery_capacity

    # ⚡ EVs ARE Charging
    total_nominal = sum(power_charging_port[i] for i in charging_indices)
    total_generated = solar + wind
    total_power_available = total_generated + storage_obj.get_soc() + grid_capacity

    # --- Case 1: Enough renewable energy to charge directly
    if total_nominal <= total_generated:
        for i in charging_indices:
            if battery_capacity[i][time_step] < ev_caps[i] - 1e-3:
                battery_capacity[i][time_step + 1] = min(
                    battery_capacity[i][time_step] + power_charging_port[i], ev_caps[i]
                )
            else:
                battery_capacity[i][time_step + 1] = battery_capacity[i][time_step]
        power_set_point = total_nominal

        # Store excess power if any
        excess = total_generated - total_nominal
        room = storage_obj.get_remaining_capacity()
        to_store = min(excess, room)
        storage_obj.charge(to_store, delta_t)
        if excess > room:
            money += (excess - to_store) * current_price

    # --- Case 2: Use renewable + storage to meet demand
    elif total_nominal <= total_generated + storage_obj.get_soc():
        deficit = total_nominal - total_generated
        storage_obj.discharge(deficit, delta_t)
        for i in charging_indices:
            if battery_capacity[i][time_step] < ev_caps[i] - 1e-3:
                battery_capacity[i][time_step + 1] = min(
                    battery_capacity[i][time_step] + power_charging_port[i], ev_caps[i]
                )
            else:
                battery_capacity[i][time_step + 1] = battery_capacity[i][time_step]
        power_set_point = total_nominal

    # --- Case 3: Need renewable + storage + grid
    elif total_nominal <= total_power_available:
        needed = total_nominal - total_generated
        storage_used = min(storage_obj.get_soc(), needed)
        actual_from_storage = storage_obj.discharge(storage_used, delta_t)
        remaining_deficit = needed - actual_from_storage
        grid_used = min(grid_capacity, remaining_deficit)
        money -= grid_used * current_price

        for i in charging_indices:
            if battery_capacity[i][time_step] < ev_caps[i] - 1e-3:
                battery_capacity[i][time_step + 1] = min(
                    battery_capacity[i][time_step] + power_charging_port[i], ev_caps[i]
                )
            else:
                battery_capacity[i][time_step + 1] = battery_capacity[i][time_step]
        power_set_point = total_nominal

    # --- Case 4: Not enough total power (curtail charging)
    elif total_nominal > total_power_available:
        available_power = total_power_available
        total_requested = total_nominal

        for i in charging_indices:
            ratio = power_charging_port[i] / total_requested
            allocated = ratio * available_power
            if battery_capacity[i][time_step] < ev_caps[i] - 1e-3:
                battery_capacity[i][time_step + 1] = min(
                    battery_capacity[i][time_step] +allocated, ev_caps[i]
                )
            else:
                battery_capacity[i][time_step + 1] = battery_capacity[i][time_step]

        used_from_storage = min(storage_obj.get_soc(), total_nominal - total_generated)
        storage_obj.discharge(used_from_storage, delta_t)
        money -= grid_capacity * current_price


    # Safety check for unexpected list return
    if isinstance(power_set_point, list):
        print(f" Warning: power_set_point was a list: {power_set_point}")
        power_set_point = power_set_point[0]

    return money, storage_obj, float(power_set_point), battery_capacity
