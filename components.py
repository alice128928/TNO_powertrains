import datetime

import streamlit as st

from config_setup import delete_config, load_config


@st.dialog("⚙️ Settings Configuration")
def settings_dialog():
    """Dialog for system configuration settings"""
    st.header("System Configuration")
    initial_money = st.number_input(
        "Initial budget ($)",
        min_value=0.0,
        format="%.4f",
        value=st.session_state.get("money", 0.0),
        key="dialog_money"
    )
    price_high = st.number_input(
        "Maximum price ($/kWh)",
        min_value=0.0,
        format="%.4f",
        value=st.session_state.get("price_high", 0.0),
        key="dialog_price_high"
    )
    price_low = st.number_input(
        "Minimum price ($/kWh)",
        min_value=0.0,
        format="%.4f",
        value=st.session_state.get("price_low", 0.0),
        key="dialog_price_low"
    )
    config_name = st.text_input(
        "Configuration version name",
        value=st.session_state.get("config_name", ""),
        key="dialog_config_name"
    )

    if st.button("Save Settings", type="primary"):
        st.session_state["money"] = initial_money
        st.session_state["price_high"] = price_high
        st.session_state["price_low"] = price_low
        st.session_state["config_name"] = config_name
        st.success("Settings saved!")
        st.rerun()


@st.dialog("⚙️ Battery Configuration")
def battery_dialog():
    """Dialog for system configuration settings"""
    st.header("Battery Configuration")
    storage_capacity = st.number_input(
        "Battery storage capacity (Wh)",
        min_value=0.0,
        value=st.session_state.get("storage", 0.0),
        key="dialog_storage"
    )

    if st.button("Save Settings", type="primary"):
        st.session_state["storage"] = storage_capacity
        st.success("Settings saved!")
        st.rerun()


@st.dialog("⚙️ Electrical grid Configuration")
def grid_dialog():
    """Dialog for system configuration settings"""
    st.header("Electrical grid Configuration")
    grid_capacity = st.number_input(
        "Grid capacity (W)",
        min_value=0.0,
        value=st.session_state.get("grid", 0.0),
        key="dialog_grid"
    )

    if st.button("Save Settings", type="primary"):
        st.session_state["grid"] = grid_capacity
        st.success("Settings saved!")
        st.rerun()

@st.dialog("⚙️ Additional load Configuration")
def load_dialog():
    """Dialog for system configuration settings"""
    st.header("Load Configuration")
    add_load = st.number_input(
        "Load (W)",
        min_value=0.0,
        value=st.session_state.get("load", 0.0),
        key="dialog_load"
    )

    if st.button("Save Settings", type="primary"):
        st.session_state["load"] = add_load
        st.success("Settings saved!")
        st.rerun()




@st.dialog("🔋 Electric Vehicle Configuration")
def ev_dialog():
    """Dialog for EV configuration"""
    st.header("Electric Vehicle Data")
    num_ev = st.number_input(
        "Number of EVs",
        min_value=1,
        step=1,
        value=st.session_state.get("num_ev", 1),
        key="dialog_num_ev"
    )

    ev_cars = []
    for i in range(int(num_ev)):
        st.subheader(f"EV {i+1}")
        car_id = st.text_input(
            f"Car ID for EV {i+1}",
            value=st.session_state.get(f"carid_{i}", ""),
            key=f"dialog_carid_{i}"
        )
        battery_capacity = st.number_input(
            f"Battery capacity (Wh) for EV {i+1}",
            min_value=0.0,
            value=st.session_state.get(f"bcap_{i}", 0.0),
            key=f"dialog_bcap_{i}"
        )
        charging_port = st.number_input(
            f"Charging port value (W) for EV {i+1}",
            min_value=0.0,
            value=st.session_state.get(f"port_{i}", 0.0),
            key=f"dialog_port_{i}"
        )
        arrival_time = st.time_input(
            f"Arrival time (HH:MM) for EV {i+1}",
            value=st.session_state.get(f"arr_{i}", datetime.time(0, 0)),
            key=f"dialog_arr_{i}"
        )
        departure_time = st.time_input(
            f"Departure time (HH:MM) for EV {i+1}",
            value=st.session_state.get(f"dep_{i}", datetime.time(0, 0)),
            key=f"dialog_dep_{i}"
        )
        ev_cars.append({
            "id": car_id,
            "battery_capacity": battery_capacity,
            "charging_port": charging_port,
            "arrival_time": arrival_time,
            "departure_time": departure_time,
        })

    if st.button("Save EV Configuration", type="primary"):
        st.session_state["num_ev"] = num_ev
        for i in range(int(num_ev)):
            st.session_state[f"carid_{i}"] = st.session_state[f"dialog_carid_{i}"]
            st.session_state[f"bcap_{i}"] = st.session_state[f"dialog_bcap_{i}"]
            st.session_state[f"port_{i}"] = st.session_state[f"dialog_port_{i}"]
            st.session_state[f"arr_{i}"] = st.session_state[f"dialog_arr_{i}"]
            st.session_state[f"dep_{i}"] = st.session_state[f"dialog_dep_{i}"]
        st.success("EV configuration saved!")
        st.rerun()







