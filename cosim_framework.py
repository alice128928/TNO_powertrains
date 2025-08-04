import matplotlib.pyplot as plt
import pandas as pd
from ev_request import ev_generate_from_config
from price_market import give_price
from battery_storage import  BatteryStorage
import numpy as np
import yaml
from datetime import datetime


class Model:
    """Wrapper class for modeling any physical process (e.g. power flow, heat production, etc.)."""

    def __init__(self, process_model):
        """Takes in the model of a physical process as a function or callable class."""
        if not callable(process_model):
            raise ValueError("The process must be a function or callable class.")
        self.process_model = process_model

    def calculate(self, *args) -> float:
        """Call the process function to perform calculations on an arbitrary number of inputs."""
        return self.process_model(*args)


class Manager:
    """The orchestrator manager for managing the data exchanged between the coupled models."""

    def __init__(self, models: list[Model], settings_configuration: dict):
        self.models = models
        self.electric_grid = models[0]
        self.controller = models[1]
        self.wind = models[2]
        self.solar = models[3]
        self.evstate = models[4]
        self.price_market = models[5]
        self.storage_battery = models[-1]
        self.settings_configuration = settings_configuration

    def run_simulation(self):
        config = self.settings_configuration
        config_id = config['InitializationSettings']['config_id']
        start_time = config['InitializationSettings']['time']['start_time']
        end_time = config['InitializationSettings']['time']['end_time']
        delta_t = config['InitializationSettings']['time']['delta_t']

        grid_topology = pd.read_csv(config['InitializationSettings']['grid_topology'])
        passive_consumer_power_setpoints = pd.read_csv(
            config['InitializationSettings']['passive_consumers_power_setpoints'],
            index_col="snapshots",
            parse_dates=True,
        )

        with open("configurations/controller_add_config.yaml", "r") as f:
            config_data = yaml.safe_load(f)

        configs = config_data["InitializationSettings"]["configs"][0]
        grid_capacity = float(configs["grid_capacity"])  # fixed spelling
        initial_money = float(configs["initial_money"])  # fixed key name
        storage_capacity = float(configs["storage_capacity"])  # fixed key name

        times = []
        smart_consumer_voltage_over_time = []
        wind_energy = []
        solar_energy = []
        power_setpoint_array = []
        price_array = []
        storage_array = []
        money_array = []

        money_array.append(initial_money)
        power_setpoint_array.append(0)
        battery = self.storage_battery.calculate(storage_capacity, 0.95, 0.95, 0)
        car_names, battery_caps, charging_ports, availability_arrays, battery_capacity_arrays, status_cars = ev_generate_from_config()
        time_index = 0
        time_steps = int((end_time - start_time) / delta_t)

        for time_step in range(time_steps):
            time_clock = start_time + time_step * delta_t
            corresponding_time_in_dataframe = passive_consumer_power_setpoints.index[time_step]
            #make all the models run

            all_consumer_voltages = self.electric_grid.calculate(
                    passive_consumer_power_setpoints, power_setpoint_array[time_index], grid_topology,
                    corresponding_time_in_dataframe,
                )

            smart_consumer_voltage = all_consumer_voltages["consumers"]["smart_consumer"]
            wind_energy_time = self.wind.calculate(time_index)
            solar_energy_time = self.solar.calculate(time_index)
            current_price_time = self.price_market.calculate(time_index)
            ev_state_time = self.evstate.calculate(time_index, availability_arrays, battery_caps, battery_capacity_arrays)

            for i in range(len(status_cars)):
                status_cars[i][time_index] = ev_state_time[i]

            money, battery, power_set_point, battery_capacity_arrays = self.controller.calculate(
                status_cars, charging_ports, battery, money_array[time_index], time_index, battery_capacity_arrays,
                solar_energy_time, wind_energy_time, current_price_time, storage_capacity, grid_capacity,
                smart_consumer_voltage, power_setpoint_array[time_index], battery_caps, availability_arrays
            )
            #append all the arrays
            times.append(time_clock)
            smart_consumer_voltage_over_time.append(smart_consumer_voltage)
            wind_energy.append(wind_energy_time)
            solar_energy.append(solar_energy_time)
            price_array.append(current_price_time)
            if isinstance(power_set_point, list):
                raise ValueError(f"Expected scalar power_set_point, got list: {power_set_point}")
            power_setpoint_array.append(power_set_point)
            time_index += 1
            storage_array.append(battery.get_soc())
            money_array.append(money)

        self.plot_results(
            times,
            smart_consumer_voltage_over_time,
            battery_capacity_arrays,
            solar_energy,
            wind_energy,
            storage_array,
            money_array,
            config_id,
        )

    def plot_results(self, times, voltages, battery_capacity_arrays, solar_energy, wind_energies, storage_array,
                     money_array, config_id):
        plt.style.use('ggplot')
        fig, axs = plt.subplots(3, 2, figsize=(14, 10))
        time_hours = np.array(times[:24]) / 60  # ⬅ Convert to hours for plotting
        # Plot for Voltage
        axs[0, 0].plot(time_hours, voltages[:24], color='blue')
        axs[0, 0].set_title("Voltage Over Time", color='black')
        axs[0, 0].set_xlabel("Time [hours]", color='black')
        axs[0, 0].set_ylabel("Voltage [V]", color='black')

        # Plot for Battery Capacities for all cars
        # Plot for Battery Capacities for all cars (first 24 hours)
        for i in range(len(battery_capacity_arrays)):
            axs[0, 1].plot(time_hours, battery_capacity_arrays[i][:24], label=f"Car {i + 1}")
        axs[0, 1].set_title("Battery Capacities Over First 24 Hours", color='black')
        axs[0, 1].set_xlabel("Time [hours]", color='black')
        axs[0, 1].set_ylabel("Battery Capacity [Wh]", color='black')
        axs[0, 1].legend()

        # Plot for Solar Energy Production (first 24 hours)
        axs[1, 0].plot(time_hours, solar_energy[:24], color='orange')
        axs[1, 0].set_title("Solar Production Over First 24 Hours", color='black')
        axs[1, 0].set_xlabel("Time [hours]", color='black')
        axs[1, 0].set_ylabel("Solar Energy [Wh]", color='black')

        # Plot for Wind Energy Production (first 24 hours)
        axs[1, 1].plot(time_hours, wind_energies[:24], color='purple')
        axs[1, 1].set_title("Wind Energy Over First 24 Hours", color='black')
        axs[1, 1].set_xlabel("Time [hours]", color='black')
        axs[1, 1].set_ylabel("Wind Energy [Wh]", color='black')

        # Plot for Storage over Time (first 24 hours)
        axs[2, 0].plot(time_hours, storage_array[:24], color='green')
        axs[2, 0].set_title("Storage Over First 24 Hours", color='black')
        axs[2, 0].set_xlabel("Time [hours]", color='black')
        axs[2, 0].set_ylabel("Storage [Wh]", color='black')

        # Plot for Money over Time (first 24 hours)
        axs[2, 1].plot(time_hours, money_array[:24], color='red')
        axs[2, 1].set_title("Money Over First 24 Hours", color='black')
        axs[2, 1].set_xlabel("Time [hours]", color='black')
        axs[2, 1].set_ylabel("Money [$]", color='black')

        # Adjust layout and save the plot
        plt.tight_layout()
        plt.savefig(f"results_config{config_id}.png")