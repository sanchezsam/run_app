# -*- coding: utf-8 -*-
# PART 1 OF 2: CORE LIBRARIES, STREAMLIT NAVIGATION AND RE-BOUND COCKPIT ROUTING
import json
import os
import datetime
import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
import matplotlib.pyplot as plt
from models import Character
from services import parse_garmin_tcx, parse_garmin_sleep_csv, parse_garmin_gpx, parse_garmin_fit
from coliseum_ui import render_coliseum
from upload_ui import render_upload_interface
from dashboard_ui import render_dashboard_overview, show_cal
from shop_ui import render_shop_interface
from character_profile import calculate_and_render_profile
from ledger_ui import render_training_ledger
from showroom_ui import render_trophy_showroom_tab
from showroom_ui import generate_dashboard_motivation_alerts

# 🥞 PANTRY ADAPTER INTERFACE IMPORTS
from pantry_ui import render_pantry_interface

# 🚨 MUST BE THE FIRST STREAMLIT EXECUTED ACTION TO PREVENT CRASHES
st.set_page_config(page_title="Cardio Training Hub", page_icon="🏎 ", layout="wide")

# ⚙️ Master Configuration Path Variables
FILE_PATH = 'save_file.json'
IMPORT_FILE_PATH = 'data/sync'  # Stores synced Garmin .fit binaries safely on disk



def process_and_award_metrics_in_memory(profile: dict, new_run_log: dict) -> dict:
    """
    Main evaluation pipeline processed completely in-memory inside app.py. 
    Processes incoming run payloads, updates profile statistics counters, 
    and returns the fully modified profile dictionary container.
    """
    import re
    import math
    import json

    if "final_metric_data" not in profile:
        return profile
        
    m_data = profile["final_metric_data"]
    run_distance = float(new_run_log.get("Distance (Miles)", 0.0))
    
    raw_pace = new_run_log.get("pace", 0.0)
    if isinstance(raw_pace, str) and ":" in raw_pace:
        try:
            parts = raw_pace.strip().split(":")
            run_pace_seconds = (int(parts[0]) * 60) + int(parts[1])
        except (ValueError, IndexError):
            run_pace_seconds = 660
    else:
        try:
            # Fallback inline calculator to bypass name errors
            run_pace_seconds = int(float(raw_pace) * 60)
        except:
            run_pace_seconds = 660
            
    try:
        raw_vert = new_run_log.get('elevation_gain', new_run_log.get('elevation', new_run_log.get('Elevation (ft)', 0.0)))
        run_elevation = float(str(raw_vert).replace("+","").replace("ft","").replace(",","").strip())
    except:
        run_elevation = 0.0
    
    if "unlocked_badges" not in profile:
        profile["unlocked_badges"] = []

    if "history_logs" not in profile:
        profile["history_logs"] = []
        
    is_duplicate = any(
        str(run.get("Date"))[:19] == str(new_run_log.get("Date"))[:19] and 
        abs(float(run.get("Distance (Miles)", 0.0)) - run_distance) < 0.01
        for run in profile["history_logs"] if isinstance(run, dict)
    )
    
    if not is_duplicate:
        profile["history_logs"].append(new_run_log)
    
    run_calories = int(run_distance * 100) 
    m_data["lifetime_calories_burned"] = int(m_data.get("lifetime_calories_burned", 0)) + run_calories
    profile["lifetime_elevation_gain"] = float(profile.get("lifetime_elevation_gain", 0.0)) + run_elevation

    total_accumulated_miles = 0.0
    history_source = profile.get("history_logs", [])

    for log_item in history_source:
        if isinstance(log_item, dict):
            total_accumulated_miles += float(log_item.get("Distance (Miles)", 0.0))

    m_data["lifetime_odometer_miles"] = round(total_accumulated_miles, 2)
    return profile



