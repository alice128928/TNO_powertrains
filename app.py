# app.py

import os
import datetime
from datetime import time
import yaml
import streamlit as st

from tab_components import (
    create_config_component,
    get_current_values,
    settings_tab,
    solar_tab,
    wind_tab,
    grid_tab,
    battery_tab,
    load_tab,
    charging_ports_tab,
    evs_tab,
    file_upload_tab,
    start_tab,          # <-- add this
)

from config_setup import init_configs, save_config
# IMPORTANT: do NOT import run here; we lazy-import it only when the user clicks "Run"
# from run_simulation import run   # <-- removed


# ----------------------------- Helpers -----------------------------

def _exists(path: str) -> bool:
    return bool(path) and os.path.exists(path)


def _write_all_yaml_from_session(
    turbines, solar_panels, ev_cars,
    storage_capacity, grid_capacity,
    initial_money, price_high, price_low,
    add_load, timestep, plot_port, plot_car_id,
    load_mode, load_points
):
    """Write all configuration YAMLs from the current UI/session state."""
    os.makedirs("configurations", exist_ok=True)

    # Ensure times / numpy scalars are YAML-safe
    for car in ev_cars:
        if isinstance(car.get("arrival_time"), time):
            car["arrival_time"] = car["arrival_time"].strftime("%H:%M")
        if isinstance(car.get("departure_time"), time):
            car["departure_time"] = car["departure_time"].strftime("%H:%M")
        if hasattr(car.get("battery_capacity"), "item"):  # numpy scalar
            car["battery_capacity"] = float(car["battery_capacity"].item())
        else:
            car["battery_capacity"] = float(car.get("battery_capacity", 0.0))

    # Custom YAML representers
    def time_representer(dumper, data):
        return dumper.represent_scalar('tag:yaml.org,2002:str', data.strftime('%H:%M'))

    def numpy_scalar_representer(dumper, data):
        return dumper.represent_scalar('tag:yaml.org,2002:float', float(data.item()))

    yaml.add_representer(datetime.time, time_representer)
    try:
        import numpy as np
        yaml.add_representer(np.floating, numpy_scalar_representer)
        yaml.add_representer(np.integer, numpy_scalar_representer)
    except Exception:
        pass

    system_config = [{
        "storage_capacity": storage_capacity,
        "grid_capacity": grid_capacity,
        "initial_money": initial_money,
        "price_high": price_high,
        "price_low": price_low,
        "add_load": add_load,            # legacy constant for back-compat
        "timestep": timestep,
        "plot_port": int(plot_port),
        "plot_car_id": str(plot_car_id or ""),
    }]

    wind_config_data = {
        "InitializationSettings": {"config_id": "config 1"},
        "wind_turbines": turbines,
    }
    solar_config_data = {
        "InitializationSettings": {"config_id": "config 1"},
        "solar_panels": solar_panels,
    }
    ev_config_data = {
        "InitializationSettings": {"config_id": "config 1", "cars": ev_cars}
    }
    controller_config_add = {
        "InitializationSettings": {"config_id": "config 1", "configs": system_config}
    }

    # Load profile
    if load_mode == "constant":
        load_config_data = {
            "InitializationSettings": {"config_id": "config 1"},
            "load_profile": {"mode": "constant", "constant_load_w": float(add_load)},
        }
    else:
        load_config_data = {
            "InitializationSettings": {"config_id": "config 1"},
            "load_profile": {"mode": "timeseries", "points": load_points},
        }

    # Ports
    ports_config_data = {
        "InitializationSettings": {"config_id": "config 1"},
        "ports": st.session_state.get("ports", []),
    }

    # ---- Write files
    with open("configurations/turbine_config.yaml", "w") as f:
        yaml.dump(wind_config_data, f, default_flow_style=False, sort_keys=False)
    with open("configurations/solar_config.yaml", "w") as f:
        yaml.dump(solar_config_data, f, default_flow_style=False, sort_keys=False)
    with open("configurations/ev_config.yaml", "w") as f:
        yaml.dump(ev_config_data, f, default_flow_style=False, sort_keys=False)
    with open("configurations/controller_add_config.yaml", "w") as f:
        yaml.dump(controller_config_add, f, default_flow_style=False, sort_keys=False)
    with open("configurations/load_config.yaml", "w") as f:
        yaml.dump(load_config_data, f, default_flow_style=False, sort_keys=False)
    with open("configurations/port_data.yaml", "w") as f:
        yaml.dump(ports_config_data, f, default_flow_style=False, sort_keys=False)


