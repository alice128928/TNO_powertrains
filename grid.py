# grid.py
# ----------------------
# This module simulates power flow in an electricity grid using a predefined grid topology and active power data.
# It integrates with a power flow engine (via PowerGridModel) and returns voltage profiles for all consumers.
#
# Inputs:
# - active_power_df (pd.DataFrame): Time-indexed active power demand for each consumer (in kW, will be converted to W)
# - smart_consumer_power_setpoint (float): Power setpoint (in W) to be applied to the smart consumer during simulation
# - grid_topology (pd.DataFrame): Grid connection data (FROM, TO, Raa, Xaa, Imax)
# - time_step (pd.DatetimeIndex): Specific timestamp at which simulation is performed
# - smart_consumer_name_in_active_power_df (str): Name of the smart consumer column (default: "Customer_95")
#
# Outputs:
# - voltages (dict): Dictionary containing consumer voltages for the given time step.
#   Format: {"time step": time_step, "consumers": {consumer_name: voltage_pu, ..., "smart_consumer": voltage_pu}}

import numpy as np
import pandas as pd
from power_grid_model import (
    LoadGenType,
    PowerGridModel,
    ComponentType,
    initialize_array,
    DatasetType,
)

def electric_grid_function(
    active_power_df: pd.DataFrame,
    smart_consumer_power_setpoint: float,
    grid_topology: pd.DataFrame,
    time_step: pd.DatetimeIndex,
    smart_consumer_name_in_active_power_df: str = "Customer_95",
) -> dict[str, float]:
    """
    Main function to simulate power flow in an electricity grid at a given time step.

    Parameters:
    - active_power_df: DataFrame of consumer power demands (in kW)
    - smart_consumer_power_setpoint: Power setpoint (in W) for smart consumer
    - grid_topology: DataFrame containing line connection data
    - time_step: Time index for simulation
    - smart_consumer_name_in_active_power_df: Column name of smart consumer

    Returns:
    - Dictionary with per-unit voltages for each consumer at the given time step
    """
    voltages = {"time step": time_step, "consumers": {}}

    # Convert from kW to W and clean column names
    active_power_df = process_active_power_data_frame(active_power_df)

    # Overwrite smart consumer power for the selected time step
    active_power_df = update_active_power_data_frame_with_smart_consumer_power_setpoint(
        active_power_df, smart_consumer_name_in_active_power_df, smart_consumer_power_setpoint, time_step,
    )

    # Perform power flow simulation and retrieve consumer voltages
    consumer_voltage_dict = run_power_flow(grid_topology, active_power_df, time_step)

    # Save results in output dictionary
    voltages["consumers"].update(consumer_voltage_dict)

    # Rename smart consumer key for clarity
    voltages["consumers"]["smart_consumer"] = voltages["consumers"].pop(smart_consumer_name_in_active_power_df)

    return voltages


def update_active_power_data_frame_with_smart_consumer_power_setpoint(
    active_power_df: pd.DataFrame,
    smart_consumer_name_in_active_power_df: str,
    smart_consumer_power_setpoint: float,
    time_step: pd.DatetimeIndex,
) -> pd.DataFrame:
    """
    Apply a new power setpoint for the smart consumer at the given time step.

    Returns:
    - Modified DataFrame with updated power for the smart consumer
    """
    active_power_df.loc[time_step, smart_consumer_name_in_active_power_df] = smart_consumer_power_setpoint
    return active_power_df


def run_power_flow(
    grid_topology_df: pd.DataFrame,
    active_power_df: pd.DataFrame,
    time_step: pd.DatetimeIndex,
) -> dict[str, float]:
    """
    Runs power flow calculation and returns consumer voltages.

    Returns:
    - Dictionary mapping each consumer to its resulting voltage (in p.u.)
    """
    input_data = prepare_power_flow_data(grid_topology_df, active_power_df, time_step)
    model = PowerGridModel(input_data)
    output_data = model.calculate_power_flow()

    # Extract voltages from output
    voltages = output_data[ComponentType.node]["u_pu"].flatten().tolist()
    consumers = active_power_df.columns
    consumer_voltage_dict = dict(zip(consumers, voltages))

    return consumer_voltage_dict


def prepare_power_flow_data(
    grid_topology_df: pd.DataFrame, active_power_df: pd.DataFrame, time_step: pd.DatetimeIndex,
) -> dict:
    """
    Prepares grid data for the power flow simulation.

    Returns:
    - Dictionary containing node, line, source, and load definitions
    """
    num_lines = len(grid_topology_df)

    # Line configuration
    line = initialize_array(DatasetType.input, ComponentType.line, num_lines)
    line["id"] = np.arange(96, 96 + num_lines)
    line["from_node"] = grid_topology_df["FROM"].values
    line["to_node"] = grid_topology_df["TO"].values
    line["from_status"] = np.ones(num_lines)
    line["to_status"] = np.ones(num_lines)
    line["r1"] = grid_topology_df["Raa"].values
    line["x1"] = grid_topology_df["Xaa"].values
    line["c1"] = np.full(num_lines, 10e-6)  # Capacitance (optional)
    line["tan1"] = np.zeros(num_lines)
    line["i_n"] = grid_topology_df["Imax"].values

    # Node setup (95 nodes, 0.4kV each)
    node = initialize_array(DatasetType.input, ComponentType.node, 95)
    node["id"] = np.arange(1, 96)
    node["u_rated"] = [0.4e3] * 95

    # Slack/source configuration (fixed voltage)
    source = initialize_array(DatasetType.input, ComponentType.source, 1)
    source["id"] = [96 + num_lines + 95]
    source["node"] = [1]
    source["status"] = [1]
    source["u_ref"] = [1.0]

    # Load configuration (per node)
    sym_load = initialize_array(DatasetType.input, ComponentType.sym_load, 95)
    sym_load["id"] = np.arange(96 + num_lines, 96 + num_lines + 95)
    sym_load["node"] = np.arange(1, 96)
    sym_load["status"] = np.ones(95)
    sym_load["type"] = np.full(95, LoadGenType.const_power)
    sym_load["p_specified"] = active_power_df.loc[time_step, :].values
    sym_load["q_specified"] = calculate_reactive_power_from_active_power(sym_load["p_specified"])

    return {
        ComponentType.node: node,
        ComponentType.line: line,
        ComponentType.sym_load: sym_load,
        ComponentType.source: source,
    }


def calculate_reactive_power_from_active_power(active_power, power_factor: float = 0.95) -> float:
    """
    Estimate reactive power based on active power and assumed power factor.

    Returns:
    - Reactive power values (negative = inductive)
    """
    return -1 * active_power * np.tan(np.arccos(power_factor))


def process_active_power_data_frame(active_power_df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert active power from kW to W and clean column names.

    Returns:
    - Cleaned DataFrame with power in watts and column names without units
    """
    active_power_df = active_power_df * 1e3
    active_power_df.columns = active_power_df.columns.str.replace(" (kW)", "")
    return active_power_df
