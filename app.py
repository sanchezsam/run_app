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
            # Inactive slice: Filled with an off-white placeholder background
            ax.fill(wedge_theta, wedge_radius, color='#f9fafb', alpha=1.0, zorder=1)

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

# 1. Read parameters using safe fallback defaults (now scaled 1-9)
endurance = current_profile.get('endurance_level', 1)
speed = current_profile.get('pace_level', 1)
elevation = current_profile.get('hill_climbing_level', 1)

# Create 5 columns total, leaving the edges as empty spacer buffers
_, col1, col2, col3, _ = st.columns([1, 2, 2, 2, 1])

with col1:
    st.metric("🔋 Endurance", f"{endurance} / 9")
    st.pyplot(generate_single_metric_nonagon(endurance, 'Endurance'))

with col2:
    st.metric("⚡ Speed", f"{speed} / 9")
    st.pyplot(generate_single_metric_nonagon(speed, 'Speed'))

with col3:
    st.metric("⛰️ Elevation", f"{elevation} / 9")
    st.pyplot(generate_single_metric_nonagon(elevation, 'Elevation'))


# Master metrics banner layout strip
hud_col1, hud_col2, hud_col3, hud_col4, hud_col5, hud_col6 = st.columns(6)
with hud_col1: st.metric('Active Level', f'{player.level}')
with hud_col2: st.metric('Gold Balance', f'{int(getattr(player, "gold", 50))}g')
with hud_col3: st.metric('VO2 Max Baseline', f'{player.vo2_max:.1f}')
with hud_col4: st.metric('Fatigue Accumulation', f'{int(getattr(player, "fatigue", 0))}/100')
with hud_col5: st.metric('🏁 Checkered Flags', f'{getattr(player, "boss_clears", 0)} Wins')
with hud_col6: st.metric('Stat Tokens', f'{getattr(player, "stat_points", 0)} Available')


tab0, tab1, tab2, tab3, tab4, tab5,tab6 = st.tabs([
    '🏠 Dashboard Overview', 'Telemetry  Sync', 'Biometric Coliseum', 'Pro Shop & Garage', 'Performance Analytics', 'Training Ledger','Calendar'
])

with tab0: 
    render_dashboard_overview(player)

with tab1: 
    render_upload_interface(player, FILE_PATH, FILE_PATH)

with tab2: 
    render_coliseum(player, FILE_PATH)

with tab3:
    render_shop_interface(player, FILE_PATH)
    st.markdown("---")
    st.markdown("### 🏎️ Vault Garage: Acquired Performance Machines")
    owned_cars = getattr(player, 'inventory', [])
    if not owned_cars:
        st.info("ℹ️ Your garage bay is currently empty. Purchase a performance machine from the catalog above!")
    else:
        st.caption("Your collected racing vehicles currently tuned and active inside your locker vault storage frames:")
        g_cols = st.columns(min(4, len(owned_cars)))
        for idx, car in enumerate(owned_cars):
            with g_cols[idx % 4]:
                car_rank = int(getattr(player, 'equipped_gear', {}).get(car, 1))
                st.info(f"🚘 **{car}**\n\n`Tuning Rank: +{car_rank}`")

with tab4:
    st.markdown('## 📊 Performance Analytics Dashboard')
    chart_runs = []
    for log in getattr(player, 'history_logs', []):
        log_str = str(log)
        if 'miles' in log_str.lower() and 'slept' not in log_str.lower():
            try:
                dist_match = re.search(r'(?:Run|run|ran|distance):?\s*([0-9.]+)', log_str, re.IGNORECASE)
                if not dist_match: dist_match = re.search(r'([0-9.]+)\s*(?:miles|mi)', log_str, re.IGNORECASE)
                pace_match = re.search(r'Pace:\s*([0-9.]+)', log_str, re.IGNORECASE)
                date_match = re.search(r'\[([0-9-]+)\]', log_str)
                if dist_match:
                    dt_obj = datetime.strptime(date_match.group(1)[:10], '%Y-%m-%d') if date_match else datetime.now()
                    chart_runs.append({'Calendar Date': dt_obj, 'Daily Distance (Miles)': float(dist_match.group(1)), 'Daily Average Pace (min/mi)': float(pace_match.group(1)) if pace_match else 8.50})
            except Exception: pass
    if chart_runs:
        df_analytics_view = pd.DataFrame(chart_runs).sort_values(by='Calendar Date')
        base_timeline = alt.Chart(df_analytics_view).encode(x=alt.X('Calendar Date:T'))
        bars_distance = base_timeline.mark_bar(color='#10b981', opacity=0.75).encode(y=alt.Y('Daily Distance (Miles):Q'))
        line_pace = base_timeline.mark_line(color='#3b82f6', point=True).encode(y=alt.Y('Daily Average Pace (min/mi):Q', scale=alt.Scale(zero=False)))
        st.altair_chart(alt.layer(bars_distance, line_pace).resolve_scale(y='independent'), use_container_width=True)
    else: st.info('Gather activity logs to map telemetry parameters.')

with tab5:
    # FIXED PANEL LOCATION: Render sub-module routing view call from newly isolated ledger file [C3]
    render_training_ledger(player)
with tab6:
     show_cal(player)
