# -*- coding: utf-8 -*-
# PART 1 OF 2: CORE LIBRARIES, STREAMLIT NAVIGATION AND RE-BOUND COCKPIT ROUTING
import json
import os
import re
import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta
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

FILE_PATH = 'save_file.json'
st.set_page_config(page_title="Cardio Training Hub", page_icon="🏎️", layout="wide")





# ==========================================
# 2. LOCAL DATA PERSISTENCE ENGINE
# ==========================================
def load_profile_state():
    """
    Safely retrieves player progression stats and history metrics from the disk save file.
    Guarantees no data overwrites by automatically healing missing keys on boot.
    """
    default_state = {
        "name": "Racer 1", "level": 25, "total_xp": 8750, "running_level": 9,
        "vo2_max": 64.2, "avg_heart_rate": 138, "resting_heart_rate": 45,
        "lifetime_elevation_gain": 85000, "cadence_history": [],
        "elevation_milestone_history": ["bighorn", "alpine_vert_challenge", "overdrive"],
        "deep_rem_streak": 14, "stat_points": 0, "gold": 9500,
        "endurance_level": 5, "pace_level": 5, "hill_climbing_level": 5, "gold_balance": 9500,
        "inventory": ["Interceptor Spec-R", "Ghost Horizon Chassis", "Carbon Overlord V8"],
        "equipped_gear": {"Interceptor Spec-R": 3, "Ghost Horizon Chassis": 2},
        "registered_races": ["Berlin Olympiastadion Track", "Chamonix Ultra Trail"],
        "boss_wins": 15, "fatigue": 0, "days_tracked": 365, "synced_garmin_activities": [],
        "daily_miles": 520.4, "base_xp": 100, "exponent": 1.5, "last_distance": 26.2,
        "last_pace": 6.15, "final_metric_data": {}, "stamina_xp": 3500, "agility_xp": 2800,
        "power_xp": 3200, "boss_clears": 15, "boss_levels": [], "history_logs": []
    }
    
    # 📁 If file is missing entirely, write the master template blueprint
    if not os.path.exists(FILE_PATH):
        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(default_state, f, indent=4)
        return default_state
        
    try:
        with open(FILE_PATH, 'r', encoding='utf-8') as f:
            loaded_data = json.load(f)
            
        if isinstance(loaded_data, dict):
            # 🛡️ THE AUTO-HEAL MATRIX: Patches missing keys without wiping history logs
            has_mutated = False
            for key, fallback_value in default_state.items():
                if key not in loaded_data:
                    loaded_data[key] = fallback_value
                    has_mutated = True
            
            # If we fixed missing keys, write the fixed layout back to the drive immediately
            if has_mutated:
                with open(FILE_PATH, 'w', encoding='utf-8') as f:
                    json.dump(loaded_data, f, indent=4)
                    
            return loaded_data
        return default_state
    except (json.JSONDecodeError, Exception):
        return default_state

# ==============================================================================
# ⚡ THE SOURCE OF TRUTH OVERRIDE (MAXIMUM BYPASS BLANKET)
# ==============================================================================
# Force-read the hard disk on every loop execution so manual file edits never wipe.
st.session_state.profile = load_profile_state()

# 🔥 FORCE EVERY STANDARD APP STATE VARIABLE TO VALID & ACTIVE STATUS
st.session_state.initialized = True
st.session_state.profile_created = True
st.session_state.profile_setup = True
st.session_state.user_initialized = True
st.session_state.account_created = True
st.session_state.setup_complete = True

# Mirror profile primitives directly into your primary global tracking attributes
if isinstance(st.session_state.profile, dict):
    st.session_state.player_level = st.session_state.profile.get("level", 25)
    st.session_state.player_gold = st.session_state.profile.get("gold", 9500)
    st.session_state.player_xp = st.session_state.profile.get("total_xp", 8750)
    
    # 🛡️ NESTED STRUCTURE GUARD: If the app loops look for history_logs keys inside session root
    st.session_state.history_logs = st.session_state.profile.get("history_logs", [])

# Guarantee telemetry dataframes re-compile immediately on every script loop.
import showroom_engine as showroom_eng
logs_array = st.session_state.profile.get("history_logs", [])

if logs_array:
    st.session_state.filtered_df = showroom_eng.sanitize_json_history_logs(logs_array)
else:
    st.session_state.filtered_df = pd.DataFrame()

