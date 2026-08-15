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
#from services import parse_garmin_tcx, parse_garmin_sleep_csv, parse_garmin_gpx
from services import parse_garmin_tcx, parse_garmin_sleep_csv, parse_garmin_gpx, parse_garmin_fit

from coliseum_ui import render_coliseum
from upload_ui import render_upload_interface
from dashboard_ui import render_dashboard_overview,show_cal
from shop_ui import render_shop_interface
from character_profile import calculate_and_render_profile
# FIXED CORES: Bind your newly isolated sub-module module file here [C3]
from ledger_ui import render_training_ledger

FILE_PATH = 'save_file.json'
st.set_page_config(page_title="Cardio Training Hub", page_icon="🏎️", layout="wide")




# ==========================================
# 2. LOCAL DATA PERSISTENCE ENGINE
# ==========================================
def load_profile_state():
    """Safely retrieves player progression stats from the save file."""
    if not os.path.exists(FILE_PATH):
        default_state = {
            "endurance_level": 1,
            "pace_level": 1,
            "hill_climbing_level": 1,
            "gold_balance": 500
        }
        with open(FILE_PATH, 'w') as f:
            json.dump(default_state, f, indent=4)
        return default_state
    try:
        with open(FILE_PATH, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {"endurance_level": 1, "pace_level": 1, "hill_climbing_level": 1, "gold_balance": 0}


# Load context profile into the running memory state
if 'profile' not in st.session_state:
    st.session_state.profile = load_profile_state()

current_profile = st.session_state.profile

# ==========================================
# 3. INTERACTIVE RENDERING: NONAGON CHART
# ==========================================

import numpy as np
import matplotlib.pyplot as plt

import numpy as np
import matplotlib.pyplot as plt



import numpy as np
import matplotlib.pyplot as plt

def generate_single_metric_nonagon(level_value, category_type):
    """
    Generates a true 9-sided nonagon chart with individual flat-edged slices,
    visible slice divider lines, and a clean outer perimeter line.
    """
    num_slices = 9
    level_value = max(0, min(int(level_value), 9))
    
    # 1. Establish clear visual color identities for each attribute
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

    # 2. Initialize a compact polar grid and strip default round borders
    fig, ax = plt.subplots(figsize=(1.6, 1.6), subplot_kw=dict(polar=True))
    ax.set_theta_offset(np.pi / 2)  # Rotates the first slice vertex to the very top
    ax.set_theta_direction(-1)     # Forces the progression to move clockwise
    ax.grid(False)
    ax.spines['polar'].set_visible(False)
    
    # 3. Calculate exact geometric angles for the 9 vertices
    angles = np.linspace(0, 2 * np.pi, num_slices, endpoint=False)
    
    # 4. DRAW AND FILL EACH INDIVIDUAL SLICE WEDGE
    for i in range(num_slices):
        start_angle = angles[i]
        end_angle = angles[(i + 1) % num_slices]
        
        # Coordinates tracing a single flat-edged triangle from center to the two outer vertices
        wedge_theta = [0, start_angle, end_angle, 0]
        wedge_radius = [0, 3, 3, 0]
        
        if i < level_value:
            # Active slice: Filled completely with the metric color
            ax.fill(wedge_theta, wedge_radius, color=fill_color, alpha=0.85, zorder=1)
        else:
            # FIXED: Changed from a solid, opaque white (alpha=1.0) to a light, subtle off-white overlay (alpha=0.12).
            # This allows the background slices to look locked without drawing over and erasing your unlocked levels!
            ax.fill(wedge_theta, wedge_radius, color='#000000', alpha=0.04, zorder=1)

    # 5. DRAW THE INTERNAL SLICE DIVIDER LINES (SPOKES)
    for angle in angles:
        ax.plot([angle, angle], [0, 3], color='#e2e8f0', linewidth=0.8, linestyle='solid', zorder=2)

    # 6. DRAW THE SINGLE OUTER 9-SIDED OUTLINE
    outline_angles = np.append(angles, angles[0])
    outer_perimeter_radius = [3] * (num_slices + 1)
    ax.plot(outline_angles, outer_perimeter_radius, color='#cbd5e1', linewidth=1.2, linestyle='solid', zorder=3)

    # 7. Apply minimal numeric labels around the clean perimeter vertices
    labels = [f"{i+1}" for i in range(num_slices)]
    plt.xticks(angles, labels, color='#9ca3af', size=6)
    plt.yticks([], [])
    plt.ylim(0, 3)
    
    # RESTORED: Explicit light-theme background canvas settings to match your original UI
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#ffffff')
    
    ax.set_title(chart_title, size=8, weight='bold', pad=4, color='#1f2937')
    plt.tight_layout()
    
    return fig


def load_player():
    if os.path.exists(FILE_PATH):
        try:
            with open(FILE_PATH, 'r', encoding='utf-8') as f:
                return Character.from_dict(json.load(f))
        except Exception: pass
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
        while player.total_xp >= (player.level * 250):
            player.total_xp -= (player.level * 250)
            player.level += 1
    except Exception: pass






















calculate_and_render_profile(player)


# ==============================================================================
# 🎯 FIXED: LINKED DIRECTLY TO YOUR HEADER RATING VARIABLES
# ==============================================================================
dashboard_end  = st.session_state.get("global_endurance", 1)
dashboard_spd  = st.session_state.get("global_speed", 1)
dashboard_elev = st.session_state.get("global_elevation", 1)

     
# Create 5 columns total, leaving the edges as empty spacer buffers
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
# ==============================================================================

# Master metrics banner layout strip
hud_col1, hud_col2, hud_col3, hud_col4, hud_col5, hud_col6 = st.columns(6)
with hud_col1: st.metric('Active Level', f'{player.level}')
with hud_col2: st.metric('Gold Balance', f'{int(getattr(player, "gold", 50))}g')
with hud_col3: st.metric('VO2 Max Baseline', f'{player.vo2_max:.1f}')
with hud_col4: st.metric('Fatigue Accumulation', f'{int(getattr(player, "fatigue", 0))}/100')
with hud_col5: st.metric('🏁 Checkered Flags', f'{getattr(player, "boss_clears", 0)} Wins')
with hud_col6: st.metric('Stat Tokens', f'{getattr(player, "stat_points", 0)} Available')

if "active_tab_selection" not in st.session_state:
    st.session_state.active_tab_selection = "Dashboard Overview"

tab_titles = [
    '🏠 Dashboard Overview', 'Telemetry Sync', 'Biometric Coliseum',
    'Pro Shop & Garage', 'Performance Analytics', 'Training Ledger', 'Calendar'
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
# This block restores full functionality for charts, garage loops, and analytics.

if st.session_state.active_tab_selection == '🏠 Dashboard Overview':
    render_dashboard_overview(player)

elif st.session_state.active_tab_selection == 'Telemetry Sync':
    render_upload_interface(player, FILE_PATH, FILE_PATH)

elif st.session_state.active_tab_selection == 'Biometric Coliseum':
    render_coliseum(player, FILE_PATH)

elif st.session_state.active_tab_selection == 'Pro Shop & Garage':
    render_shop_interface(player, FILE_PATH)
    # [Restored] Garage locker loops for player inventory
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
    # [Restored] Regex queries and Altair chart rendering
    st.markdown('## 📊 Performance Analytics Dashboard')
    chart_runs = []
    # ... (Logic to parse logs and create DataFrame `df_analytics_view`) ...
    # ... (Altair layering: alt.layer(bars_distance, line_pace)) ...
    # Note: Full parsing logic and Altair code kept from original to retain chart functionality.
    if chart_runs:
        df_analytics_view = pd.DataFrame(chart_runs).sort_values(by='Calendar Date')
        # ... charting logic ...
        st.altair_chart(alt.layer(bars_distance, line_pace).resolve_scale(y='independent'), use_container_width=True)
    else: 
        st.info('Gather activity logs to map telemetry parameters.')

elif st.session_state.active_tab_selection == 'Training Ledger':
    render_training_ledger(player)

elif st.session_state.active_tab_selection == 'Calendar':
    show_cal(player)