@st.dialog("💨 Wind Turbine Configuration")
def wind_dialog():
    """Dialog for wind turbine configuration"""
    st.header("Wind Turbine Data")
    num_turbine_types = st.number_input(
        "Number of wind farms",
        min_value=1,
        step=1,
        value=st.session_state.get("num_turbine_types", 1),
        key="dialog_num_turbine_types"
    )

    turbines = []
    for i in range(int(num_turbine_types)):
        st.subheader(f"Turbine farm {i+1}")
        hub_height = st.number_input(
            f"Hub height (m) for a turbine in farm {i+1}",
            min_value=0.0,
            value=st.session_state.get(f"hub_{i}", 0.0),
            key=f"dialog_hub_{i}"
        )

        number_of_turbines = st.number_input(
            f"Number of turbines in farm {i+1}",
            min_value=1,
            step=1,
            value=st.session_state.get(f"count_{i}", 1),
            key=f"dialog_count_{i}"
        )
        turbine_id = st.text_input(
            f"Turbine name (e.g., E-126/4200) for farm {i+1}",
            value=st.session_state.get(f"turbine_id_{i}", ""),
            key=f"dialog_turbine_id_{i}"
        )

        turbines.append({
            "hub_height": hub_height,
            "number_of_turbines": number_of_turbines,
            "turbine_id": turbine_id,
        })

    if st.button("Save Wind Configuration", type="primary"):
        st.session_state["num_turbine_types"] = num_turbine_types
        for i in range(int(num_turbine_types)):
            st.session_state[f"hub_{i}"] = st.session_state[f"dialog_hub_{i}"]
            st.session_state[f"count_{i}"] = st.session_state[f"dialog_count_{i}"]
            st.session_state[f"turbine_id_{i}"] = st.session_state[f"dialog_turbine_id_{i}"]
        st.success("Wind turbine configuration saved!")
        st.rerun()







@st.dialog("☀️ Solar Panel Configuration")
def solar_dialog():
    """Dialog for solar panel configuration"""
    st.header("Solar Panel Data")
    num_solar_types = st.number_input(
        "Number of solar farms",
        min_value=1,
        step=1,
        value=st.session_state.get("num_solar_types", 1),
        key="dialog_num_solar_types"
    )

    solar_panels = []
    for i in range(int(num_solar_types)):
        st.subheader(f"Solar farm {i+1}")
        latitude = st.number_input(
            f"Latitude (°) for panels in farm {i+1}",
            format="%.4f",
            min_value=-180.0,
            max_value=180.0,
            value=st.session_state.get(f"lat_{i}", 0.0),
            key=f"dialog_lat_{i}"
        )
        longitude = st.number_input(
            f"Longitude (°) for panels in farm {i+1}",
            format="%.4f",
            min_value=-180.0,
            max_value=180.0,
            value=st.session_state.get(f"lon_{i}", 0.0),
            key=f"dialog_lon_{i}"
        )
        altitude = st.number_input(
            f"Altitude (m) for panels in farm {i+1}",
            value=st.session_state.get(f"alt_{i}", 0),
            key=f"dialog_alt_{i}"
        )
        surface_tilt = st.number_input(
            f"Surface tilt (°) for panels in farm {i+1}",
            value=st.session_state.get(f"tilt_{i}", 0),
            key=f"dialog_tilt_{i}"
        )
        number_of_panels = st.number_input(
            f"Number of panels in farm {i+1}",
            min_value=1,
            step=1,
            value=st.session_state.get(f"panels_{i}", 1),
            key=f"dialog_panels_{i}"
        )
        module_id = st.text_input(
            f"Panel name for farm {i+1}",
            value=st.session_state.get(f"module_id_{i}", ""),
            key=f"dialog_module_id_{i}"
        )
        inverter_id = st.text_input(
            f"Inverter name for farm {i+1}",
            value=st.session_state.get(f"inverter_id_{i}", ""),
            key=f"dialog_inverter_id_{i}"
        )
        solar_panels.append({
            "latitude": latitude,
            "longitude": longitude,
            "altitude": altitude,
            "surface_tilt": surface_tilt,
            "number_of_panels": number_of_panels,
            "module_id": module_id,
            "inverter_id": inverter_id,
        })


    if st.button("Save Solar Configuration", type="primary"):
        st.session_state["num_solar_types"] = num_solar_types
        for i in range(int(num_solar_types)):
            st.session_state[f"lat_{i}"] = st.session_state[f"dialog_lat_{i}"]
            st.session_state[f"lon_{i}"] = st.session_state[f"dialog_lon_{i}"]
            st.session_state[f"alt_{i}"] = st.session_state[f"dialog_alt_{i}"]
            st.session_state[f"tilt_{i}"] = st.session_state[f"dialog_tilt_{i}"]
            st.session_state[f"panels_{i}"] = st.session_state[f"dialog_panels_{i}"]
            st.session_state[f"inverter_id_{i}"] = st.session_state[f"dialog_inverter_id_{i}"]
            st.session_state[f"module_id_{i}"] = st.session_state[f"dialog_module_id_{i}"]

        st.success("Solar panel configuration saved!")
        st.rerun()