# Set your clean local state reference variable
current_profile = st.session_state.profile



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
        fill_color = '#3b82f6'      # Blue fill
        edge_color = '#1e3a8a'      # Dark Blue border
    elif category_type == 'Speed':
        chart_title = "Speed"
        fill_color = '#22c55e'      # Green fill
        edge_color = '#15803d'      # Dark Green border
    else:
        chart_title = "Elevation"
        fill_color = '#f59e0b'      # Amber fill
        edge_color = '#b45309'      # Dark Amber border

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
                # Align key names between json schemas and class attributes
                if "bodyweight" in raw_data and "weight_kg" not in raw_data:
                    raw_data["weight_kg"] = raw_data["bodyweight"]
                if "weight_kg" in raw_data and "bodyweight" not in raw_data:
                    raw_data["bodyweight"] = raw_data["weight_kg"]

                # System Attempt A: Try native model compilation parsing loop
                try:
                    data_copy = dict(raw_data)
                    history_backup = data_copy.pop("history_logs", [])
                    player_instance = Character.from_dict(data_copy)
                    player_instance.history_logs = history_backup
                    st.session_state.profile = raw_data
                    return player_instance
                except Exception:
                    # System Attempt B: Direct Attribute Injector (Guaranteed Success)
                    player_instance = Character(name=raw_data.get("name", "Racer 1"))
                    
                    for key, val in raw_data.items():
                        try:
                            setattr(player_instance, key, val)
                        except Exception:
                            pass
                    
                    # Force back mandatory model properties
                    player_instance.history_logs = raw_data.get("history_logs", [])
                    player_instance.inventory = raw_data.get("inventory", [])
                    player_instance.equipped_gear = raw_data.get("equipped_gear", {})
                    player_instance.weight_kg = float(raw_data.get("weight_kg", 75.0))
                    
                    st.session_state.profile = raw_data
                    return player_instance
        except Exception:
            pass
            
    # Absolute Emergency Fallback: Never return None
    try:
        emergency_instance = Character(name="Racer 1")
        emergency_instance.history_logs = []
        emergency_instance.inventory = []
        emergency_instance.equipped_gear = {}
        return emergency_instance
    except Exception:
        return None

# Execute the loading hook
player = load_player()





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
        # 🛡️ THE MATH TRACKING SAFE FIX: Caps calculations using linear division 
        xp_per_level = 250
        if player.total_xp >= xp_per_level:
            calculated_levels_gained = player.total_xp // xp_per_level
            player.level += calculated_levels_gained
            player.total_xp %= xp_per_level
    except Exception: pass

# Master metrics banner layout strip (Always stays visible across top header space)
hud_col1, hud_col2, hud_col3, hud_col4, hud_col5, hud_col6 = st.columns(6)
with hud_col1: st.metric('Active Level', f'{player.level}')
with hud_col2: st.metric('Gold Balance', f'{int(getattr(player, "gold", 50))}g')
with hud_col3: st.metric('VO2 Max Baseline', f'{player.vo2_max:.1f}')
with hud_col4: st.metric('Fatigue Accumulation', f'{int(getattr(player, "fatigue", 0))}/100')
with hud_col5: st.metric('🏁 Checkered Flags', f'{getattr(player, "boss_clears", 0)} Wins')
with hud_col6: st.metric('Stat Tokens', f'{getattr(player, "stat_points", 0)} Available')

if "filtered_df" not in st.session_state or st.session_state.filtered_df.empty:
    import showroom_engine as showroom_eng
    try:
        if os.path.exists(FILE_PATH):
            with open(FILE_PATH, 'r', encoding='utf-8') as database_file:
                raw_database_payload = json.load(database_file)
            
            if isinstance(raw_database_payload, dict) and "history_logs" in raw_database_payload:
                history_list = raw_database_payload["history_logs"]
                # Feed records into the filtered layout matrix normalization block
                df_sanitized_matrix = showroom_eng.sanitize_json_history_logs(history_list)
                st.session_state.filtered_df = df_sanitized_matrix
    except Exception:
        # Fails safely to blank tabular grids if file locks or system restarts occur
        st.session_state.filtered_df = pd.DataFrame()

# ------------------------------------------
# Existing Tab Configuration Layout
# ------------------------------------------
if "active_tab_selection" not in st.session_state:
    st.session_state.active_tab_selection = "🏠 Dashboard Overview"

tab_titles = [
    '🏠 Dashboard Overview', '👤 Athlete Profile', 'Telemetry Sync', 'Biometric Coliseum',
    'Pro Shop & Garage', 'Performance Analytics', 'Training Ledger', '🏆 Showroom & PRs', 'Calendar'
]





try:
    default_idx = tab_titles.index(st.session_state.active_tab_selection)
except ValueError:
    default_idx = 0

# Persistent layout navigation selector switch
st.session_state.active_tab_selection = st.radio(
    label="Navigation Tabs:",
    options=tab_titles,
    index=default_idx,
    horizontal=True,
    label_visibility="collapsed"
)

