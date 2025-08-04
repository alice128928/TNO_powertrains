# energy_price_reader.py
# ----------------------
# This module provides utility functions to:
# 1. Read hourly energy prices from an Excel file (e.g. spot market data)
# 2. Retrieve the price at a specific time index
#
# Inputs:
# - Excel file with energy prices (e.g. "EnergyPriceManyDays.xlsx")
#   Columns: [Date, Price]
#
# Outputs:
# - DataFrame with cleaned date and float-converted price
# - Single price value (in €/Wh) for a given time index

import pandas as pd

def read_energy_prices(filepath: str) -> pd.DataFrame:
    """
    Reads the Excel file and returns a DataFrame with 'date' and 'price' columns,
    limited to the first 480 rows (i.e., 20 days of hourly data).

    Parameters:
    - filepath (str): Path to the Excel file

    Returns:
    - pd.DataFrame: DataFrame with 'date' as datetime and 'price' as float [€/MWh]
    """
    # Load only first 480 rows and first two columns (date and price)
    df = pd.read_excel(filepath, usecols=[0, 1], nrows=480)

    # Rename columns for clarity
    df.columns = ['date', 'price']

    # Convert date column to datetime objects
    df['date'] = pd.to_datetime(df['date'])

    # Convert price column from string with comma decimal to float
    df['price'] = df['price'].astype(str).str.replace(',', '.').astype(float)

    return df

def give_price(time_index: int) -> float:
    """
    Returns the electricity price at a specific time index (e.g. hour of simulation).

    Parameters:
    - time_index (int): Row index (0–479) corresponding to the time step

    Returns:
    - float: Price in €/Wh (converted from €/MWh by dividing by 1000)
    """
    # Read the full energy price data
    price_data = read_energy_prices('data/EnergyPriceManyDays.xlsx')

    # Convert €/MWh to €/Wh (or k€/MWh to €/kWh depending on input unit)
    price_wh = price_data['price'].iloc[time_index] / 1000

    return price_wh
