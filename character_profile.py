# -*- coding: utf-8 -*-
import streamlit as st
import json
import re
from datetime import datetime, timedelta

def calculate_and_render_profile(player):
    now_date = datetime.now()
    three_weeks_ago = now_date - timedelta(days=21)
    
    total_3wk_miles = 0.0
    max_single_run_elevation = 0.0
    fastest_pace_in_window = 999.0
    valid_sessions_count = 0
    
    # Parse data rows within the 3-week rolling timeline window
    raw_logs = getattr(player, 'history_logs', [])
    for log in raw_logs:
        log_str = str(log)
        if 'miles' in log_str.lower() and 'slept' not in log_str.lower():
            try:
                date_match = re.search(r'\[([0-9-]+)\]', log_str)
                if date_match:
                    log_dt = datetime.strptime(date_match.group(1)[:10], '%Y-%m-%d')
                    if log_dt >= three_weeks_ago:
                        dist_match = re.search(r'Run:\s*([0-9.]+)', log_str, re.IGNORECASE)
                        if not dist_match:
                            dist_match = re.search(r'(?:ran|run):?\s*([0-9.]+)', log_str, re.IGNORECASE)
                        
                        pace_match = re.search(r'Pace:\s*([0-9.]+)', log_str, re.IGNORECASE)
                        ele_match = re.search(r'Elevation\s*Climbed:\s*\+?([0-9.]+)', log_str, re.IGNORECASE)
                        
                        if dist_match:
                            total_3wk_miles += float(dist_match.group(1))
                            valid_sessions_count += 1
                        if ele_match:
                            curr_ele = float(ele_match.group(1))
                            if curr_ele > max_single_run_elevation: max_single_run_elevation = curr_ele
                        if pace_match:
                            current_pace = float(pace_match.group(1))
                            if 2.0 < current_pace < fastest_pace_in_window: fastest_pace_in_window = current_pace
            except Exception: pass
            
    # Arcade 1–9 ratings math scales
    endurance_rating = max(1, min(9, int((total_3wk_miles / 300.0) * 9)))
    if fastest_pace_in_window < 900.0 and fastest_pace_in_window > 0:
        if fastest_pace_in_window <= 5.50: speed_rating = 9
        else: speed_rating = max(1, min(9, int(9 - ((fastest_pace_in_window - 5.50) * 1.5))))
    else: speed_rating = 1
    strength_rating = max(1, min(9, int((max_single_run_elevation / 6000.0) * 9)))
    
    # Flashing Overdrive Warnings
    if total_3wk_miles >= 45.0:
        st.error("🔥 🔥 🔥 RUNNER RECORD ON FIRE !! SPRINT OVERDRIVE ENGAGED !! 🔥 🔥 🔥")
    elif valid_sessions_count >= 3:
        st.warning("⚡ ATHLETE IS HEATING UP !")

    # CONDENSED ARCADE RUNNER HUD
    with st.container(border=True):
        st.markdown(f"🎰 **TRACK CHAMPIONSHIP ROSTER MATRIX** | CREDIT INSERTED | **STAGES COMPLETED: {valid_sessions_count}**")
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.markdown(f"🔋 **AEROBIC CAPACITY / ENDURANCE** `[ {endurance_rating} / 9 ]`")
            st.progress(float(endurance_rating / 9.0))
            st.caption(f"Volume Covered: {total_3wk_miles:.1f} / 300.0 Mi")
            
        with c2:
            st.markdown(f"⚡ **SPRINT VELOCITY / PACE** `[ {speed_rating} / 9 ]`")
            st.progress(float(speed_rating / 9.0))
            pace_str = f"{int(fastest_pace_in_window)}:{(fastest_pace_in_window%1)*60:02.0f} min/mi" if fastest_pace_in_window < 900.0 else "N/A"
            st.caption(f"PR Split Time: {pace_str} (Target: 5:30)")
            
        with c3:
            st.markdown(f"⛰️ **HILL-CLIMBING ELEVATION FORCE** `[ {strength_rating} / 9 ]`")
            st.progress(float(strength_rating / 9.0))
            st.caption(f"Peak Ascent Ascent: {int(max_single_run_elevation)} / 6,000 ft")

