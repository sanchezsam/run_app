# -*- coding: utf-8 -*-
# PART 1 OF 2: CORE LIBRARIES, STREAMLIT NAVIGATION AND RE-BOUND COCKPIT ROUTING
import json
import os
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

FILE_PATH = 'save_file.json'

st.set_page_config(page_title="Cardio Training Hub", page_icon="🏎", layout="wide")

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
        "power_xp": 3200, "boss_clears": 15, "boss_levels": [], "history_logs": [],
        # 🥞 Pantry Core Ledger persistent properties
        "calorie_bank_balance": 5000, 
        "calorie_bank_total_earned": 5000, 
        "pantry_purchase_counts": {}, 
        "pantry_single_trophies": [], 
        "pantry_cuisine_trophies": [] 
    }

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

# ==============================================================================
# ⚡ THE SOURCE OF TRUTH OVERRIDE (MAXIMUM BYPASS BLANKET)
# ==============================================================================
st.session_state.profile = load_profile_state()
st.session_state.initialized = True
st.session_state.profile_created = True
st.session_state.profile_setup = True
st.session_state.user_initialized = True
st.session_state.account_created = True
st.session_state.setup_complete = True

if isinstance(st.session_state.profile, dict):
    st.session_state.player_level = st.session_state.profile.get("level", 25)
    st.session_state.player_gold = st.session_state.profile.get("gold", 9500)
    st.session_state.player_xp = st.session_state.profile.get("total_xp", 8750)
    st.session_state.calorie_bank_balance = st.session_state.profile.get("calorie_bank_balance", 5000)
    st.session_state.pantry_purchase_counts = st.session_state.profile.get("pantry_purchase_counts", {})
    st.session_state.pantry_single_trophies = st.session_state.profile.get("pantry_single_trophies", [])
    st.session_state.pantry_cuisine_trophies = st.session_state.profile.get("pantry_cuisine_trophies", [])
    st.session_state.history_logs = st.session_state.profile.get("history_logs", [])

import showroom_engine as showroom_eng
logs_array = st.session_state.profile.get("history_logs", [])
if logs_array:
    st.session_state.filtered_df = showroom_eng.sanitize_json_history_logs(logs_array)
else:
    st.session_state.filtered_df = pd.DataFrame()

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
            
            xp_per_level = 250
            if player.total_xp >= xp_per_level:
                calculated_levels_gained = player.total_xp // xp_per_level
                player.level += calculated_levels_gained
                player.total_xp %= xp_per_level
    except Exception: 
        pass

    hud_col1, hud_col2, hud_col3, hud_col4, hud_col5, hud_col6 = st.columns(6)
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

    with hud_col1: st.metric('Active Level', f'{player.level}')
    with hud_col2: st.metric('Gold Balance', f'{int(getattr(player, "gold", 50))} g')
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
    st.caption(f"Logged in as: **{getattr(player, 'name', 'Racer 1')}**")
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
        if st.button("📊 Performance Analytics", key="nav_sidebar_anly", type="primary" if st.session_state.active_tab_selection == "Performance Analytics" else "secondary", use_container_width=True):
            st.session_state.active_tab_selection = "Performance Analytics"
            st.rerun()
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
#if st.session_state.active_tab_selection == "🏆 Showroom & PRs":
#    raw_profile = st.session_state.get("profile", {})
#    raw_logs_list = raw_profile.get("history_logs", [])
#    clean_dicts_list = []
#    if isinstance(raw_logs_list, list):
#        for entry in raw_logs_list:
#            if isinstance(entry, dict):
#                clean_dicts_list.append(entry)
#                
#    if len(clean_dicts_list) > 0:
#        df_raw_wrapper = pd.DataFrame(clean_dicts_list)
#        df_instances = showroom_eng.compile_all_award_instances(df_raw_wrapper)
#    else:
#        df_instances = pd.DataFrame(columns=["award_code", "date", "metric", "type", "details"])
#        
#    if "award_code" not in df_instances.columns:
#        df_instances = pd.DataFrame(columns=["award_code", "date", "metric", "type", "details"])
#        
#    defense_state = raw_profile.get("defense_state", "stable")
#    
#    # Forward the now roomier sb_col2 container layout to the renderer function
#    render_trophy_showroom_tab(df_instances, defense_state, popout_container=sb_col2)
#
#elif st.session_state.active_tab_selection == 'Calendar':
#    show_cal(player)






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
elif st.session_state.active_tab_selection == 'Performance Analytics':
    st.markdown('## 📊 Performance Analytics Dashboard')
    chart_runs = st.session_state.profile.get("history_logs", [])
    
    if chart_runs and len(chart_runs) > 0:
        df_analytics_view = pd.DataFrame(chart_runs)
        
        # 🛡 FIX: Map inconsistent json log history keys to columns BEFORE sorting
        if "Calendar Date" not in df_analytics_view.columns and "date" in df_analytics_view.columns:
            df_analytics_view["Calendar Date"] = df_analytics_view["date"]
        if "Distance (Miles)" not in df_analytics_view.columns and "dist" in df_analytics_view.columns:
            df_analytics_view["Distance (Miles)"] = df_analytics_view["dist"]
            
        if "Calendar Date" not in df_analytics_view.columns:
            df_analytics_view["Calendar Date"] = pd.Timestamp.now().strftime("%Y-%m-%d")
        if "Distance (Miles)" not in df_analytics_view.columns:
            df_analytics_view["Distance (Miles)"] = 0.0

        df_analytics_view = df_analytics_view.sort_values(by='Calendar Date')
        
        base_chart = alt.Chart(df_analytics_view).encode(x='Calendar Date:T')
        bars_distance = base_chart.mark_bar(color='#3b82f6', opacity=0.6).encode(
            y=alt.Y('Distance (Miles):Q', title='Distance (mi)')
        )
        st.altair_chart(bars_distance, use_container_width=True)
    else:
        st.info('Gather activity logs to map telemetry parameters.')
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

elif st.session_state.active_tab_selection == 'Calendar':
    show_cal(player)