# ==========================================
# 2. LOCAL DATA PERSISTENCE ENGINE
# ==========================================
def load_profile_state():
    """
    Safely retrieves player progression stats and history metrics from the disk save file.
    Guarantees no data overwrites by automatically healing missing keys on boot.
    """
    default_state = {
        "name": "Racer 1", 
        "level": 0,                     
        "total_xp": 0,                  
        "running_level": 0,             
        "vo2_max": 0.0,                 
        "avg_heart_rate": 0, 
        "resting_heart_rate": 0,        
        "lifetime_elevation_gain": 0,   
        "cadence_history": [],
        "elevation_milestone_history": [], 
        "deep_rem_streak": 0, 
        "stat_points": 0, 
        "gold": 0,                      
        "endurance_level": 0,           
        "pace_level": 0,                
        "hill_climbing_level": 0,       
        "gold_balance": 0,              
        "inventory": [],                
        "equipped_gear": {},
        "registered_races": [],
        "boss_wins": 0,                 
        "fatigue": 0, 
        "days_tracked": 0, 
        "synced_garmin_activities": [],
        "daily_miles": 0.0,             
        "base_xp": 0,                   
        "exponent": 0.0,                
        "last_distance": 0.0,
        "last_pace": 0.0, 
        "final_metric_data": {}, 
        "stamina_xp": 0, 
        "agility_xp": 0,
        "power_xp": 0, 
        "boss_clears": 0,               
        "boss_levels": {}, 
        "history_logs": [],
        "calorie_bank_balance": 0,      
        "calorie_bank_total_earned": 0, 
        "pantry_purchase_counts": {}, 
        "pantry_single_trophies": [], 
        "pantry_cuisine_trophies": [] 
    }
    
    sticky_keys_to_wipe = ["profile", "global_endurance", "global_speed", "global_elevation"]
    for state_key in sticky_keys_to_wipe:
        if state_key in st.session_state:
            del st.session_state[state_key]

    if not os.path.exists(FILE_PATH):
        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(default_state, f, indent=4)
        return default_state

    try:
        with open(FILE_PATH, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
            if isinstance(loaded_data, dict):
                has_mutated = False
                for key, fallback_value in default_state.items():
                    if key not in loaded_data:
                        loaded_data[key] = fallback_value
                        has_mutated = True
                if has_mutated:
                    with open(FILE_PATH, 'w', encoding='utf-8') as f:
                        json.dump(loaded_data, f, indent=4)
                return loaded_data
            return default_state
    except (json.JSONDecodeError, Exception):
        return default_state


if "profile" not in st.session_state:
    # 🌟 Absolute First Boot: Fetch clean data dictionary layout straight from disk
    st.session_state["profile"] = load_profile_state()
else:
    # 🔄 Subsequent Page Refreshes: Pull disk metrics and merge into active memory
    disk_data = load_profile_state()
    active_profile = st.session_state.get("profile")

    if isinstance(disk_data, dict) and isinstance(active_profile, dict):
        for k, v in disk_data.items():
            if k == "history_logs" and isinstance(v, list):
                if "history_logs" not in active_profile:
                    active_profile["history_logs"] = []
                for log_item in v:
                    if log_item not in active_profile["history_logs"]:
                        active_profile["history_logs"].append(log_item)
            elif k == "unlocked_badges" and isinstance(v, list):
                if "unlocked_badges" not in active_profile:
                    active_profile["unlocked_badges"] = []
                for badge in v:
                    if badge not in active_profile["unlocked_badges"]:
                        active_profile["unlocked_badges"].append(badge)
            else:
                # Retain the highest available metrics counters
                if isinstance(v, (int, float)) and k in active_profile:
                    active_profile[k] = max(active_profile[k], v)

# ==============================================================================
# 🛡️  THE GLOBAL DOT-NOTATION PROXY PATCH (app.py Alignment)
# Maps st.session_state.profile straight to st.session_state["profile"] globally.
# This instantly fixes coliseum_ui.py and all other tabs with zero extra code editing!
# ==============================================================================
if "profile" in st.session_state:
    # Binds a direct reference link so that both syntax methods update the exact same RAM block
    st.session_state.profile = st.session_state["profile"]

# Enforce explicit layout state markers across the active session runtime context
st.session_state.initialized = True
st.session_state.profile_created = True
st.session_state.profile_setup = True
st.session_state.user_initialized = True
st.session_state.account_created = True
st.session_state.setup_complete = True


# ==============================================================================
# ⚡ THE ROOT INITIALIZATION HOOKS (Fixed to Eliminate NameErrors)
# Standard safe string keys initialize cleanly without looking for un-imported catalogs!
# ==============================================================================
if "selected_track_id" not in st.session_state:
    st.session_state.selected_track_id = ""

if "selected_boss_id" not in st.session_state:
    st.session_state.selected_boss_id = ""


# ==============================================================================
# 🎯 FIXED: TARGETED ROOT INITIALIZATION VALUES WITH BRACKET NOTATION
# Replaces old dot notation at line 169 to eliminate final AttributeError crashes!
# ==============================================================================
if "profile" in st.session_state and isinstance(st.session_state["profile"], dict):
    st.session_state.player_level = st.session_state["profile"].get("level", 0)
    st.session_state.player_gold = st.session_state["profile"].get("gold", 0)
    st.session_state.player_xp = st.session_state["profile"].get("total_xp", 0)
    st.session_state.calorie_bank_balance = st.session_state["profile"].get("calorie_bank_balance", 0)
    st.session_state.pantry_purchase_counts = st.session_state["profile"].get("pantry_purchase_counts", {})
    st.session_state.pantry_single_trophies = st.session_state["profile"].get("pantry_single_trophies", [])
    st.session_state.pantry_cuisine_trophies = st.session_state["profile"].get("pantry_cuisine_trophies", [])
    st.session_state.history_logs = st.session_state["profile"].get("history_logs", [])

import showroom_engine as showroom_eng
# Fixed the logs array pointer right below to read the safe memory block
logs_array = st.session_state["profile"].get("history_logs", []) if "profile" in st.session_state else []
if logs_array:
    st.session_state.filtered_df = showroom_eng.sanitize_json_history_logs(logs_array)
else:
    st.session_state.filtered_df = pd.DataFrame()


# ==============================================================================
# 🎯 FIXED: TRACK HISTORICAL LOG ARRAYS SAFELY WITH BRACKET STRING KEY FORMAT
# Replaces old dot notation at line 194 to clear out the final AttributeError!
# ==============================================================================
import showroom_engine as showroom_eng

# Using the dictionary lookup string pattern keeps Streamlit completely happy on boot passes
logs_array = st.session_state["profile"].get("history_logs", []) if "profile" in st.session_state else []

if logs_array:
    st.session_state.filtered_df = showroom_eng.sanitize_json_history_logs(logs_array)
else:
    st.session_state.filtered_df = pd.DataFrame()

# 🎯 FIXED: Replaced old dot notation with safe dictionary binding checks
if "profile" in st.session_state:
    current_profile = st.session_state["profile"]
else:
    current_profile = load_profile_state()
# ===============================================

# 🧬 GLOBAL BIOMETRIC CONDITIONING INITIALIZATION (app.py Sync)
# ==============================================================================
from character_economy_config import CHARACTER_XP_CONFIG

days_since_last_run = 999  # Couch baseline fallback
if isinstance(logs_array, list) and len(logs_array) > 0:
    try:
        last_log_date = logs_array[-1].get("Date", "")[:10]
        last_run_dt = datetime.datetime.strptime(last_log_date, '%Y-%m-%d').date()
        days_since_last_run = max(0, (datetime.date.today() - last_run_dt).days)
    except Exception:
        pass

cfg_dec = CHARACTER_XP_CONFIG["decay_tiers"]
cfg_taper = CHARACTER_XP_CONFIG["continuous_workload_taper"]

p_fuel_decay, p_nitro_decay, p_torque_decay = 0.0, 0.0, 0.0
status_indicator_text = "🟢 STATUS: PEAK CONDITIONING"
status_alert_type = "success"

if days_since_last_run <= cfg_dec["peak_window_days"]:
    p_fuel_decay, p_nitro_decay, p_torque_decay = cfg_dec["tier_1_penalties"]
    status_indicator_text = "🟢 STATUS: PEAK CONDITIONING"
    status_alert_type = "success"
elif days_since_last_run <= cfg_dec["minor_decay_days"]:
    p_fuel_decay, p_nitro_decay, p_torque_decay = cfg_dec["tier_2_penalties"]
    status_indicator_text = "🟡 STATUS: MINOR NEUROMUSCULAR SLOWDOWN"
    status_alert_type = "warning"
elif days_since_last_run <= cfg_dec["medium_decay_days"]:
    p_fuel_decay, p_nitro_decay, p_torque_decay = cfg_dec["tier_3_penalties"]
    status_indicator_text = "🟠 STATUS: ACTIVE ATHLETIC DECAY"
    status_alert_type = "warning"
elif days_since_last_run <= cfg_dec["severe_decay_days"]:
    p_fuel_decay, p_nitro_decay, p_torque_decay = cfg_dec["tier_4_penalties"]
    status_indicator_text = "🔴 STATUS: SYSTEMIC MITOCHONDRIAL ATROPHY"
    status_alert_type = "error"
else:
    p_fuel_decay, p_nitro_decay, p_torque_decay = cfg_dec["tier_5_penalties"]
    status_indicator_text = "🔴 STATUS: CHRONIC DECONDITIONING"
    status_alert_type = "error"

today_dt = datetime.date.today()
cutoff_14d = today_dt - datetime.timedelta(days=14)
cutoff_28d = today_dt - datetime.timedelta(days=28)

miles_recent_14_days = 0.0
miles_previous_14_days = 0.0

if isinstance(logs_array, list):
    for log_item in logs_array:
        if isinstance(log_item, dict) and "Date" in log_item:
            try:
                log_date_str = log_item.get("Date", "")[:10]
                log_dt = datetime.datetime.strptime(log_date_str, '%Y-%m-%d').date()
                if today_dt >= log_dt >= cutoff_14d:
                    miles_recent_14_days += float(log_item.get("Distance (Miles)", log_item.get("Distance", 0.0)))
                elif cutoff_14d > log_dt >= cutoff_28d:
                    miles_previous_14_days += float(log_item.get("Distance (Miles)", log_item.get("Distance", 0.0)))
            except Exception:
                pass

miles_last_28_days = miles_recent_14_days + miles_previous_14_days
peak_target = float(cfg_taper["peak_monthly_target_miles"])
is_building_volume = miles_recent_14_days > miles_previous_14_days

if miles_last_28_days < peak_target:
    if is_building_volume and days_since_last_run <= cfg_dec["peak_window_days"]:
        p_fuel_decay = 0.0
        p_nitro_decay = 0.0
        status_indicator_text = "🚀 STATUS: POSITIVE TRAINING ACCELERATION (BUILD PHASE)"
        status_alert_type = "success"
    else:
        volume_deficit_ratio = (peak_target - miles_last_28_days) / peak_target
        chronic_stamina_penalty = round(volume_deficit_ratio * cfg_taper["max_atrophy_penalty_cap"], 1)
        chronic_speed_penalty   = round(chronic_stamina_penalty * cfg_taper["speed_decay_sensitivity"], 1)
        
        p_fuel_decay  = max(p_fuel_decay, chronic_stamina_penalty)
        p_nitro_decay = max(p_nitro_decay, chronic_speed_penalty)
        
        retention_pct = int((miles_last_28_days / peak_target) * 100)
        if retention_pct >= 60:
            status_indicator_text = f"📉 STATUS: STABLE REGULATED TAPER ({retention_pct}% Volume Retained)"
            status_alert_type = "warning"
        else:
            status_indicator_text = f"⚠️ STATUS: MODERATE VOLUME DEFICIT ({retention_pct}% Volume Retained)"
            status_alert_type = "error"

p_fuel_max   = int(current_profile.get("endurance_level", 1) if isinstance(current_profile, dict) else 1)
p_nitro_max  = int(current_profile.get("pace_level", 1) if isinstance(current_profile, dict) else 1)
p_torque_max = int(current_profile.get("hill_climbing_level", 1) if isinstance(current_profile, dict) else 1)

st.session_state.global_days_gap = days_since_last_run
st.session_state.global_miles_28d = miles_last_28_days
st.session_state.global_peak_target = peak_target
st.session_state.global_status_text = status_indicator_text
st.session_state.global_alert_type = status_alert_type
st.session_state.global_is_building = is_building_volume

st.session_state.p_fuel   = max(1.0, round(p_fuel_max - p_fuel_decay, 1))
st.session_state.p_nitro  = max(1.0, round(p_nitro_max - p_nitro_decay, 1))
st.session_state.p_torque = max(1.0, round(p_torque_max - p_torque_decay, 1))
st.session_state.p_fuel_decay   = p_fuel_decay
st.session_state.p_nitro_decay  = p_nitro_decay
st.session_state.p_torque_decay = p_torque_decay

try:
    player = Character(FILE_PATH)
    player.p_fuel = st.session_state.p_fuel
    player.p_nitro = st.session_state.p_nitro
    player.p_torque = st.session_state.p_torque
    player.calorie_bank_balance = st.session_state.get("calorie_bank_balance", 0)
    player.level = st.session_state.get("player_level", 1)
    player.gold = st.session_state.get("player_gold", 0)
    player.total_xp = st.session_state.get("player_xp", 0)
except Exception:
    player = current_profile





# ==========================================
# 3. INTERACTIVE RENDERING: NONAGON CHART
# ==========================================
def generate_single_metric_nonagon(level_value, category_type):
    """
    Generates a true 9-sided nonagon chart with individual flat-edged slices,
    visible slice divider lines, and a clean outer perimeter line.
    """
    num_slices = 9
    level_value = max(0, min(int(level_value), 9))
    if category_type == 'Endurance':
        chart_title = "Endurance"
        fill_color = '#3b82f6' 
        edge_color = '#1e3a8a' 
    elif category_type == 'Speed':
        chart_title = "Speed"
        fill_color = '#22c55e' 
        edge_color = '#15803d' 
    else:
        chart_title = "Elevation"
        fill_color = '#f59e0b' 
        edge_color = '#b45309' 

    fig, ax = plt.subplots(figsize=(1.6, 1.6), subplot_kw=dict(polar=True))
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.grid(False)
    ax.spines['polar'].set_visible(False)
    
    angles = np.linspace(0, 2 * np.pi, num_slices, endpoint=False)
    for i in range(num_slices):
        start_angle = angles[i]
        end_angle = angles[(i + 1) % num_slices]
        wedge_theta = [0, start_angle, end_angle, 0]
        wedge_radius = [0, 3, 3, 0]
        if i < level_value:
            ax.fill(wedge_theta, wedge_radius, color=fill_color, alpha=0.85, zorder=1)
        else:
            ax.fill(wedge_theta, wedge_radius, color='#000000', alpha=0.04, zorder=1)
            
    for angle in angles:
        ax.plot([angle, angle], [0, 3], color='#e2e8f0', linewidth=0.8, linestyle='solid', zorder=2)
        
    outline_angles = np.append(angles, angles[0])
    outer_perimeter_radius = [3] * (num_slices + 1)
    ax.plot(outline_angles, outer_perimeter_radius, color='#cbd5e1', linewidth=1.2, linestyle='solid', zorder=3)
    
    labels = [f"{i+1}" for i in range(num_slices)]
    plt.xticks(angles, labels, color='#9ca3af', size=6)
    plt.yticks([], [])
    plt.ylim(0, 3)
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#ffffff')
    ax.set_title(chart_title, size=8, weight='bold', pad=4, color='#1f2937')
    plt.tight_layout()
    return fig

def load_player():
    """
    Safely retrieves player progression stats from disk.
    Guarantees that a valid Character instance is always returned to prevent
    the application from locking onto the initialization splash screen.
    """
    if os.path.exists(FILE_PATH):
        try:
            with open(FILE_PATH, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
                if isinstance(raw_data, dict):
                    if "bodyweight" in raw_data and "weight_kg" not in raw_data:
                        raw_data["weight_kg"] = raw_data["bodyweight"]
                    if "weight_kg" in raw_data and "bodyweight" not in raw_data:
                        raw_data["bodyweight"] = raw_data["weight_kg"]
                        
                    try:
                        data_copy = dict(raw_data)
                        history_backup = data_copy.pop("history_logs", [])
                        player_instance = Character.from_dict(data_copy)
                        player_instance.history_logs = history_backup
                        st.session_state.profile = raw_data
                        return player_instance
                    except Exception:
                        player_instance = Character(name=raw_data.get("name", "Racer 1"))
                        for key, val in raw_data.items():
                            try:
                                setattr(player_instance, key, val)
                            except Exception:
                                pass
                        player_instance.history_logs = raw_data.get("history_logs", [])
                        player_instance.inventory = raw_data.get("inventory", [])
                        player_instance.equipped_gear = raw_data.get("equipped_gear", {})
                        player_instance.weight_kg = float(raw_data.get("weight_kg", 75.0))
                        st.session_state.profile = raw_data
                        return player_instance
        except Exception:
            pass
            
    try:
        emergency_instance = Character(name="Racer 1")
        emergency_instance.history_logs = []
        emergency_instance.inventory = []
        emergency_instance.equipped_gear = {}
        return emergency_instance
    except Exception:
        return None


if player is None:
    st.title('Character Profile Initialization')
    with st.form('init_char_form'):
        c_name = st.text_input('Driver Profile Name', value='Racer 1')
        c_weight = st.number_input('Body Weight (kg)', min_value=30.0, value=75.0)
        if st.form_submit_button('Forge Active Profile'):
            player_obj = Character(name=c_name.strip())
            player_obj.weight_kg = c_weight
            with open(FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(player_obj.to_dict(), f, default=str, indent=4)
            st.success('✨ Profile Forged! Launching dashboard engine...')
            st.rerun()
    st.stop()

# PART 2 OF 2: MASTER METRICS STRIPS, TAB CONTROLLERS AND STABLE FILE SAVE EMITTERS
if player is not None and os.path.exists(FILE_PATH):
    try:
        with open(FILE_PATH, 'r', encoding='utf-8') as f:
            raw = json.load(f)
            player.level = int(raw.get('level', 1))
            player.total_xp = int(raw.get('total_xp', 0))
            player.gold = int(raw.get('gold', 50))
            player.fatigue = int(raw.get('fatigue', 0))
            
            xp_per_level = 250
            if player.total_xp >= xp_per_level:
                calculated_levels_gained = player.total_xp // xp_per_level
                player.level += calculated_levels_gained
                player.total_xp %= xp_per_level
    except Exception: 
        pass

    hud_col1, hud_col2, hud_col3, hud_col4, hud_col5, hud_col6,hud_col7 = st.columns(7)
    st.write("")
    active_trophies = getattr(player, 'pantry_single_trophies', [])
    if active_trophies:
        st.markdown("### 🏆 **EARNED ATHLETE MILESTONE TROPHIES**")
        t_cols = st.columns(max(4, len(active_trophies)))
        col_idx = 0
        if "Rabbit" in active_trophies:
            with t_cols[col_idx]:
                st.success("🐇 **Fleet-Footed Rabbit**\n\n`Pace: Elite Sub-8:30`\n\n ⚡ *Speed Class Mastered*")
                col_idx += 1
        if "Deer" in active_trophies:
            with t_cols[col_idx]:
                st.info("🦌 **Swift-Stride Deer**\n\n`Dist: Long Training Run`\n\n 🔋 *Endurance Class Unlocked*")
                col_idx += 1

    # 🎯 UPDATED HUD METRICS DISPLAY GRID FIXED
    # All inline getattr defaults have been set to absolute zero baseline models.
    # This guarantees that if a player object is read with blank or missing variables,
    # the screen cleanly loads absolute zero metrics instead of stale fallback values!
    with hud_col1: st.metric('Active Level', f'{player.level}')
    with hud_col2: st.metric('Gold Balance', f'{int(getattr(player, "gold", 0))} g')  # 💰 Changed fallback from 50 to 0
    with hud_col3: st.metric('VO2 Max Baseline', f'{player.vo2_max:.1f}')
    with hud_col4: st.metric('Fatigue Accumulation', f'{int(getattr(player, "fatigue", 0))}/100')
    with hud_col5: st.metric('🏁 Checkered Flags', f'{getattr(player, "boss_clears", 0)} Wins')
    with hud_col6: st.metric('Stat Tokens', f'{getattr(player, "stat_points", 0)} Available')
    with hud_col7: st.metric('🔥 Calorie Bank', f'{int(getattr(player, "calorie_bank_balance", 0))} kcal')

if "filtered_df" not in st.session_state or st.session_state.filtered_df.empty:
    import showroom_engine as showroom_eng
    try:
        if os.path.exists(FILE_PATH):
            with open(FILE_PATH, 'r', encoding='utf-8') as database_file:
                raw_database_payload = json.load(database_file)
                if isinstance(raw_database_payload, dict) and "history_logs" in raw_database_payload:
                    history_list = raw_database_payload["history_logs"]
                    df_sanitized_matrix = showroom_eng.sanitize_json_history_logs(history_list)
                    st.session_state.filtered_df = df_sanitized_matrix
    except Exception:
        st.session_state.filtered_df = pd.DataFrame()

# ==========================================
# 💎 STYLIZED SIDEBAR NAVIGATION HUB
# ==========================================
if "active_tab_selection" not in st.session_state:
    st.session_state.active_tab_selection = "🏠 Dashboard Overview"

with st.sidebar:
    st.markdown("### 🏎️ Cardio Training Hub")
    #st.caption(f"Logged in as: **{getattr(player, 'name', 'Racer 1')}**")
    # 🟢 Pulls the true profile string name out of your loaded state dictionary
    active_username = st.session_state.get("profile", {}).get("name", "Racer 1")
    st.sidebar.markdown(f"**Logged in as:** {active_username}")

    st.markdown("---")
    
    # 🎯 STEP 1: Check if the Showroom is selected.
    # If active, inject custom CSS to widen the sidebar dynamically from ~336px to 580px,
    # and adjust the column ratios to give the popout sub-menu plenty of space.
    if st.session_state.get("active_tab_selection") == "🏆 Showroom & PRs":
        st.markdown(
            """
            <style>
            [data-testid="stSidebar"] {
                min-width: 580px !important;
                max-width: 580px !important;
            }
            </style>
            """,
            unsafe_allow_html=True
        )
        # Give the main menu a solid proportion (1) and the popout sub-menu more breathing room (1.5)
        sb_col1, sb_col2 = st.columns([1, 1.5])
    else:
        # Fallback: When on other tabs, do not inject the CSS, allowing the sidebar
        # to automatically snap back to its regular, default narrow layout.
        sb_col1 = st.container()
        sb_col2 = None

    # 🎯 STEP 2: Place all your existing navigation buttons inside the left column (sb_col1)
    with sb_col1:
        # Category Group 1: Core Hub
        st.markdown("🎮 **CORE ATHLETE HUB**")
        if st.button("🏠 Dashboard Overview", key="nav_sidebar_dash", type="primary" if st.session_state.active_tab_selection == "🏠 Dashboard Overview" else "secondary", use_container_width=True):
            st.session_state.active_tab_selection = "🏠 Dashboard Overview"
            st.rerun()
        if st.button("👤 Athlete Profile", key="nav_sidebar_prof", type="primary" if st.session_state.active_tab_selection == "👤 Athlete Profile" else "secondary", use_container_width=True):
            st.session_state.active_tab_selection = "👤 Athlete Profile"
            st.rerun()
            
        st.markdown("")
        # Category Group 2: Data Ingest & Logging
        st.markdown("⚡ **DATA INGESTION**")
        if st.button("📥 Telemetry Sync", key="nav_sidebar_sync", type="primary" if st.session_state.active_tab_selection == "Telemetry Sync" else "secondary", use_container_width=True):
            st.session_state.active_tab_selection = "Telemetry Sync"
            st.rerun()
        if st.button("📜 Training Ledger", key="nav_sidebar_ledger", type="primary" if st.session_state.active_tab_selection == "Training Ledger" else "secondary", use_container_width=True):
            st.session_state.active_tab_selection = "Training Ledger"
            st.rerun()
        if st.button("📅 Calendar Schedule", key="nav_sidebar_cal", type="primary" if st.session_state.active_tab_selection == "Calendar" else "secondary", use_container_width=True):
            st.session_state.active_tab_selection = "Calendar"
            st.rerun()
            
        st.markdown("")
        # Category Group 3: Performance Arenas
        st.markdown("🏟️ **COMPETITION ARENAS**")
        if st.button("🏟️ Biometric Coliseum", key="nav_sidebar_coli", type="primary" if st.session_state.active_tab_selection == "Biometric Coliseum" else "secondary", use_container_width=True):
            st.session_state.active_tab_selection = "Biometric Coliseum"
            st.rerun()
        #if st.button("📊 Performance Analytics", key="nav_sidebar_anly", type="primary" if st.session_state.active_tab_selection == "Performance Analytics" else "secondary", use_container_width=True):
        #    st.session_state.active_tab_selection = "Performance Analytics"
        #    st.rerun()
        if st.button("🏆 Showroom & PRs", key="nav_sidebar_show", type="primary" if st.session_state.active_tab_selection == "🏆 Showroom & PRs" else "secondary", use_container_width=True):
            st.session_state.active_tab_selection = "🏆 Showroom & PRs"
            st.rerun()
            
        st.markdown("")
        # Category Group 4: Marketplace Economy
        st.markdown("🛒 **MARKETPLACE ECONOMY**")
        if st.button("🛍️ Pro Shop & Garage", key="nav_sidebar_shop", type="primary" if st.session_state.active_tab_selection == "Pro Shop & Garage" else "secondary", use_container_width=True):
            st.session_state.active_tab_selection = "Pro Shop & Garage"
            st.rerun()
        if st.button("🏪 Calorie Pantry Market", key="nav_sidebar_pantry", type="primary" if st.session_state.active_tab_selection == "🏪 Calorie Pantry Market" else "secondary", use_container_width=True):
            st.session_state.active_tab_selection = "🏪 Calorie Pantry Market"
            st.rerun()


# =====================================================================
# SHOWROOM ROUTING ROUTINE (KEEP THIS EXACTLY THE SAME AROUND LINE 429)
# =====================================================================
if st.session_state.active_tab_selection == "🏆 Showroom & PRs":
    raw_profile = st.session_state.get("profile", {})
    raw_logs_list = raw_profile.get("history_logs", [])
    clean_dicts_list = []
    if isinstance(raw_logs_list, list):
        for entry in raw_logs_list:
            if isinstance(entry, dict):
                clean_dicts_list.append(entry)
                
    if len(clean_dicts_list) > 0:
        df_raw_wrapper = pd.DataFrame(clean_dicts_list)
        df_instances = showroom_eng.compile_all_award_instances(df_raw_wrapper)
    else:
        df_instances = pd.DataFrame(columns=["award_code", "date", "metric", "type", "details"])
        
    if "award_code" not in df_instances.columns:
        df_instances = pd.DataFrame(columns=["award_code", "date", "metric", "type", "details"])
        
    defense_state = raw_profile.get("defense_state", "stable")
    
    # Forward the now roomier sb_col2 container layout to the renderer function
    #render_trophy_showroom_tab(df_instances, defense_state, popout_container=sb_col2)
    #render_trophy_showroom_tab(df_instances, defense_state, popout_container=sb_col2, widget_id="sidebar_view")


elif st.session_state.active_tab_selection == 'Calendar':
    show_cal(player)






# --- TAB CONTROLLER CONDITIONAL RENDERING ---
if st.session_state.active_tab_selection == '🏠 Dashboard Overview':
    generate_dashboard_motivation_alerts()
    render_dashboard_overview(player)
elif st.session_state.active_tab_selection == '👤 Athlete Profile':
    calculate_and_render_profile(player)
    st.write("")
    st.markdown("### 🗺 **ATHLETE MATRIX PROFILE GAUGES**")
    dashboard_end = st.session_state.get("global_endurance", 1)
    dashboard_spd = st.session_state.get("global_speed", 1)
    dashboard_elev = st.session_state.get("global_elevation", 1)
    
    _, col1, col2, col3, _ = st.columns([1, 2, 2, 2, 1])
    with col1:
        st.metric("🔋 Endurance", f"{dashboard_end} / 9")
        st.pyplot(generate_single_metric_nonagon(dashboard_end, 'Endurance'))
    with col2:
        st.metric("⚡ Speed", f"{dashboard_spd} / 9")
        st.pyplot(generate_single_metric_nonagon(dashboard_spd, 'Speed'))
    with col3:
        st.metric("⛰ Elevation", f"{dashboard_elev} / 9")
        st.pyplot(generate_single_metric_nonagon(dashboard_elev, 'Elevation'))
elif st.session_state.active_tab_selection == 'Telemetry Sync':
    # Create two clear sub-tabs within the Telemetry Sync page view
    cloud_tab, manual_tab = st.tabs(["☁️ Garmin Connect Cloud Sync", "📥 Manual FIT File Ingestion"])
    
                       













    with cloud_tab:
        st.markdown("### ☁️ Garmin Connect Direct Sync Gateway")
        st.caption("Pull your latest activity directly from Garmin servers without downloading files.")

        import os
        import io
        import re
        import glob
        import math
        import json
        import traceback
        import zipfile
        from datetime import datetime, timedelta
        import streamlit as st
        from garminconnect import Garmin
        from services import parse_garmin_fit

        # 1. Title/Header
        st.subheader("🏃‍♂️ Garmin Connect Sync Engine")

        # 2. Date Range Input Layout
        #col1, col2 = st.columns(2)
        #with col1:
        #    start_date = st.date_input("Start Date", value=datetime.today() - timedelta(days=7))
        #with col2:
        #    end_date = st.date_input("End Date", value=datetime.today())


        # Open app.py and change lines 545-550 to this clean configuration:
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start Date", 
                value=datetime.today() - timedelta(days=7),
                min_value=datetime(2000, 1, 1), # 🟢 Removed the '.date' segment
                max_value=datetime.today()
            )
        with col2:
            end_date = st.date_input(
                "End Date", 
                value=datetime.today(),
                min_value=datetime(2000, 1, 1), # 🟢 Removed the '.date' segment
                max_value=datetime.today()
            )


        if start_date > end_date:
            st.error("❌ Error: Start Date must be before or equal to End Date.")
        # ======================================================================
        # 🧪 DEV BYPASS SWITCH (DEFAULTED TO TRUE FOR DISK-BASED UPLOAD TESTING)
        # ======================================================================
        st.markdown("---")
        #st.caption("🛠️ Sync Data")
        #bypass_download = st.checkbox("⚙️ Bypass Download Phase (Test Upload Mode)", value=True)
        # ======================================================================

        # 3. Render historical audit log messages if they exist in state memory
        if "garmin_debug_history" in st.session_state:
            with st.expander("📝 Persistent Telemetry Audit Logs", expanded=True):
                for log_msg in st.session_state.garmin_debug_history:
                    st.write(log_msg)
                if "garmin_traceback" in st.session_state:
                    st.error("🔍 System Traceback Error Details:")
                    st.code(st.session_state.garmin_traceback, language="python")
                if st.button("🗑️  Clear Logs & Reset Cache", use_container_width=True):
                    del st.session_state.garmin_debug_history
                    st.session_state.pop("garmin_traceback", None)
                    st.rerun()
        # 4. Action Button Trigger (Disabled if date range is invalid OR if test bypass mode is active)
        #button_disabled = (start_date > end_date) or bypass_download
        button_dispabled=False
        saved_count = 0

        #if not bypass_download and st.button("🔄 Sync Garmin Data Range", use_container_width=True, disabled=button_disabled):
        if st.button("🔄 Sync Garmin Data Range", use_container_width=True):
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")

            with st.status("🛠️ Syncing with Garmin...", expanded=True) as status:
                client = Garmin("samrsanchez@gmail.com", "S@n420chez")
                try:
                    client.login()
                    activities = client.get_activities_by_date(start_str, end_str)
                    
                    for act in activities:
                        if act.get("activityType", {}).get("typeKey") == "running":
                            raw_bytes = client.download_activity(act["activityId"], dl_fmt=client.ActivityDownloadFormat.ORIGINAL)
                            
                            destination_file = os.path.join(IMPORT_FILE_PATH, f"garmin_{act['startTimeLocal'][:10]}_{act['activityId']}.fit")
                            with open(destination_file, "wb") as f:
                                f.write(raw_bytes)
                            saved_count += 1
                    
                    if saved_count > 0:
                        status.update(label=f"✅ Saved {saved_count} runs to staging folder.", state="complete")
                    else:
                        status.update(label="ℹ️ No new running tracks found.", state="complete")
                except Exception as api_err:
                    status.update(label="❌ Sync Failed", state="error")
            #st.rerun()
        # ======================================================================
        # 🚀 IMMEDIATE DATA UPLOAD DIRECT CORE (FULLY INTEGRATED EXACT REPLICA)
        # ======================================================================
        automated_files = glob.glob("data/sync/*.fit")

        if automated_files:
            # Import your application's secondary evaluation calculators
            from upload_ui import compute_current_ratings, check_single_run_patches, process_and_award_metrics
            
            st.success(f"📦 Found {len(automated_files)} Garmin files inside staging directory! Executing inline ingestion core...")
            
            with st.spinner("Processing file binaries and injecting telemetry rewards..."):
                staged_sessions = []
                total_batch_distance = 0.0
                historical_logs = getattr(player, 'history_logs', [])
                
                # --- STEP A: INITIAL PARSING & PRE-STAGING LOOP ---
                for file_path in automated_files:
                    filename = os.path.basename(file_path)
                    print("----------")
                    print(filename)
                    try:
                        with open(file_path, "rb") as f:
                            file_bytes = f.read()
                        print("FDFDFD")
                        if zipfile.is_zipfile(io.BytesIO(file_bytes)):
                            print("zip")
                            with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:

                                # Get the list of all files hidden inside this ZIP archive
                                internal_filenames = z.namelist()
                                
                                if internal_filenames:
                                    # Grab the very first file inside the ZIP archive
                                    first_file = internal_filenames[0]
                                    
                                    # Extract its raw bytes into file_bytes
                                    file_bytes = z.read(first_file)
                                    #filename=first_file
                                    filename = os.path.basename(first_file)
                                    print(f"Successfully extracted internal file: {first_file}")
                                else:
                                    print("The ZIP file is empty!")



                                #fit_filenames = [name for name in z.namelist() if name.lower().endswith('.fit')]
                                #if fit_filenames:
                                #    file_bytes = z.read(fit_filenames)
                        
                        print("*****")    
                        fit_metrics_temp = parse_garmin_fit(file_bytes)
                        print("temp here")
                        calculated_distance_miles = fit_metrics_temp["distance_mi"]
                        total_secs = int(fit_metrics_temp["duration_seconds"])
                        chk_dur = str(timedelta(seconds=total_secs))
                        chk_date = fit_metrics_temp["date"]
                        chk_dist = round(calculated_distance_miles, 2)
                        chk_dur_strip = chk_dur.strip()
                        
                        # --- DUPLICATE FILTER CHECKING ---
                        is_file_duplicate = False
                        for log_row in historical_logs:
                            if isinstance(log_row, dict):
                                h_date = str(log_row.get("Date", log_row.get("date", "")))[:10]
                                h_date = log_row.get("Date", log_row.get("date", ""))
                                if hasattr(h_date, "strftime"):
                                    h_date = h_date.strftime("%Y-%m-%d %H:%M:%S") # Result: "2026-08-21 14:23:11"

                                print("((()))(()(")
                                print(chk_date)
                                print(h_date)
                                h_dist = round(float(log_row.get("Distance (Miles)", log_row.get("distance_mi", 0.0))), 2)
                                h_dur = str(log_row.get("Duration", log_row.get("duration", ""))).strip()
                                if h_date == chk_date and h_dist == chk_dist and h_dur == chk_dur_strip:
                                    print("Duplicate")
                                    is_file_duplicate = True
                                    break
                        print("here")
                                    
                        if is_file_duplicate:
                            st.warning(f"⚠️ Filtered Out Duplicate: `{filename}` already exists in database record profile logs.")
                            print("Remove")
                            os.remove(file_path)
                            continue
                            
                        staged_sessions.append({
                            "name": filename, "date": fit_metrics_temp["date"],  
                            "dist": round(calculated_distance_miles, 2), "duration": chk_dur,  
                            "pace": fit_metrics_temp["pace"], "ele": fit_metrics_temp["elevation_gain_ft"], 
                            "calories": fit_metrics_temp["calories"], "splits": fit_metrics_temp["splits"],
                            "aerobic_decoupling_percent": fit_metrics_temp.get("aerobic_decoupling_percent", 0.0),
                            "ambient_temp_f": fit_metrics_temp.get("ambient_temp_f", 72.0),
                            "type": "FIT Activity", "file_disk_path": file_path
                        })
                        total_batch_distance += calculated_distance_miles
                        
                    except Exception as e:
                        st.error(f"❌ Core parsing pipeline failure on item {filename}: {str(e)}")
                        try: os.remove(file_path)
                        except Exception: pass
                # --- STEP B: THE NATIVE COMMIT PIPELINE REPLICA (BLOCK 5 CONTINUED) ---
                if staged_sessions:
                    try:
                        if not hasattr(player, 'history_logs'): player.history_logs = []
                        if not hasattr(player, 'unlocked_badges'): player.unlocked_badges = []
                        if not hasattr(player, 'calorie_bank_balance'): player.calorie_bank_balance = 5000
                        if not hasattr(player, 'calorie_bank_total_earned'): player.calorie_bank_total_earned = 5000
                        if not hasattr(player, 'pantry_purchase_counts'): player.pantry_purchase_counts = {}
                        if not hasattr(player, 'pantry_single_trophies'): player.pantry_single_trophies = []
                        if not hasattr(player, 'pantry_cuisine_trophies'): player.pantry_cuisine_trophies = []

                        pre_upload_badge_count = len(player.unlocked_badges)
                        total_gold_rewarded, total_xp_gained = 0, 0
                        total_calories_ingested = 0
                        
                        for s in staged_sessions:
                            z1, z2, z3, z4, z5 = 15, 45, 20, 15, 5 
                            gold = max(2, int(float(s['dist']) * 10))
                            xp = max(5, int(float(s['dist']) * 50))
                            total_gold_rewarded += gold
                            total_xp_gained += xp
                            
                            try:
                                raw_val = s.get('calories', 0)
                                session_kcal = int(float(raw_val)) if raw_val is not None else 0
                            except (ValueError, TypeError):
                                session_kcal = 0
                                
                            if session_kcal <= 0 and float(s.get('dist', 0)) > 0:
                                session_kcal = int(float(s['dist']) * 100)
                                s['calories'] = session_kcal
                                
                            total_calories_ingested += session_kcal
                            
                            raw_s_pace = s.get('pace', 0.0)
                            if raw_s_pace is None or raw_s_pace == "00:00" or (isinstance(raw_s_pace, float) and (math.isnan(raw_s_pace) or raw_s_pace <= 0)):
                                clean_pace_val = "00:00"
                                pace_text = "—"
                            elif isinstance(raw_s_pace, str) and ":" in raw_s_pace:
                                clean_pace_val = raw_s_pace
                                pace_text = raw_s_pace
                            else:
                                try:
                                    clean_pace_val = float(raw_s_pace)
                                    pace_text = f"{clean_pace_val:.2f}"
                                except (ValueError, TypeError):
                                    clean_pace_val = "11:00"
                                    pace_text = "11:00"

                            text_sentence = f"[{s['date']}] Run: {s['dist']:.2f} miles | Pace: {pace_text} min/mi | Elevation Climbed: +{s.get('ele', 0)} ft | [REWARD] +{gold}g, +{xp} XP. | [CALORIE REWARDS] +{int(s.get('calories', 0))} kcal"
                            
                            structured_log = {
                                "Date": s['date'], "Name": s.get('name', 'Run'), "Distance (Miles)": float(s['dist']),
                                "Duration": s.get('duration', '00:00:00'), "pace": clean_pace_val,
                                "Elevation (ft)": f"+{s.get('ele', 0)} ft", "splits": s.get('splits', []),
                                "text_payload": text_sentence, "aerobic_decoupling_percent": float(s.get("aerobic_decoupling_percent", 0.0)),
                                "ambient_temp_f": float(s.get("ambient_temp_f", 72.0)),
                                "zone_1_2_duration_percent": round(((z1 + z2) / max(1, z1 + z2 + z3 + z4 + z5)) * 100.0, 2)
                            }
                            player.history_logs.append(structured_log)
                            
                            if os.path.exists(s["file_disk_path"]):
                                os.remove(s["file_disk_path"])

                        player.gold = getattr(player, 'gold', 50) + total_gold_rewarded
                        player.total_xp = getattr(player, 'total_xp', 0) + total_xp_gained
                        player.calorie_bank_balance += total_calories_ingested
                        player.calorie_bank_total_earned += total_calories_ingested
                        
                        st_rating = getattr(player, 'stamina_rating', 100)
                        ef_rating = getattr(player, 'efficiency_rating', 100)
                        pw_rating = getattr(player, 'power_rating', 100)

                        post_st, post_ef, post_pw, miles_added, new_st, new_ef, new_pw = compute_current_ratings(
                            player.history_logs, st_rating, ef_rating, pw_rating
                        )
                        player.stamina_rating, player.efficiency_rating, player.power_rating = new_st, new_ef, new_pw
                        player.stamina_level, player.efficiency_level, player.power_level = post_st, post_ef, post_pw

                        if player.history_logs:
                            for entry in player.history_logs[-len(staged_sessions):]:
                                discovered_patches = check_single_run_patches(entry.copy())
                                entry["earned_patches"] = list(discovered_patches) if isinstance(discovered_patches, list) else discovered_patches
                                
                                emoji_strip = "".join([p.get("icon", "") for p in discovered_patches if p.get("icon")])
                                if emoji_strip and "🎖️ Rewards:" not in entry.get("text_payload", ""):
                                    entry["text_payload"] = entry.get("text_payload", "").strip() + f" | 🎖️ Rewards: {emoji_strip}"

                                for patch in discovered_patches:
                                    if patch["id"] not in player.unlocked_badges:
                                        player.unlocked_badges.append(patch["id"])

                            
                            


                                                # =========================================================================
                        # 🛡️ FIXED: TRANSACT-SAFE APPEND CORE FOR GARMIN DIRECT CLOUD SYNC
                        # =========================================================================
                        import json
                        import os

                        if os.path.exists(FILE_PATH) and os.path.getsize(FILE_PATH) > 0:
                            try:
                                with open(FILE_PATH, 'r', encoding='utf-8') as db_file:
                                    fresh_disk_data = json.load(db_file)
                            except json.JSONDecodeError:
                                fresh_disk_data = {}
                        else:
                            fresh_disk_data = {}

                        if "history_logs" not in fresh_disk_data:
                            fresh_disk_data["history_logs"] = []
                        if "unlocked_badges" not in fresh_disk_data:
                            fresh_disk_data["unlocked_badges"] = []

                        fresh_logs = getattr(player, 'history_logs', [])
                        fresh_badges = getattr(player, 'unlocked_badges', [])

                        for log in fresh_logs:
                            is_dup = any(
                                str(old_log.get("Date"))[:19] == str(log.get("Date"))[:19] and 
                                abs(float(old_log.get("Distance (Miles)", 0.0)) - float(log.get("Distance (Miles)", 0.0))) < 0.01
                                for old_log in fresh_disk_data["history_logs"] if isinstance(old_log, dict)
                            )
                            if not is_dup:
                                fresh_disk_data["history_logs"].append(log)

                        for badge in fresh_badges:
                            if badge not in fresh_disk_data["unlocked_badges"]:
                                fresh_disk_data["unlocked_badges"].append(badge)

                        fresh_disk_data['level'] = player.level
                        fresh_disk_data['total_xp'] = player.total_xp
                        fresh_disk_data['gold'] = player.gold
                        fresh_disk_data['fatigue'] = player.fatigue
                        fresh_disk_data['calorie_bank_balance'] = player.calorie_bank_balance
                        fresh_disk_data['calorie_bank_total_earned'] = player.calorie_bank_total_earned
                        fresh_disk_data['pantry_purchase_counts'] = player.pantry_purchase_counts
                        fresh_disk_data['pantry_single_trophies'] = player.pantry_single_trophies
                        fresh_disk_data['pantry_cuisine_trophies'] = player.pantry_cuisine_trophies

                        if fresh_disk_data["history_logs"]:
                            fresh_disk_data = process_and_award_metrics_in_memory(fresh_disk_data, fresh_disk_data["history_logs"][-1])

                        # 7. Write to disk exactly ONCE to guarantee structural integrity
                        with open(FILE_PATH, 'w', encoding='utf-8') as db_file:
                            json.dump(fresh_disk_data, db_file, default=str, indent=4, ensure_ascii=False)

                        # =========================================================================
                        # 🟢 FIXED: SAFE BRACKET INITIALIZATION CHECKS TO ELIMINATE THE KEYERROR
                        # =========================================================================
                        if "profile" in st.session_state and isinstance(st.session_state["profile"], dict):
                            st.session_state["profile"]["history_logs"] = list(fresh_disk_data.get("history_logs", []))
                            st.session_state["profile"]["unlocked_badges"] = list(fresh_disk_data.get("unlocked_badges", []))
                        else:
                            # If profile is missing from session state on reload, initialize it safely right here
                            st.session_state["profile"] = dict(fresh_disk_data)





                        if hasattr(player, 'final_metric_data'):
                            player.final_metric_data = current_database.get("final_metric_data", {})





                        player.history_logs = fresh_disk_data.get("history_logs", [])
                        player.unlocked_badges = fresh_disk_data.get("unlocked_badges", [])
                        if hasattr(player, 'final_metric_data'):
                            player.final_metric_data = fresh_disk_data.get("final_metric_data", {})
                        
                        post_upload_badges = fresh_disk_data.get("unlocked_badges", [])
                        st.session_state.last_sync_deltas = {
                            "gold": total_gold_rewarded, "xp": total_xp_gained, "count": len(staged_sessions),
                            "miles_added": sum(float(s['dist']) for s in staged_sessions),
                            "batch_patches_earned": max(0, len(post_upload_badges) - pre_upload_badge_count)  
                        }
                        
                        st.cache_data.clear()
                        st.session_state.uploader_reset_token = st.session_state.get("uploader_reset_token", 0) + 1
                        st.balloons()
                        st.toast(f"🏃 Success! Direct upload complete: +{total_gold_rewarded}g | +{total_xp_gained} XP added directly to your profile.", icon="🔥")
                        st.rerun()
                        
                    except Exception as commit_err:
                        st.error(f"❌ Ingestion Commit Failure: {str(commit_err)}")
        else:
            st.info("ℹ️ Staging directory 'data/sync' is currently clear of tracks. Put files there or toggle off test mode to run a download pull.")

    with manual_tab:
        st.markdown("---")
        render_upload_interface(player, FILE_PATH, FILE_PATH)




































elif st.session_state.active_tab_selection == 'Biometric Coliseum':
    render_coliseum(player, FILE_PATH)
elif st.session_state.active_tab_selection == 'Pro Shop & Garage':
    render_shop_interface(player, FILE_PATH)
    #st.markdown("---")
    #st.markdown("### 🏎 Vault Garage: Acquired Performance Machines")
    #owned_cars = getattr(player, 'inventory', [])
    #if not owned_cars:
    #    st.info("ℹ Your garage bay is currently empty.")
    #else:
    #    g_cols = st.columns(min(4, len(owned_cars)))
    #    for idx, car in enumerate(owned_cars):
    #        with g_cols[idx % 4]:
    #            car_rank = int(getattr(player, 'equipped_gear', {}).get(car, 1))
    #            st.info(f"🚘 **{car}**\n\n`Tuning Rank: +{car_rank}`")
elif st.session_state.active_tab_selection == '🏪 Calorie Pantry Market':
    render_pantry_interface(player, FILE_PATH)
#elif st.session_state.active_tab_selection == 'Performance Analytics':
#    st.markdown('## 📊 Performance Analytics Dashboard')
#    chart_runs = st.session_state.profile.get("history_logs", [])
#    
#    if chart_runs and len(chart_runs) > 0:
#        df_analytics_view = pd.DataFrame(chart_runs)
#        
#        # 🛡 FIX: Map inconsistent json log history keys to columns BEFORE sorting
#        if "Calendar Date" not in df_analytics_view.columns and "date" in df_analytics_view.columns:
#            df_analytics_view["Calendar Date"] = df_analytics_view["date"]
#        if "Distance (Miles)" not in df_analytics_view.columns and "dist" in df_analytics_view.columns:
#            df_analytics_view["Distance (Miles)"] = df_analytics_view["dist"]
#            
#        if "Calendar Date" not in df_analytics_view.columns:
#            df_analytics_view["Calendar Date"] = pd.Timestamp.now().strftime("%Y-%m-%d")
#        if "Distance (Miles)" not in df_analytics_view.columns:
#            df_analytics_view["Distance (Miles)"] = 0.0
#
#        df_analytics_view = df_analytics_view.sort_values(by='Calendar Date')
#        
#        base_chart = alt.Chart(df_analytics_view).encode(x='Calendar Date:T')
#        bars_distance = base_chart.mark_bar(color='#3b82f6', opacity=0.6).encode(
#            y=alt.Y('Distance (Miles):Q', title='Distance (mi)')
#        )
#        st.altair_chart(bars_distance, use_container_width=True)
#    else:
#        st.info('Gather activity logs to map telemetry parameters.')
elif st.session_state.active_tab_selection == 'Training Ledger':
    render_training_ledger(player)
elif st.session_state.active_tab_selection == "🏆 Showroom & PRs":
    # 🎯 FIX: Recover the raw_profile dictionary from session state.
    # This prevents the NameError by ensuring the variable is fully defined
    # before its keys ('history_logs' and 'defense_state') are accessed below.
    raw_profile = st.session_state.get("profile", {})

    raw_logs_list = raw_profile.get("history_logs", [])
    clean_dicts_list = []
    if isinstance(raw_logs_list, list):
        for entry in raw_logs_list:
            if isinstance(entry, dict):
                clean_dicts_list.append(entry)

    if len(clean_dicts_list) > 0:
        df_raw_wrapper = pd.DataFrame(clean_dicts_list)
        df_instances = showroom_eng.compile_all_award_instances(df_raw_wrapper)
    else:
        df_instances = pd.DataFrame(columns=["award_code", "date", "metric", "type", "details"])

    if "award_code" not in df_instances.columns:
        df_instances = pd.DataFrame(columns=["award_code", "date", "metric", "type", "details"])

    defense_state = raw_profile.get("defense_state", "stable")

    # Forward the pre-allocated second column container layout to the renderer function
    render_trophy_showroom_tab(df_instances, defense_state, popout_container=sb_col2)

#elif st.session_state.active_tab_selection == 'Calendar':
#    show_cal(player)