def get_current_values():
    """Get current values from session state for simulation"""
    # Get turbine data
    num_turbine_types = st.session_state.get("num_turbine_types", 1)
    turbines = []
    for i in range(int(num_turbine_types)):
        turbines.append({
            "hub_height": st.session_state.get(f"hub_{i}", 0.0),
            "number_of_turbines": st.session_state.get(f"count_{i}", 1),
            "turbine_id": st.session_state.get(f"turbine_id_{i}", ""),  # ✅ fixed
        })

    # Get solar data
    num_solar_types = st.session_state.get("num_solar_types", 1)
    solar_panels = []
    for i in range(int(num_solar_types)):
        solar_panels.append({
            "latitude": st.session_state.get(f"lat_{i}", 0.0),
            "longitude": st.session_state.get(f"lon_{i}", 0.0),
            "altitude": st.session_state.get(f"alt_{i}", 0),
            "surface_tilt": st.session_state.get(f"tilt_{i}", 0),
            "number_of_panels": st.session_state.get(f"panels_{i}", 1),
            "inverter_id": st.session_state.get(f"inverter_id_{i}", ""),
            "module_id": st.session_state.get(f"module_id_{i}", ""),

        })

    # Get EV data
    num_ev = st.session_state.get("num_ev", 1)
    ev_cars = []
    for i in range(int(num_ev)):
        ev_cars.append({
            "id": st.session_state.get(f"carid_{i}", ""),
            "battery_capacity": st.session_state.get(f"bcap_{i}", 0.0),
            "charging_port": st.session_state.get(f"port_{i}", 0.0),
            "arrival_time": st.session_state.get(f"arr_{i}", datetime.time(0, 0)),
            "departure_time": st.session_state.get(f"dep_{i}", datetime.time(0, 0)),
        })

    # Get system config
    storage_capacity = st.session_state.get("storage", 0.0)
    grid_capacity = st.session_state.get("grid", 0.0)
    initial_money = st.session_state.get("money", 0.000)
    price_high = st.session_state.get("price_high", 0.000)
    price_low = st.session_state.get("price_low", 0.000)
    config_name = st.session_state.get("config_name", "")
    add_load = st.session_state.get("load", 0.0)


    return (turbines, solar_panels, ev_cars, storage_capacity, grid_capacity,
            initial_money, price_high, price_low, config_name,add_load)


def create_config_component():
    st.header("Saved Configurations")
    if st.session_state.configs:
        st.info("You can load or delete saved configurations below:")
        cols = st.columns(3)
        for name in st.session_state.configs.keys():
            with cols[0]:
                st.write(f"Config name: **{name}**")
            with cols[1]:
                if st.button("Load", key=f"load_{name}", icon="💾", type="secondary"):
                    load_config(name)
            with cols[2]:
                if st.button("Delete", key=f"del_{name}", icon="🗑️", type="primary"):
                    delete_config(name)
    else:
        st.info("No saved configurations found. Create a new one below.")
