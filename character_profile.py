# -*- coding: utf-8 -*-
import streamlit as st
import numpy as np
import json
import re
from datetime import datetime, timedelta

def calculate_and_render_profile(player):
    now_date = datetime.now()
    
    # ⏱️ SPORTS SCIENCE PHYSIOLOGICAL TIMELINE LOOKBACKS
    seven_days_ago  = now_date - timedelta(days=7)    # Acute Fatigue / Sharpness Window
    twenty_eight_ago = now_date - timedelta(days=28)  # Chronic Aerobic Engine Window
    eighty_four_ago  = now_date - timedelta(days=84)  # Macro Structural Base Window (12 Weeks)
    
    # Initialize metric accumulators
    miles_7d = 0.0
    miles_28d = 0.0
    miles_84d = 0.0
    
    total_3wk_miles = 0.0  # Kept to prevent breaking legacy HUD metrics calculations
    valid_sessions_count = 0
    
    # Speed & Elevation variables
    fastest_pace_in_window = 999.0
    total_84d_elevation = 0.0
    max_single_run_elevation = 0.0
    
    # Parse data rows across the expanded 84-day macro training base timeline
    raw_logs = getattr(player, 'history_logs', [])
    for log in raw_logs:
        log_str = str(log)
        if 'miles' in log_str.lower() and 'slept' not in log_str.lower():
            try:
                date_match = re.search(r'\[([0-9-]+)\]', log_str)
                if date_match:
                    log_dt = datetime.strptime(date_match.group(1)[:10], '%Y-%m-%d')
                    
                    # Cut off processing if log sits beyond our 12-week macro database window
                    if log_dt < eighty_four_ago:
                        continue
                        
                    dist_match = re.search(r'Run:\s*([0-9.]+)', log_str, re.IGNORECASE)
                    if not dist_match:
                        dist_match = re.search(r'(?:ran|run):?\s*([0-9.]+)', log_str, re.IGNORECASE)
                    
                    pace_match = re.search(r'Pace:\s*([0-9.]+)', log_str, re.IGNORECASE)
                    ele_match = re.search(r'Elevation\s*Climbed:\s*\+?([0-9.]+)', log_str, re.IGNORECASE)
                    
                    # 1. Parse distances down across exact physiological timelines
                    if dist_match:
                        run_miles = float(dist_match.group(1))
                        
                        # Timeline Allocation A: 7-Day Sharpness
                        if log_dt >= seven_days_ago:
                            miles_7d += run_miles
                        # Timeline Allocation B: 28-Day Aerobic Capacity Engine
                        if log_dt >= twenty_eight_ago:
                            miles_28d += run_miles
                            total_3wk_miles += run_miles  # Maintains backward compatibility with legacy HUD displays
                            valid_sessions_count += 1
                        # Timeline Allocation C: 84-Day Deep Base Cushion
                        if log_dt >= eighty_four_ago:
                            miles_84d += run_miles

                    # 2. Parse elevation into total volume accumulation metrics
                    if ele_match:
                        curr_ele = float(ele_match.group(1))
                        if log_dt >= twenty_eight_ago:
                            if curr_ele > max_single_run_elevation: 
                                max_single_run_elevation = curr_ele
                        if log_dt >= eighty_four_ago:
                            total_84d_elevation += curr_ele

                    # 3. Parse pace metrics safely within the chronic 28-day window
                    if pace_match and log_dt >= twenty_eight_ago:
                        current_pace = float(pace_match.group(1))
                        if 2.0 < current_pace < fastest_pace_in_window: 
                            fastest_pace_in_window = current_pace
            except Exception: 
                pass

    # ==============================================================================
    # 🧮 PHYSIOLOGICAL METRICS MATRIX MATRICES
    # ==============================================================================
    
    # 🔋 1. ENDURANCE: Dual-Timeline EWMA Cushion Engine Base
    # Converts 84-day macro volume into an average weekly chronic volume base
    # (84 days / 7 days = 12 full training base weeks)
    avg_weekly_macro_volume = miles_84d / 12.0
    
    # Base cushion levels acts as a protective shield (e.g. 60+ mi/wk base unlocks L7 floor cushion)
    macro_base_cushion = min(9, int(avg_weekly_macro_volume / 8.5))
    
    # Calculate active, near-term fitness level (targeted at ~45 total miles per 28 days per level)
    active_engine_level = max(1, min(9, int(miles_28d / 15.0)))
    
    # We combine them using a weighted balance coefficient
    # Your 12-week macro base acts as a 65% protective floor to model slow metabolic deconditioning
    if avg_weekly_macro_volume >= 35.0:
        endurance_rating = int(round((macro_base_cushion * 0.65) + (active_engine_level * 0.35)))
    else:
        # If no macro structural base exists, rely completely on what you have run lately
        endurance_rating = active_engine_level
    endurance_rating = max(1, min(9, endurance_rating))

    # ⚡ 2. SPEED: True Pace Time Conversion to Absolute Running Seconds
    if 2.0 < fastest_pace_in_window < 20.0:
        minutes = int(fastest_pace_in_window)
        seconds = int(round((fastest_pace_in_window % 1) * 100))
        total_pace_seconds = (minutes * 60) + seconds
        
        # Physiological Speed Curve: Target 5:30 (330s) = Level 9 | 10:00 (600s) = Level 1
        if total_pace_seconds <= 330:
            speed_rating = 9
        else:
            speed_rating = max(1, min(9, int(9 - ((total_pace_seconds - 330) / 33.7))))
            
        # 📈 Acute Sharpness Modifier: If you have run over 15 miles in the last 7 days, 
        # your muscle sharpness spikes, awarding a +1 speed level bonus (caps cleanly at 9)
        if miles_7d >= 15.0 and speed_rating < 9:
            speed_rating += 1
    else: 
        speed_rating = 1

    # ⛰️ 3. ELEVATION STRENGTH: Calibrated Down to 10,000 FT Ceiling Scale
    # 10,000 ft accumulated climbing over a 12-week window unlocks Level 9 Max Strength
    strength_rating = max(1, min(9, int((total_84d_elevation / 10000.0) * 9)))
    # ==============================================================================
    # 🎯 WRITE TRIPLE-SYNC CACHE ENTRIES OUT TO STREAMLIT GLOBAL STORAGE CLIPBOARD
    # ==============================================================================
    st.session_state["global_endurance"] = int(endurance_rating)
    st.session_state["global_speed"]     = int(speed_rating)
    st.session_state["global_elevation"] = int(strength_rating)

    # Flashing Overdrive Warnings
    if total_3wk_miles >= 45.0:
        st.error("🔥 🔥 🔥 RUNNER RECORD ON FIRE !! SPRINT OVERDRIVE ENGAGED !! 🔥 🔥 🔥")
    elif valid_sessions_count >= 3:
        st.warning("⚡ ATHLETE IS HEATING UP !")

    # CONDENSED ARCADE RUNNER HUD
    with st.container(border=True):
        st.markdown(f"🎰 **TRACK CHAMPIONSHIP ROSTER MATRIX** | CREDIT INSERTED | **STAGES COMPLETED (28D): {valid_sessions_count}**")
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.markdown(f"🔋 **AEROBIC CAPACITY / ENDURANCE** `[ {endurance_rating} / 9 ]`")
            st.progress(float(endurance_rating / 9.0))
            st.caption(f"Volume (28D): {miles_28d:.1f} Mi | Base Engine: {avg_weekly_macro_volume:.1f} mi/wk")
            
        with c2:
            st.markdown(f"⚡ **SPRINT VELOCITY / PACE** `[ {speed_rating} / 9 ]`")
            st.progress(float(speed_rating / 9.0))
            pace_str = f"{int(fastest_pace_in_window)}:{(fastest_pace_in_window%1)*60:02.0f} min/mi" if fastest_pace_in_window < 900.0 else "N/A"
            st.caption(f"PR Split Time: {pace_str} | Acute (7D): {miles_7d:.1f} mi")
            
        with c3:
            st.markdown(f"⛰️ **HILL-CLIMBING ELEVATION FORCE** `[ {strength_rating} / 9 ]`")
            st.progress(float(strength_rating / 9.0))
            st.caption(f"Peak Accumulation (84D): {int(total_84d_elevation):,} / 10,000 ft")

    # ==============================================================================
    # 🏆 DYNAMIC LEVEL-UP QUEST CHALLENGES MATRIX
    # ==============================================================================
    st.write("")
    st.markdown("### 🎯 **RANK ADVANCEMENT CHALLENGES**")
    
    # 🔋 SIMULATION ENGINE: Step forward to calculate the next true rating bump
    next_endurance_target = miles_28d
    endurance_delta = 0.0
    
    if endurance_rating < 9:
        for test_miles in np.arange(miles_28d, miles_28d + 150.0, 0.5):
            test_active_level = max(1, min(9, int(test_miles / 15.0)))
            if avg_weekly_macro_volume >= 35.0:
                test_rating = int(round((macro_base_cushion * 0.65) + (test_active_level * 0.35)))
            else:
                test_rating = test_active_level
                
            if test_rating > endurance_rating:
                next_endurance_target = test_miles
                endurance_delta = next_endurance_target - miles_28d
                break
                
        # 🚨 ANCHOR OVERRIDE CORE FIX: Programmatically bypass the 0.0 rounding dead zone.
        # Forces a clean 15-mile volume target tier above current miles to lift the anchor.
        if endurance_delta <= 0.0:
            next_clean_tier = ((int(miles_28d / 15.0)) + 1) * 15.0
            next_endurance_target = float(next_clean_tier)
            endurance_delta = max(1.0, next_endurance_target - miles_28d)
    
    # Calculate target seconds for speed advancement
    if speed_rating < 9:
        next_speed_seconds = 330 + ((9 - (speed_rating + 1)) * 33.7)
        next_min = int(next_speed_seconds // 60)
        next_sec = int(next_speed_seconds % 60)
        speed_target_str = f"{next_min}:{next_sec:02d} min/mi"
    else:
        speed_target_str = "MAX LEVEL REACHED"
        
    next_elevation_target = ((strength_rating + 1) * 10000.0) / 9.0
    elevation_delta = max(0.0, next_elevation_target - total_84d_elevation)
    
    ch1, ch2, ch3 = st.columns(3)
    
    with ch1:
        with st.container(border=True):
            st.markdown("⚙️ **Endurance Unlock Quest**")
            if endurance_rating < 9:
                st.write(f"Log **{endurance_delta:.1f}** more total miles within your 28-day chronic tracking loop to break into **Level {endurance_rating + 1}**.")
                st.caption(f"Current Target: {miles_28d:.1f} / {next_endurance_target:.1f} Mi")
            else:
                st.success("👑 **MAX LEVEL ACHIEVED**")
                st.caption("Aerobic baseline completely maximized.")
                
    with ch2:
        with st.container(border=True):
            st.markdown("⚡ **Velocity Unlock Quest**")
            if speed_rating < 9:
                st.write(f"Drop your best 28-day training split time below **{speed_target_str}** to rank up to **Level {speed_rating + 1}**.")
                st.caption(f"Current Best Split: {pace_str}")
                if miles_7d < 15.0:
                    st.info(f"💡 Run **{15.0 - miles_7d:.1f} mi** more this week for a +1 Sharpness level bonus!")
            else:
                st.success("👑 **MAX LEVEL ACHIEVED**")
                st.caption("Sprint pace completely maximized.")
                
    with ch3:
        with st.container(border=True):
            st.markdown("🧗‍♂️ **Torque Unlock Quest**")
            if strength_rating < 9:
                st.write(f"Accumulate **{int(elevation_delta):,} ft** more vertical climbing gain across your 84-day macro loop to unlock **Level {strength_rating + 1}**.")
                st.caption(f"Current Target: {int(total_84d_elevation):,} / {int(next_elevation_target):,} ft")
            else:
                st.success("👑 **MAX LEVEL ACHIEVED**")
                st.caption("Vertical capacity completely maximized.")

