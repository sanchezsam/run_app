# -*- coding: utf-8 -*-
"""
ATHLETE SHEET — PREMIUM RPG CHARACTER PROFILE (character_profile.py)
Implements an interactive, high-fidelity sports RPG character sheet.
Features dynamic class archetypes, level-locked profile portraits (1.png to 9.png),
custom retrowave neon progress bars, a shoe degradation tracker, heart rate zone meters,
streak counters, a physical therapy desk for fatigue recovery, talent tree perks,
and a chronological back-dated trend engine to chart historical fitness changes.
Includes a fully customizable level-to-title rank progression mapping table with an image fallback.
"""

import streamlit as st
import numpy as np
import json
import re
import os
import math
import pandas as pd
from datetime import datetime, timedelta

# =========================================================================
# 🏆 CUSTOMIZABLE LEVEL PROGRESSION TITLES MAPPING
# Feel free to change these strings to create your own personalized rank titles!
# =========================================================================
LEVEL_TITLES_MAP = {
    1: "Greenhorn Recruit",
    2: "Asphalt Jogger",
    3: "Cadence Finder",
    4: "Steady-State Cruiser",
    5: "Sub-Threshold Striker",
    6: "Tempo Dominator",
    7: "Endurance Vanguard",
    8: "Master Pacer",
    9: "Sub-2 Sovereign / Immortal"
}

def compute_historical_snapshot(history_logs, target_date):
    """
    Slices historical running logs relative to a back-dated point in time 
    to simulate exactly what the player's trait levels were at that moment.
    """
    seven_days_ago = target_date - timedelta(days=7)
    twenty_eight_ago = target_date - timedelta(days=28)
    eighty_four_ago = target_date - timedelta(days=84)
    
    miles_7d = 0.0
    miles_28d = 0.0
    miles_84d = 0.0
    fastest_pace = 999.0
    total_elevation = 0.0
    
    for log in history_logs:
        if isinstance(log, dict):
            date_raw = log.get("Date", "")
            try:
                log_dt = datetime.strptime(str(date_raw)[:10], '%Y-%m-%d')
            except Exception:
                continue
            dist_val = float(log.get("Distance (Miles)", 0.0))
            pace_val = float(log.get("pace", 999.0))
            ele_str = str(log.get("Elevation (ft)", "0")).replace('+', '').replace('ft', '').strip()
            ele_val = float(ele_str) if ele_str else 0.0
        else:
            log_str = str(log)
            try:
                date_match = re.search(r'\[([0-9-]+)\]', log_str)
                if not date_match: continue
                log_dt = datetime.strptime(date_match.group(1)[:10], '%Y-%m-%d')
                d_m = re.search(r'Run:\s*([0-9.]+)', log_str, re.IGNORECASE)
                if not d_m: d_m = re.search(r'(?:ran|run):?\s*([0-9.]+)', log_str, re.IGNORECASE)
                dist_val = float(d_m.group(1)) if d_m else 0.0
                p_m = re.search(r'Pace:\s*([0-9.]+)', log_str)
                pace_val = float(p_m.group(1)) if p_m else 999.0
                e_m = re.search(r'Elevation\s*Climbed:\s*\+?([0-9.]+)', log_str)
                ele_val = float(e_m.group(1)) if e_m else 0.0
            except Exception:
                continue

        # Skip workout log instances that occurred after our historical snapshot checkpoint
        if log_dt > target_date or log_dt < eighty_four_ago:
            continue
            
        if dist_val > 0:
            if log_dt >= seven_days_ago: miles_7d += dist_val
            if log_dt >= twenty_eight_ago: miles_28d += dist_val
            if log_dt >= eighty_four_ago: miles_84d += dist_val
        if ele_val > 0:
            if log_dt >= eighty_four_ago: total_elevation += ele_val
        if 2.0 < pace_val < 20.0 and log_dt >= twenty_eight_ago:
            if pace_val < fastest_pace: fastest_pace = pace_val

    # Stamina level solver
    avg_wk_vol = miles_84d / 12.0
    macro_cushion = min(9, int(avg_wk_vol / 8.5))
    act_stamina = max(1, min(9, int(miles_28d / 15.0)))
    endurance_lvl = int(round((macro_cushion * 0.65) + (act_stamina * 0.35))) if avg_wk_vol >= 35.0 else act_stamina
    endurance_lvl = max(1, min(9, endurance_lvl))
    
    # Efficiency speed level solver
    if 2.0 < fastest_pace < 20.0:
        minutes = int(fastest_pace)
        seconds = min(59, int(round((fastest_pace % 1) * 100)))
        tot_secs = (minutes * 60) + seconds
        speed_lvl = 9 if tot_secs <= 330 else max(1, min(9, int(9 - ((tot_secs - 330) / 33.7))))
        if miles_7d >= 15.0 and speed_lvl < 9: speed_lvl += 1
    else:
        speed_lvl = 1
        
    # Climbing level solver
    climb_lvl = max(1, min(9, int((total_elevation / 10000.0) * 9)))
    
    return endurance_lvl, speed_lvl, climb_lvl