# --------------------------- App bootstrap --------------------------

st.set_page_config(page_title="Co-simulation Input Parameters", layout="wide")
init_configs()

# Session state defaults
if "result_ready" not in st.session_state:
    st.session_state["result_ready"] = False
if "used_yaml_loader" not in st.session_state:
    st.session_state["used_yaml_loader"] = False
if "save_config_clicked" not in st.session_state:
    st.session_state["save_config_clicked"] = False

st.title("Co-simulation Input Parameters")
create_config_component()
st.divider()

# --------------------------- Tab-based Interface ------------------------

tab0, tab9, tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "🚀 Start",
    "📁 Files",
    "⚙️ Settings",
    "🔋 Battery",
    "⚡ Grid",
    "🏠 Load",
    "⚡ Charging Ports",
    "🚗 EVs",
    "💨 Wind",
    "☀️ Solar",
])


with tab0:
    start_tab()

with tab9:
    file_upload_tab()
    st.divider()

with tab1:
    settings_tab()

with tab2:
    battery_tab()

with tab3:
    grid_tab()

with tab4:
    load_tab()

with tab5:
    charging_ports_tab()

with tab6:
    evs_tab()

with tab7:
    wind_tab()

with tab8:
    solar_tab()

st.divider()

# ------------------- Controls: Save + Run buttons -------------------

# Robust unpack: works with 13 (legacy) or 15 (with load extras)
_vals = list(get_current_values())
(turbines, solar_panels, ev_cars, storage_capacity, grid_capacity,
 initial_money, price_high, price_low, config_name,
 add_load, timestep, plot_port, plot_car_id) = _vals[:13]

# Optional extras
load_mode = st.session_state.get("load_mode", "constant")
load_points = st.session_state.get("load_timeseries", [])
if len(_vals) > 13:
    load_mode = _vals[13]
if len(_vals) > 14:
    load_points = _vals[14]

controls_col1, controls_col2 = st.columns([1, 1])

