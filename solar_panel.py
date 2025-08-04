import os
import yaml
import numpy as np
import pandas as pd
from pvlib.modelchain import ModelChain
from pvlib.pvsystem import PVSystem, retrieve_sam
from pvlib.location import Location
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS

# --- Global cache ---
_weather_data = None
_pv_system = None
_location = None
_number_of_panels = None

def get_weather_data(filename='data/2016_Dc_Coordinates_(1).xlsx'):
    """Load and preprocess solar weather data (resampled to 1h, first 480 rows)."""
    df = pd.read_excel(filename).drop(0)
    df.columns = df.iloc[0]
    df = df.drop(1)

    df['datetime'] = pd.to_datetime(df[['Year', 'Month', 'Day', 'Hour', 'Minute']])
    df.set_index('datetime', inplace=True)
    df.index = pd.to_datetime(df.index)

    df = df.rename(columns={
        "Temperature": "temp_air",
        "Wind Speed": "wind_speed",
        "Relative Humidity": "humidity",
        "Precipitable Water": "precipitable_water",
        "GHI": "ghi",
        "DNI": "dni",
        "DHI": "dhi"
    })

    for col in ['temp_air', 'wind_speed', 'humidity', 'precipitable_water', 'ghi', 'dni', 'dhi']:
        df[col] = df[col].astype(float)

    df = df[['temp_air', 'wind_speed', 'humidity', 'precipitable_water', 'ghi', 'dni', 'dhi']]
    return df.resample('1h').mean().iloc[:480]


def load_panel_config(path='configurations/solar_config.yaml'):
    """Load solar panel configuration from separate YAML file."""
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    return config.get("solar_panels", [])


def create_pv_system(panel_data: dict):
    """Create PVSystem and Location objects."""
    module_db = retrieve_sam("cecmod")
    inverter_db = retrieve_sam("cecinverter")
    module = module_db["Znshine_PV_Tech_ZXP6_72_295_P"]
    inverter = inverter_db["ABB__MICRO_0_3_I_OUTD_US_208__208V_"]
    temp_model = TEMPERATURE_MODEL_PARAMETERS["sapm"]["open_rack_glass_glass"]

    location = Location(
        latitude=panel_data["latitude"],
        longitude=panel_data["longitude"],
        altitude=panel_data["altitude"]
    )

    system = PVSystem(
        surface_tilt=panel_data["surface_tilt"],
        surface_azimuth=180,
        module_parameters=module,
        inverter_parameters=inverter,
        temperature_model_parameters=temp_model
    )

    return system, location, panel_data["number_of_panels"]


def init_solar_model():
    """Initialize the solar model configuration and cache components."""
    global _weather_data, _pv_system, _location, _number_of_panels

    if _weather_data is None:
        _weather_data = get_weather_data()

    panel_config = load_panel_config()
    panel_data = panel_config[0]  # support for list of solar types

    _pv_system, _location, _number_of_panels = create_pv_system(panel_data)


def solar_Power(time_index: int) -> float:
    """
    Compute solar power output dynamically for the given timestep.

    Args:
        time_index (int): Index of the time step (0–479)

    Returns:
        float: Total solar power output in Watts
    """
    global _weather_data, _pv_system, _location, _number_of_panels

    if time_index < 0 or time_index >= len(_weather_data):
        return 0.0

    weather_step = _weather_data.iloc[[time_index]]
    mc = ModelChain(_pv_system, _location, aoi_model="physical")
    mc.run_model(weather=weather_step)

    ac_output = mc.results.ac.iloc[0] if not mc.results.ac.empty else 0.0
    return ac_output * _number_of_panels


# Initialize the system once at import
init_solar_model()