def calculate_and_render_profile(player, FILE_PATH=None):
    now_date = datetime.now()
    
    # ⏱️ SPORTS SCIENCE LOOKBACKS
    seven_days_ago  = now_date - timedelta(days=7)
    twenty_eight_ago = now_date - timedelta(days=28)
    eighty_four_ago  = now_date - timedelta(days=84)
    
    miles_7d = 0.0
    miles_28d = 0.0
    miles_84d = 0.0
    valid_sessions_count = 0
    fastest_pace_in_window = 999.0
    total_84d_elevation = 0.0
    max_single_run_elevation = 0.0
    
    # Heart rate and streak processing variables
    hr_counts = {"recovery": 0, "aerobic": 0, "threshold": 0, "vo2max": 0}
    discovered_dates = []
    
    raw_logs = getattr(player, 'history_logs', [])
    for log in raw_logs:
        if isinstance(log, dict):
            log_str = log.get("text_payload", str(log))
            dist_val = float(log.get("Distance (Miles)", 0.0))
            pace_val = float(log.get("pace", 999.0))
            ele_str = str(log.get("Elevation (ft)", "0")).replace('+', '').replace('ft', '').strip()
            ele_val = float(ele_str) if ele_str else 0.0
            date_raw = log.get("Date", "")
            
            # Extract heart rate metrics cleanly for sports science focus meter
            avg_hr = log.get("avg_heart_rate") or log.get("heart_rate")
            if avg_hr:
                try:
                    hr_float = float(avg_hr)
                    if hr_float < 130: hr_counts["recovery"] += 1
                    elif 130 <= hr_float < 152: hr_counts["aerobic"] += 1
                    elif 152 <= hr_float < 172: hr_counts["threshold"] += 1
                    else: hr_counts["vo2max"] += 1
                except (ValueError, TypeError): pass

            try:
                log_dt = datetime.strptime(str(date_raw)[:10], '%Y-%m-%d')
                discovered_dates.append(log_dt)
            except Exception: continue
        else:
            log_str = str(log)
            dist_val, pace_val, ele_val = 0.0, 999.0, 0.0
            try:
                date_match = re.search(r'\[([0-9-]+)\]', log_str)
                if not date_match: continue
                log_dt = datetime.strptime(date_match.group(1)[:10], '%Y-%m-%d')
                discovered_dates.append(log_dt)
                d_match = re.search(r'Run:\s*([0-9.]+)', log_str, re.IGNORECASE)
                if not d_match: d_match = re.search(r'(?:ran|run):?\s*([0-9.]+)', log_str, re.IGNORECASE)
                dist_val = float(d_match.group(1)) if d_match else 0.0
                p_match = re.search(r'Pace:\s*([0-9.]+)', log_str)
                pace_val = float(p_match.group(1)) if p_match else 999.0
                e_match = re.search(r'Elevation\s*Climbed:\s*\+?([0-9.]+)', log_str)
                ele_val = float(e_match.group(1)) if e_match else 0.0
                
                hr_match = re.search(r'(?:HR|Heart Rate|BPM):\s*([0-9.]+)', log_str, re.IGNORECASE)
                if hr_match:
                    hr_float = float(hr_match.group(1))
                    if hr_float < 130: hr_counts["recovery"] += 1
                    elif 130 <= hr_float < 152: hr_counts["aerobic"] += 1
                    elif 152 <= hr_float < 172: hr_counts["threshold"] += 1
                    else: hr_counts["vo2max"] += 1
            except Exception: continue

        if 'miles' in log_str.lower() and 'slept' not in log_str.lower():
            if log_dt < eighty_four_ago: continue
            if dist_val > 0:
                if log_dt >= seven_days_ago: miles_7d += dist_val
                if log_dt >= twenty_eight_ago:
                    miles_28d += dist_val
                    valid_sessions_count += 1
                if log_dt >= eighty_four_ago: miles_84d += dist_val
            if ele_val > 0:
                if log_dt >= twenty_eight_ago: max_single_run_elevation = max(max_single_run_elevation, ele_val)
                if log_dt >= eighty_four_ago: total_84d_elevation += ele_val
            if 2.0 < pace_val < 20.0 and log_dt >= twenty_eight_ago:
                if pace_val < fastest_pace_in_window: fastest_pace_in_window = pace_val

    # --- RESOLVE CORE STAT TIER RATINGS ---
    avg_weekly_macro_volume = miles_84d / 12.0
    macro_base_cushion = min(9, int(avg_weekly_macro_volume / 8.5))
    active_stamina_level = max(1, min(9, int(miles_28d / 15.0)))
    
    if avg_weekly_macro_volume >= 35.0:
        endurance_rating = int(round((macro_base_cushion * 0.65) + (active_stamina_level * 0.35)))
    else:
        endurance_rating = active_stamina_level
    endurance_rating = max(1, min(9, endurance_rating))

    if 2.0 < fastest_pace_in_window < 20.0:
        minutes = int(fastest_pace_in_window)
        seconds = min(59, int(round((fastest_pace_in_window % 1) * 100)))
        total_pace_seconds = (minutes * 60) + seconds
        speed_rating = 9 if total_pace_seconds <= 330 else max(1, min(9, int(9 - ((total_pace_seconds - 330) / 33.7))))
        if miles_7d >= 15.0 and speed_rating < 9: speed_rating += 1
    else: 
        speed_rating = 1

    strength_rating = max(1, min(9, int((total_84d_elevation / 10000.0) * 9)))
    
    # Calculate unified Overall Runner Level (ORL)
    total_pts = (endurance_rating * 100) + (speed_rating * 100) + (strength_rating * 100)
    orl_level = max(1, min(9, int(total_pts / 300)))
    
    # Extract the custom title string corresponding to the active rank tier
    active_custom_rank_title = LEVEL_TITLES_MAP.get(orl_level, f"Rank {orl_level} Runner")
    
    st.session_state["global_endurance"] = int(endurance_rating)
    st.session_state["global_speed"]     = int(speed_rating)
    st.session_state["global_elevation"] = int(strength_rating)

    # Resolve Character Archetype Styling Parameters
    if endurance_rating >= speed_rating + 2 and endurance_rating >= strength_rating + 2:
        class_archetype, class_emoji, class_color = "The Wandering Ultra-Nomad", "🗺️", "#3498db"
        class_desc = "Possesses elite, deep volume endurance thresholds built for multi-hour survival boundaries."
    elif speed_rating >= endurance_rating + 2 and speed_rating >= strength_rating + 2:
        class_archetype, class_emoji, class_color = "The Tarmac Bullet", "⚡", "#e74c3c"
        class_desc = "Dominates short-track splits and flat tarmac thoroughfares using explosive leg turnover."
    elif strength_rating >= endurance_rating + 2 and strength_rating >= speed_rating + 2:
        class_archetype, class_emoji, class_color = "The Alpine Sky-Wraith", "🧗‍♂️", "#9b59b6"
        class_desc = "Thrives on punishing vertical grades, thin air trail obstacles, and mountain scree."
    elif endurance_rating >= 5 and speed_rating >= 5 and strength_rating >= 5 and abs(endurance_rating - speed_rating) <= 1 and abs(speed_rating - strength_rating) <= 1:
        class_archetype, class_emoji, class_color = "The All-Terrain Harrier", "👑", "#f1c40f"
        class_desc = "A perfectly balanced tactical master matching speed, mountain torque, and mileage capacities cleanly."
    else:
        class_archetype, class_emoji, class_color = "The Emerging Harrier", "🏃‍♂️", "#2ecc71"
        class_desc = "A versatile competitor actively shaping and rounding out their foundational metrics profile."

    # --- RENDER ARCHETYPE HEADER WITH INTEGRATED PORTRAIT UNLOCK LOOP AND USER RANK PROGRESSION TITLE ---
    st.markdown(f"""
    <div style='background: linear-gradient(135deg, #1a252f 0%, #2c3e50 100%); border-left: 6px solid {class_color}; border-radius: 6px; padding: 18px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
        <div style='display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 15px;'>
            <div style='display: flex; align-items: center; gap: 20px;'>
                <div id='portrait-container'>
                    <!-- Level-locked snapshot container mapping direct local image files -->
                    <div style='width: 85px; height: 85px; border-radius: 50%; border: 3px solid {class_color}; background: #2c3e50; display: flex; align-items: center; justify-content: center; font-size: 2rem; color: white; box-shadow: 0 0 10px {class_color};'>
                        {orl_level}
                    </div>
                </div>
                <div>
                    <p style='margin: 0; font-size: 0.75rem; color: #bdc3c7; letter-spacing: 1.5px; text-transform: uppercase; font-weight: bold;'>ATHLETE DOSSIER &bull; {active_custom_rank_title.upper()} (LVL {orl_level})</p>
                    <h2 style='margin: 4px 0; color: white; font-size: 1.65rem;'>{class_emoji} {class_archetype}</h2>
                    <p style='margin: 2px 0 0 0; font-size: 0.88rem; color: #ecf0f1; font-style: italic;'>{class_desc}</p>
                </div>
            </div>
            <div style='background: rgba(255,255,255,0.06); border-radius: 8px; padding: 10px 18px; text-align: center; min-width: 120px;'>
                <span style='font-size: 0.7rem; color: #bdc3c7; display: block; font-weight: bold;'>TRAINING STREAK</span>
                <h3 style='margin: 0; color: #f1c40f; font-size: 1.5rem;'>{max(1, int(len(discovered_dates)/3))} Weeks</h3>
                <span style='font-size: 0.65rem; color: #2ecc71; display: block;'>1.2x Multiplier Active</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Scan inside images/profile_pics/ directory path for level-locked avatar assets
    image_extensions = [".png", ".jpg", ".jpeg"]
    portrait_found = False
    for ext in image_extensions:
        potential_path = os.path.join("images", "profile_pics", f"{orl_level}{ext}")
        if os.path.exists(potential_path):
            st.sidebar.image(potential_path, caption=f"Unlocked Level {orl_level} Portrait: {active_custom_rank_title}", use_container_width=True)
            portrait_found = True
            break
            
    # CRITICAL INJECTED FALLBACK MECHANISM: Graceful layout display if custom art assets are missing
    if not portrait_found:
        st.sidebar.markdown(f"""
        <div style='display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 20px; border: 2px dashed rgba(128,128,128,0.25); border-radius: 8px; background: rgba(255,255,255,0.01); text-align: center; margin-bottom: 15px;'>
            <div style='width: 105px; height: 105px; border-radius: 50%; border: 3px dashed {class_color}; background: #2c3e50; display: flex; align-items: center; justify-content: center; font-size: 2.6rem; box-shadow: inset 0 0 15px rgba(0,0,0,0.3); margin-bottom: 12px; filter: drop-shadow(0 0 4px {class_color});'>
                {class_emoji}
            </div>
            <p style='margin: 0; font-weight: bold; font-size: 0.85rem; color: #ecf0f1;'>{active_custom_rank_title}</p>
            <p style='margin: 2px 0 0 0; font-size: 0.7rem; color: #7f8c8d;'>Frame Shell &bull; Level {orl_level} Unlocked</p>
        </div>
        """, unsafe_allow_html=True)
        st.sidebar.info(f"🖼️ **Missing Asset Fallback Active:** To apply custom artwork over this frame, drop a picture file named `{orl_level}.png` into your local `images/profile_pics/` subdirectory directory loop!")

    # Establish tab navigation panels
    tab_sheet, tab_recovery, tab_trends, tab_perks, tab_cabinet = st.tabs([
        "📊 Biometric Core Sheet", 
        "👟 Gear & Recovery Desk",
        "📈 Chronological Trait Growth", 
        "🔮 Talent Tree Progression",
        "🎖️ Milestone Trophy Case"
    ])

    # =========================================================================
    # TAB 1: RETROWAVE CUSTOM PROGRESS STAT BARS
    # =========================================================================
    with tab_sheet:
        def render_neon_stat_bar(label, icon, level, metrics_str, hex_color):
            pct = (level / 9.0) * 100.0
            st.markdown(f"""
            <div style='margin-bottom: 16px; padding: 12px; border: 1px solid rgba(128,128,128,0.15); border-radius: 6px; background-color: rgba(255,255,255,0.01);'>
                <div style='display: flex; justify-content: space-between; margin-bottom: 4px; align-items: center;'>
                    <span style='font-weight: bold; font-size: 0.92rem;'>{icon} {label}</span>
                    <span style='color: {hex_color}; font-weight: bold; font-size: 0.95rem;'>LVL {level} / 9</span>
                </div>
                <div style='background-color: rgba(128,128,128,0.1); border-radius: 4px; height: 12px; width: 100%; overflow: hidden; margin-bottom: 4px;'>
                    <div style='background-color: {hex_color}; height: 100%; width: {pct}%; border-radius: 4px; box-shadow: 0 0 8px {hex_color};'></div>
                </div>
                <span style='font-size: 0.75rem; color: #7f8c8d;'>{metrics_str}</span>
            </div>
            """, unsafe_allow_html=True)

        render_neon_stat_bar(
            "AEROBIC STAMINA & ENDURANCE", "🔋", endurance_rating,
            f"Volume (28D): {miles_28d:.1f} Mi | Aerobic Base Foundation: {avg_weekly_macro_volume:.1f} mi/wk", "#3498db"
        )
        
        pace_str = f"{int(fastest_pace_in_window)}:{(fastest_pace_in_window%1)*60:02.0f} min/mi" if fastest_pace_in_window < 900.0 else "N/A"
        render_neon_stat_bar(
            "STRIDE EFFICIENCY & PACE", "⚡", speed_rating,
            f"PR Windows Split Pace: {pace_str} | Active Sharpness Filter (7D): {miles_7d:.1f} mi", "#e74c3c"
        )
        
        render_neon_stat_bar(
            "VERTICAL CLIMBING POWER", "⛰️", strength_rating,
            f"Peak Vertical Accumulation (84D): {int(total_84d_elevation):,} / 10,000 ft", "#9b59b6"
        )

        st.write("")
        st.markdown("#### 🎯 Rank Advancement Requirements")
        
        next_endurance_target = miles_28d
        endurance_delta = 0.0
        if endurance_rating < 9:
            for test_miles in np.arange(miles_28d, miles_28d + 150.0, 0.5):
                test_lvl = max(1, min(9, int(test_miles / 15.0)))
                test_rating = int(round((macro_base_cushion * 0.65) + (test_lvl * 0.35))) if avg_weekly_macro_volume >= 35.0 else test_lvl
                if test_rating > endurance_rating:
                    next_endurance_target = test_miles
                    endurance_delta = next_endurance_target - miles_28d
                    break
            if endurance_delta <= 0.0:
                next_clean_tier = ((int(miles_28d / 15.0)) + 1) * 15.0
                next_endurance_target = float(next_clean_tier)
                endurance_delta = max(1.0, next_endurance_target - miles_28d)

        if speed_rating < 9:
            next_speed_seconds = 330 + ((9 - (speed_rating + 1)) * 33.7)
            speed_target_str = f"{int(next_speed_seconds // 60)}:{int(next_speed_seconds % 60):02d} min/mi"
        else:
            speed_target_str = "MAX LEVEL REACHED"

        next_elevation_target = ((strength_rating + 1) * 10000.0) / 9.0
        elevation_delta = max(0.0, next_elevation_target - total_84d_elevation)

        ch1, ch2, ch3 = st.columns(3)
        with ch1:
            with st.container(border=True):
                st.markdown("🔋 **Endurance Target**")
                if endurance_rating < 9:
                    st.write(f"Log **{endurance_delta:.1f}** more miles in your 28D chronic tracking loop.")
                    st.caption(f"Progress: {miles_28d:.1f} / {next_endurance_target:.1f} Mi")
                else: st.success("👑 **MAX TIER LOCKED**")
        with ch2:
            with st.container(border=True):
                st.markdown("⚡ **Velocity Target**")
                if speed_rating < 9:
                    st.write(f"Drop your best 28D training split time below **{speed_target_str}**.")
                    st.caption(f"Current Best: {pace_str}")
                else: st.success("👑 **MAX TIER LOCKED**")
        with ch3:
            with st.container(border=True):
                st.markdown("⛰️ **Climbing Target**")
                if strength_rating < 9:
                    st.write(f"Accumulate **{int(elevation_delta):,} ft** more vertical gain across your 84D loop.")
                    st.caption(f"Progress: {int(total_84d_elevation):,} / {int(next_elevation_target):,} ft")
                else: st.success("👑 **MAX TIER LOCKED**")

    # =========================================================================
    # TAB 2: ADVANCED RECOVERY & EXTENDED GEAR HEALTH LABS
    # =========================================================================
    with tab_recovery:
        st.markdown("### 👟 Integrated Equipment Odometer & Performance Wear")
        st.caption("Track running shoe structural breakdown parameters. Retiring degraded gear protects you from injury.")
        
        active_shoe = getattr(player, 'equipped_shoe_name', 'Carbon Plated Daily Trainer')
        profile_dict = st.session_state.get("profile", {})
        m_data = profile_dict.get("final_metric_data", {})
        lifetime_miles = float(m_data.get("lifetime_odometer_miles", 0.0))
        
        # Calculate shoe wear metrics (Carbon models wear down faster at 200mi limits)
        shoe_limit = 200.0 if "carbon" in active_shoe.lower() or "plated" in active_shoe.lower() else 450.0
        shoe_miles = min(shoe_limit, lifetime_miles % shoe_limit)
        shoe_wear_pct = (shoe_miles / shoe_limit) * 100.0
        
        col_shoe, col_wear_bar = st.columns([1, 2])
        with col_shoe:
            st.metric("Equipped Shoe Odometer", f"{shoe_miles:.1f} / {shoe_limit:.0f} Mi")
            st.caption(f"Active Model: `{active_shoe}`")
        with col_wear_bar:
            st.write("<br/>", unsafe_allow_html=True)
            st.progress(shoe_wear_pct / 100.0)
            if shoe_wear_pct >= 85.0:
                st.error("⚠️ **CRITICAL FOAM DEGRADATION:** Cushioning exhausted! Retire this model at the Pro Shop to mitigate injury spikes.")
            else:
                st.success("✅ **FOAM INTEGRITY STABLE:** Shoe structural response boundaries are safe.")

        st.markdown("---")
        st.markdown("### 🫁 Heart Rate Distribution Focus Balance")
        st.caption("Sports science polarized breakdown monitors. Maintain 80% low-intensity miles to activate optimal metabolic adaptations.")
        
        total_hr_sessions = sum(hr_counts.values())
        if total_hr_sessions > 0:
            hr_df = pd.DataFrame([
                {"Zone Intensity": "🔵 Low-Intensity Recovery (<130 BPM)", "Sessions Count": hr_counts["recovery"]},
                {"Zone Intensity": "🟢 Aerobic Base Building (130-152 BPM)", "Sessions Count": hr_counts["aerobic"]},
                {"Zone Intensity": "🟡 Threshold Tempo (152-172 BPM)", "Sessions Count": hr_counts["threshold"]},
                {"Zone Intensity": "🔴 VO2 Max Intervals (>172 BPM)", "Sessions Count": hr_counts["vo2max"]}
            ])
            st.bar_chart(hr_df.set_index("Zone Intensity"), use_container_width=True)
        else:
            st.info("ℹ️ No heart rate telemetry profiles discovered yet. Upload a Garmin .fit record to draw focus distribution curves.")

        if getattr(player, 'fatigue', 0) >= 80:
            st.markdown("---")
            st.markdown("### 🩹 Physical Therapy Desk & Injury Log")
            st.error("""💥 **ACTIVE CONDITION: MINOR PLANTAR FASCIITIS / SHIN SPLINTS**
            
Your localized fatigue threshold has breached safety parameters. Stride performance factors are suffering a temporary -1.5 velocity debuff across Coliseum loops.
            
📋 **REHABILITATION ASSIGNMENT QUEST:**
To dissolve this condition card block, you must upload an intentional low-intensity recovery session containing an average heart rate strictly under 130 BPM, or log a full calendar rest day rest cycle.""")

    # =========================================================================
    # TAB 3: CHRONOLOGICAL TRAIT GROWTH (HISTORICAL DATA PROGRESSION)
    # =========================================================================
    with tab_trends:
        st.markdown("### 📈 Chronological Performance Evolution Tracker")
        st.caption("Re-evaluates historical data vectors back in time to chart the growth or deconditioning of your traits.")
        st.write("")
        
        if not discovered_dates or len(discovered_dates) < 2:
            st.info("ℹ️ Insufficient time-series coordinates discovered. Log multiple workouts over distinct dates to populate historical trend charts.")
        else:
            max_log_date = max(discovered_dates)
            snapshot_dates = [max_log_date - timedelta(days=d) for d in [35, 28, 21, 14, 7, 0]]
            
            trend_records = []
            for s_date in snapshot_dates:
                hist_end, hist_speed, hist_climb = compute_historical_snapshot(raw_logs, s_date)
                trend_records.append({
                    "Timeline Checkpoint": s_date.strftime("%Y-%m-%d"),
                    "Aerobic Stamina": hist_end,
                    "Stride Efficiency": hist_speed,
                    "Climbing Power": hist_climb
                })
                
            df_trends = pd.DataFrame(trend_records)
            st.line_chart(df_trends.set_index("Timeline Checkpoint"), use_container_width=True)
            with st.expander("👁️ View Granular Historical Level Logs"):
                st.dataframe(df_trends, use_container_width=True, hide_index=True)

    # =========================================================================
    # TAB 4: INTERACTIVE TALENT TREE PERK ALLOCATION
    # =========================================================================
    with tab_perks:
        st.markdown("### 🔮 Interactive Talent Tree Terminal")
        st.caption("Invest your career unallocated talent points to activate permanent character buffs.")
        
        if not hasattr(player, "stat_points") or player.stat_points is None: player.stat_points = 0
        if not hasattr(player, "perks") or not isinstance(player.perks, dict):
            player.perks = {"stride_spring": 0, "lung_capacity": 0, "thermal_adaptability": 0}
            
        st.write("")
        col_points, col_reset = st.columns([3, 1])
        with col_points: st.metric("Unallocated Talent Perks Points Available", f"{player.stat_points} PTS")
        with col_reset:
            st.write("<br/>", unsafe_allow_html=True)
            if player.perks["stride_spring"] > 0 or player.perks["lung_capacity"] > 0 or player.perks["thermal_adaptability"] > 0:
                if st.button("Reset Allocated Points", use_container_width=True):
                    total_refund = player.perks["stride_spring"] + player.perks["lung_capacity"] + player.perks["thermal_adaptability"]
                    player.stat_points += total_refund
                    player.perks = {"stride_spring": 0, "lung_capacity": 0, "thermal_adaptability": 0}
                    if FILE_PATH:
                        with open(FILE_PATH, 'w', encoding='utf-8') as f:
                            json.dump(player.to_dict() if hasattr(player, 'to_dict') else player.__dict__, f, default=str, indent=4)
                    st.rerun()

        st.markdown("---")
        PERK_MANIFEST = [
            {"id": "stride_spring", "name": "👟 Stride Spring Resonance", "desc": "Reduces simulated base pace splits equations by a flat 0.8 seconds per point allocated."},
            {"id": "lung_capacity", "name": "🫁 Capillary Density / Lung Capacity", "desc": "Decreases simulated match fatigue accumulation rates by 3% per invested tier point."},
            {"id": "thermal_adaptability", "name": "🌡️ Thermal Adaptability Coefficient", "desc": "Lowers extreme weather sync entry qualification locks by 1 run per point (Max 3)."}
        ]
        
        for perk in PERK_MANIFEST:
            p_id = perk["id"]
            current_investment = player.perks.get(p_id, 0)
            with st.container(border=True):
                pk_info, pk_action = st.columns([3, 1])
                with pk_info:
                    st.markdown(f"##### {perk['name']}")
                    st.markdown(f"*{perk['desc']}*")
                    st.markdown(f"**Current Investment Rank:** `{current_investment} / 5` Tier Blocks Pinned")
                with pk_action:
                    st.write("<br/>", unsafe_allow_html=True)
                    can_invest = player.stat_points > 0 and current_investment < 5
                    if st.button("➕ Invest Point", key=f"invest_btn_{p_id}", disabled=not can_invest, use_container_width=True):
                        player.stat_points -= 1
                        player.perks[p_id] = current_investment + 1
                        if FILE_PATH:
                            with open(FILE_PATH, 'w', encoding='utf-8') as f:
                                json.dump(player.to_dict() if hasattr(player, 'to_dict') else player.__dict__, f, default=str, indent=4)
                        st.rerun()

    # =========================================================================
    # TAB 5: THE LOCKER ROOM CABINET DISPLAY CASE (MEDALS / MILESTONES)
    # =========================================================================
    with tab_cabinet:
        st.markdown("### 🎖️ The Locker Room Cabinet Trophy Display Case")
        st.caption("High-prestige signature milestone tokens mounted permanently from high-stakes Coliseum duels.")
        st.write("")
        
        tokens_list = getattr(player, 'milestone_tokens', [])
        TOKEN_MANIFEST = {
            "skyrunner_laurel": {"name": "The Skyrunner Laurel", "icon": "⛰️", "border": "#9b59b6", "desc": "Conquered Kilian on an elite alpine single-track skyrun."},
            "sub2_breaking_token": {"name": "The Sub-2 Breaking Token", "icon": "⏱️", "border": "#e74c3c", "desc": "Defeated Eliud on a world-record asphalt marathon course."},
            "lightning_bolt_token": {"name": "The Lightning Bolt Token", "icon": "⚡", "border": "#f1c40f", "desc": "Out-printed Usain on his home 400m tactical sprint oval."},
            "ultramarathon_immortal": {"name": "The Ultramarathon Immortal Badge", "icon": "♾️", "border": "#3498db", "desc": "Surpassed Yiannis in a grueling 100-mile endurance simulation."}
        }
        
        if not tokens_list:
            st.info("🔒 No high-prestige milestone tokens mounted yet. Challenge and conquer the elite legendary runners on their signature home tracks in the Coliseum to secure your first medals!")
        else:
            grid_cols = st.columns(4)
            col_idx = 0
            for t_id, t_meta in TOKEN_MANIFEST.items():
                target_col = grid_cols[col_idx % 4]
                is_owned = t_id in tokens_list
                with target_col:
                    if is_owned:
                        st.markdown(f"""
                        <div style='border: 2px solid {t_meta["border"]}; border-radius: 6px; padding: 12px; text-align: center; background-color: rgba(255,255,255,0.03); min-height: 160px;'>
                            <span style='font-size: 2.2rem; filter: drop-shadow(0 0 6px {t_meta["border"]});'>{t_meta["icon"]}</span>
                            <h6 style='margin: 8px 0 4px 0; font-weight: bold; color: white;'>{t_meta["name"]}</h6>
                            <p style='margin: 0; font-size: 0.68rem; color: #bdc3c7; line-height: 1.2;'>{t_meta["desc"]}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div style='border: 1px dashed rgba(128,128,128,0.2); border-radius: 6px; padding: 12px; text-align: center; opacity: 0.3; min-height: 160px;'>
                            <span style='font-size: 2.2rem;'>🔒</span>
                            <h6 style='margin: 8px 0 4px 0; font-weight: bold; color: gray;'>Locked Medal</h6>
                            <p style='margin: 0; font-size: 0.65rem; color: gray; line-height: 1.2;'>Defeat this pacer's home circuit event to unlock.</p>
                        </div>
                        """, unsafe_allow_html=True)
                col_idx += 1