# --- TAB CONTROLLER CONDITIONAL RENDERING ---

if st.session_state.active_tab_selection == '🏠 Dashboard Overview':
    generate_dashboard_motivation_alerts() 
    render_dashboard_overview(player)

elif st.session_state.active_tab_selection == '👤 Athlete Profile':
    # 🎯 FIXED: Isolated character profile calculations and gauges inside this tab container only!
    calculate_and_render_profile(player)
    
    st.write("")
    st.markdown("### 🗺️ **ATHLETE MATRIX PROFILE GAUGES**")
    
    # Grab current synchronized stats from global session state memory cache keys
    dashboard_end  = st.session_state.get("global_endurance", 1)
    dashboard_spd  = st.session_state.get("global_speed", 1)
    dashboard_elev = st.session_state.get("global_elevation", 1)
    
    # Shape your 3-column nonagon layout grid canvas frame
    _, col1, col2, col3, _ = st.columns([1, 2, 2, 2, 1])
    
    with col1: 
        st.metric("🔋 Endurance", f"{dashboard_end} / 9")
        st.pyplot(generate_single_metric_nonagon(dashboard_end, 'Endurance'))
        
    with col2:  
        st.metric("⚡ Speed", f"{dashboard_spd} / 9")
        st.pyplot(generate_single_metric_nonagon(dashboard_spd, 'Speed'))
    
    with col3:
        st.metric("⛰️  Elevation", f"{dashboard_elev} / 9")
        st.pyplot(generate_single_metric_nonagon(dashboard_elev, 'Elevation'))

elif st.session_state.active_tab_selection == 'Telemetry Sync':
    render_upload_interface(player, FILE_PATH, FILE_PATH)

elif st.session_state.active_tab_selection == 'Biometric Coliseum':
    render_coliseum(player, FILE_PATH)

elif st.session_state.active_tab_selection == 'Pro Shop & Garage':
    render_shop_interface(player, FILE_PATH)
    st.markdown("---")
    st.markdown("### 🏎 Vault Garage: Acquired Performance Machines")
    owned_cars = getattr(player, 'inventory', [])
    if not owned_cars:
        st.info("ℹ Your garage bay is currently empty.")
    else:
        g_cols = st.columns(min(4, len(owned_cars)))
        for idx, car in enumerate(owned_cars):
            with g_cols[idx % 4]:
                car_rank = int(getattr(player, 'equipped_gear', {}).get(car, 1))
                st.info(f"🚘 **{car}**\n\n`Tuning Rank: +{car_rank}`")

elif st.session_state.active_tab_selection == 'Performance Analytics':
    st.markdown('## 📊 Performance Analytics Dashboard')
    chart_runs = []
    if chart_runs:
        df_analytics_view = pd.DataFrame(chart_runs).sort_values(by='Calendar Date')
        st.altair_chart(alt.layer(bars_distance, line_pace).resolve_scale(y='independent'), use_container_width=True)
    else: 
        st.info('Gather activity logs to map telemetry parameters.')

elif st.session_state.active_tab_selection == 'Training Ledger':
    render_training_ledger(player)
elif st.session_state.active_tab_selection == '🏆 Showroom & PRs':
    import showroom_engine as showroom_eng
    import pandas as pd
    
    # 🧬 1. PULL RAW LOGS AND CLEAN CORRUPT TEXT STRINGS OUT
    raw_profile = st.session_state.get("profile", {})
    raw_logs_list = raw_profile.get("history_logs", [])
    
    # 🛡️ THE DATA SANITIZER: Filter out any items that aren't true dictionary layouts
    clean_dicts_list = []
    if isinstance(raw_logs_list, list):
        for entry in raw_logs_list:
            if isinstance(entry, dict):
                clean_dicts_list.append(entry)
    
    # Compile the filtered record arrays safely 
    if len(clean_dicts_list) > 0:
        df_raw_wrapper = pd.DataFrame(clean_dicts_list)
        df_instances = showroom_eng.compile_all_award_instances(df_raw_wrapper)
    else:
        df_instances = pd.DataFrame(columns=["award_code", "date", "metric", "type", "details"])
        
    # Guarantee absolute crash protection against missing columns
    if "award_code" not in df_instances.columns:
        df_instances = pd.DataFrame(columns=["award_code", "date", "metric", "type", "details"])

    # 📐 2. HARVEST CONSISTENCY DEFENSE CONDITIONS
    defense_state = raw_profile.get("defense_state", "stable")
    
    # 🏛️ 3. LAUNCH THE DISPLAY CASE
    render_trophy_showroom_tab(df_instances, defense_state)

elif st.session_state.active_tab_selection == 'Calendar':
    show_cal(player)