with controls_col1:
    if st.button("💾 Save Configuration"):
        if config_name:
            # Ensure times and dates are YAML-safe strings
            for car in ev_cars:
                if isinstance(car.get("arrival_time"), time):
                    car["arrival_time"] = car["arrival_time"].strftime("%H:%M")
                if isinstance(car.get("departure_time"), time):
                    car["departure_time"] = car["departure_time"].strftime("%H:%M")
                # Ensure battery capacity is a simple float
                if hasattr(car.get("battery_capacity"), 'item'):  # numpy scalar
                    car["battery_capacity"] = float(car["battery_capacity"].item())
                else:
                    car["battery_capacity"] = float(car["battery_capacity"])

            # Build YAML config blobs
            system_config = [{
                "storage_capacity": storage_capacity,
                "grid_capacity": grid_capacity,
                "initial_money": initial_money,
                "price_high": price_high,
                "price_low": price_low,
                "add_load": add_load,  # legacy constant (kept for back-compat)
                "timestep": timestep,
                "plot_port": int(plot_port),
                "plot_car_id": str(plot_car_id or ""),
            }]

            wind_config_data = {
                "InitializationSettings": {"config_id": "config 1"},
                "wind_turbines": turbines,
            }
            solar_config_data = {
                "InitializationSettings": {"config_id": "config 1"},
                "solar_panels": solar_panels,
            }
            ev_config_data = {
                "InitializationSettings": {"config_id": "config 1", "cars": ev_cars}
            }
            controller_config_add = {
                "InitializationSettings": {"config_id": "config 1", "configs": system_config}
            }

            # Dedicated load_config.yaml
            if load_mode == "constant":
                load_config_data = {
                    "InitializationSettings": {"config_id": "config 1"},
                    "load_profile": {
                        "mode": "constant",
                        "constant_load_w": float(add_load)
                    }
                }
            else:
                load_config_data = {
                    "InitializationSettings": {"config_id": "config 1"},
                    "load_profile": {
                        "mode": "timeseries",
                        "points": load_points  # [{"time": ISO8601, "load_w": float}, ...]
                    }
                }

            os.makedirs("configurations", exist_ok=True)

            # Custom YAML representers
            def time_representer(dumper, data):
                return dumper.represent_scalar('tag:yaml.org,2002:str', data.strftime('%H:%M'))

            def numpy_scalar_representer(dumper, data):
                return dumper.represent_scalar('tag:yaml.org,2002:float', float(data.item()))

            yaml.add_representer(datetime.time, time_representer)
            try:
                import numpy as np
                yaml.add_representer(np.floating, numpy_scalar_representer)
                yaml.add_representer(np.integer, numpy_scalar_representer)
            except ImportError:
                pass

            with open("configurations/turbine_config.yaml", "w") as f:
                yaml.dump(wind_config_data, f, default_flow_style=False, sort_keys=False)
            with open("configurations/solar_config.yaml", "w") as f:
                yaml.dump(solar_config_data, f, default_flow_style=False, sort_keys=False)
            with open("configurations/ev_config.yaml", "w") as f:
                yaml.dump(ev_config_data, f, default_flow_style=False, sort_keys=False)
            with open("configurations/controller_add_config.yaml", "w") as f:
                yaml.dump(controller_config_add, f, default_flow_style=False, sort_keys=False)
            with open("configurations/load_config.yaml", "w") as f:
                yaml.dump(load_config_data, f, default_flow_style=False, sort_keys=False)

            # NEW: save charging ports to configurations/port_data.yaml
            ports_config_data = {
                "InitializationSettings": {"config_id": "config 1"},
                "ports": st.session_state.get("ports", [])
            }
            with open("configurations/port_data.yaml", "w") as f:
                yaml.dump(ports_config_data, f, default_flow_style=False, sort_keys=False)

            # Optional: persist through your own helper as well
            save_config(turbines, solar_panels, ev_cars,
                        storage_capacity, grid_capacity,
                        initial_money, price_high, price_low,
                        add_load, timestep)

            st.session_state["save_config_clicked"] = True
            st.success("Configuration saved ✅")
        else:
            st.error("Please set a configuration name in the Settings tab first!")

