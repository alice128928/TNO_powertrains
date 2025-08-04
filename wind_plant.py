import os

import numpy as np
import yaml
import requests
import pandas as pd
from windpowerlib import WindTurbine, WindFarm, TurbineClusterModelChain

# --- Module-level variables to cache weather and wind farm setup ---
_weather_data = None
_wind_farm = None
def get_weather_data(filename='weather.csv', datapath=''):
    file = 'data/weather.csv'
    weather_df = pd.read_csv(file, index_col=0, header=[0, 1])
    weather_df.index = pd.to_datetime(weather_df.index, utc=True)
    weather_df.index = weather_df.index.tz_convert('Europe/Berlin')
    return weather_df.resample('1h').first().iloc[:480]


def load_turbine_config(path='configurations/turbine_config.yaml'):
    """Load YAML turbine configuration."""
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    return config["wind_turbines"]


def collect_turbines(turbine_data: list):
    """Create a turbine fleet DataFrame compatible with WindFarm."""
    fleet = []
    for i, t in enumerate(turbine_data):
        turbine = WindTurbine(
            name=f"turbine_{i}",
            hub_height=t["hub_height"],
            nominal_power=t["nominal_power"],
            power_curve=pd.DataFrame({
                "value": [p * 1000 for p in [1.0, 2.0, 2.1, 5.0, 5.5, 5.0]],
                "wind_speed": [7.0, 8.5, 9.0, 11.5, 12.0, 15.0]
            })
        )
        fleet.append({
            "wind_turbine": turbine,
            "number_of_turbines": float(t["number_of_turbines"]),
            "total_capacity": np.nan
        })
    return pd.DataFrame(fleet)[["wind_turbine", "number_of_turbines", "total_capacity"]]


def init_wind_farm():
    """Initializes wind farm and caches data globally."""
    global _weather_data, _wind_farm
    if _weather_data is None:
        _weather_data = get_weather_data()

    turbine_config = load_turbine_config()
    turbine_fleet = collect_turbines(turbine_config)

    _wind_farm = WindFarm(wind_turbine_fleet=turbine_fleet, name='UserDefinedFarm')

init_wind_farm()
def power_wind(time_index: int) -> float:
    """
    Returns power output for the wind farm at a specific time step.

    Args:
        time_index (int): Timestep index (0–479).

    Returns:
        float: Total wind farm power output at that timestep.
    """
    global _weather_data, _wind_farm

    weather_step = _weather_data.iloc[[time_index]]
    model_chain = TurbineClusterModelChain(_wind_farm)
    model_chain.run_model(weather_step)

    return model_chain.power_output.iloc[0].sum()