with controls_col2:
    if st.button("▶️ Run Simulation", type="primary"):
        st.info("Running simulation with current inputs...")
        try:
            use_uploaded_yaml = st.session_state.get("use_uploaded_yaml", False)
            save_config_clicked = st.session_state.get("save_config_clicked", False)
            used_yaml_loader = st.session_state.get("used_yaml_loader", False)

            # ---------- Write YAMLs only if we're in UI-config mode AND user didn't click Save ----------
            if (not use_uploaded_yaml) and (not save_config_clicked):
                # Ensure times/dates are YAML-safe
                for car in ev_cars:
                    if isinstance(car.get("arrival_time"), time):
                        car["arrival_time"] = car["arrival_time"].strftime("%H:%M")
                    if isinstance(car.get("departure_time"), time):
                        car["departure_time"] = car["departure_time"].strftime("%H:%M")
                    if hasattr(car.get("battery_capacity"), 'item'):
                        car["battery_capacity"] = float(car["battery_capacity"].item())
                    else:
                        car["battery_capacity"] = float(car["battery_capacity"])

                system_config = [{
                    "storage_capacity": storage_capacity,
                    "grid_capacity": grid_capacity,
                    "initial_money": initial_money,
                    "price_high": price_high,
                    "price_low": price_low,
                    "add_load": add_load,
                    "timestep": timestep,
                    "plot_port": int(plot_port),
                    "plot_car_id": str(plot_car_id or ""),
                }]

                wind_config_data = {
                    "InitializationSettings": {"config_id": "config 1"},
                    "wind_turbines": turbines,
                }
                solar_config_data = {
                    "InitializationSettings": {"config_id": "config 1"},
                    "solar_panels": solar_panels,
                }
                ev_config_data = {
                    "InitializationSettings": {"config_id": "config 1", "cars": ev_cars}
                }
                controller_config_add = {
                    "InitializationSettings": {"config_id": "config 1", "configs": system_config}
                }

                if load_mode == "constant":
                    load_config_data = {
                        "InitializationSettings": {"config_id": "config 1"},
                        "load_profile": {
                            "mode": "constant",
                            "constant_load_w": float(add_load)
                        }
                    }
                else:
                    load_config_data = {
                        "InitializationSettings": {"config_id": "config 1"},
                        "load_profile": {
                            "mode": "timeseries",
                            "points": load_points
                        }
                    }

                os.makedirs("configurations", exist_ok=True)

                def time_representer(dumper, data):
                    return dumper.represent_scalar('tag:yaml.org,2002:str', data.strftime('%H:%M'))

                def numpy_scalar_representer(dumper, data):
                    return dumper.represent_scalar('tag:yaml.org,2002:float', float(data.item()))

                yaml.add_representer(datetime.time, time_representer)
                try:
                    import numpy as np
                    yaml.add_representer(np.floating, numpy_scalar_representer)
                    yaml.add_representer(np.integer, numpy_scalar_representer)
                except ImportError:
                    pass

                with open("configurations/turbine_config.yaml", "w") as f:
                    yaml.dump(wind_config_data, f, default_flow_style=False, sort_keys=False)
                with open("configurations/solar_config.yaml", "w") as f:
                    yaml.dump(solar_config_data, f, default_flow_style=False, sort_keys=False)
                with open("configurations/ev_config.yaml", "w") as f:
                    yaml.dump(ev_config_data, f, default_flow_style=False, sort_keys=False)
                with open("configurations/controller_add_config.yaml", "w") as f:
                    yaml.dump(controller_config_add, f, default_flow_style=False, sort_keys=False)
                with open("configurations/load_config.yaml", "w") as f:
                    yaml.dump(load_config_data, f, default_flow_style=False, sort_keys=False)

                ports_config_data = {
                    "InitializationSettings": {"config_id": "config 1"},
                    "ports": st.session_state.get("ports", [])
                }
                with open("configurations/port_data.yaml", "w") as f:
                    yaml.dump(ports_config_data, f, default_flow_style=False, sort_keys=False)

                st.info("Wrote YAMLs from current UI values (auto, no Save clicked).")
            else:
                if use_uploaded_yaml or used_yaml_loader:
                    st.info("Using uploaded YAMLs from the configurations/ folder.")
                elif save_config_clicked:
                    st.info("Using YAMLs saved via '💾 Save Configuration'.")

            # ---------- Safety: ensure YAMLs exist; if missing, write them now from session ----------
            required_paths = [
                "configurations/controller_add_config.yaml",
                "configurations/ev_config.yaml",
                "configurations/solar_config.yaml",
                "configurations/turbine_config.yaml",
                "configurations/port_data.yaml",
                "configurations/load_config.yaml",
            ]
            missing = [p for p in required_paths if not _exists(p)]
            if missing:
                _write_all_yaml_from_session(
                    turbines, solar_panels, ev_cars,
                    storage_capacity, grid_capacity,
                    initial_money, price_high, price_low,
                    add_load, timestep, plot_port, plot_car_id,
                    load_mode, load_points
                )
                # Re-check
                missing = [p for p in required_paths if not _exists(p)]
                if missing:
                    names = ", ".join(os.path.basename(p) for p in missing)
                    st.error(f"Missing required config files: {names}. Save or upload configs in the 📁 Files tab.")
                    st.stop()

            # ---------- Run (lazy import so UI loads without files) ----------
            from run_simulation import run as _run_simulation

            with st.spinner("Simulating..."):
                results = _run_simulation()
            st.session_state["results"] = results
            st.session_state["result_ready"] = True
            st.success("Simulation finished ✅")
        except Exception as e:
            st.session_state["result_ready"] = False
            st.error(f"Simulation failed: {e}")

st.divider()

# ------------------------- Results (always) -------------------------

st.header("📊 Simulation Results")
if results_figure := st.session_state.get("results"):
    st.plotly_chart(results_figure)
# if st.session_state.get("result_ready", False):
#     # result_path = "results_config1.png"
#     # if os.path.exists(result_path):
#     #     st.image(result_path, use_container_width=True, caption="Final result")
#     else:
#         st.warning(f"Result image '{result_path}' not found.")
# else:
#     st.info("Run a simulation to see results here.")

# ----------------------------- End ---------------------------------
