# -*- coding: utf-8 -*-
"""
THE BIOMETRIC COLISEUM ARENA INTERFACE (coliseum_ui.py)
Manages interactive race staging matches, tactical strategies, climate adaptation,
pacer profiles, and track unlocking manuals driven by real training telemetry.
"""
import streamlit as st
import json
import os
import re
import pandas as pd
import time
import random
from datetime import datetime, timedelta
from coliseum_config import boss_catalog, course_catalog
import services

# =========================================================================
# 📊 CORE TELEMETRY COMPILERS & HELPER UTILITIES
# =========================================================================
def compile_coliseum_stats(player):
    """
    Crawls historical logs to build interactive win/loss records for rivals,
    race counts for circuits, and environmental exposure metrics.
    """
    history_logs = getattr(player, 'history_logs', [])
    
    # Initialize trackers
    boss_stats = {k: {"wins": 0, "losses": 0, "total": 0} for k in boss_catalog.keys()}
    course_stats = {k: {"raced_count": 0} for k in course_catalog.keys()}
    climate_exposure = {"Hot": 0, "Cold": 0}
    
    for log in history_logs:
        log_str = str(log)
        
        # 1. Parse Historical Climate Telemetry from Upload Records
        if "[CALORIE VAULT]" in log_str:
            temp_match = re.search(r'ambient_temp_f":\s*([0-9.]+)', log_str)
            if temp_match:
                temp_val = float(temp_match.group(1))
                if temp_val >= 88.0:
                    climate_exposure["Hot"] += 1
                elif temp_val <= 38.0:
                    climate_exposure["Cold"] += 1
                    
                       # 2. Parse Arena Circuit Outcomes
        # 🎯 BUG FIX: Changed loose "Track Match" check to the exact unique prefix
        # generated exclusively by Coliseum victories and defeats.
        if "🏁 Track Match Victory:" in log_str or "🏁 Track Match Defeat:" in log_str:
            is_win = "Victory:" in log_str or "🏁 Track Match Victory:" in log_str
            
            # Extract Boss Name
            detected_boss = None
            for b_name in boss_catalog.keys():
                if b_name in log_str:
                    detected_boss = b_name
                    break
                        
            # Extract Course Track Name
            detected_course = None
            for c_name in course_catalog.keys():
                # Extract clean prefix up to the bracket to ensure exact text matching
                clean_c = c_name.split(" [")[0]
                if clean_c in log_str:
                    detected_course = c_name
                    break
                    
            if detected_boss:
                boss_stats[detected_boss]["total"] += 1
                if is_win:
                    boss_stats[detected_boss]["wins"] += 1
                else:
                    boss_stats[detected_boss]["losses"] += 1
                    
            if detected_course:
                course_stats[detected_course]["raced_count"] += 1
 
    return boss_stats, course_stats, climate_exposure


def check_is_unlocked(criteria, character_stats, lifetime_miles):
    """
    Verifies if an athlete fulfills the criteria gates for a track or pacer rival.
    Returns (is_unlocked, error_reason_dict)
    """
    if not criteria:
        return True, {}
        
    errors = {}
    
    # Evaluate Unified Level Gate
    if "min_orl_level" in criteria and character_stats.get("level", 1) < criteria["min_orl_level"]:
        errors["orl"] = f"Requires Overall Runner Level {criteria['min_orl_level']}"
        
    # Evaluate Specialized Skill Gates
    if "min_stamina_level" in criteria and character_stats.get("endurance_level", 1) < criteria["min_stamina_level"]:
        errors["stamina"] = f"Requires Aerobic Stamina Level {criteria['min_stamina_level']}"
        
    if "min_efficiency_level" in criteria and character_stats.get("speed_level", 1) < criteria["min_efficiency_level"]:
        errors["efficiency"] = f"Requires Stride Efficiency Level {criteria['min_efficiency_level']}"
        
    if "min_power_level" in criteria and character_stats.get("strength_level", 1) < criteria["min_power_level"]:
        errors["power"] = f"Requires Climbing Power Level {criteria['min_power_level']}"
        
    # Evaluate Lifetime Odometer Gate
    if "min_lifetime_miles" in criteria and lifetime_miles < criteria["min_lifetime_miles"]:
        errors["miles"] = f"Requires {criteria['min_lifetime_miles']:.1f} Career Miles ({lifetime_miles:.1f}/{criteria['min_lifetime_miles']:.1f})"
        
    if errors:
        return False, errors
    return True, {}


def format_finish_time(secs):
    """Converts raw float seconds into formatted time strings with millisecond precision."""
    ts = str(timedelta(seconds=int(secs)))
    ms = int((secs - int(secs)) * 1000)
    return f"{ts}.{ms:03d}"


# =========================================================================
# 🎨 VISUAL ASSET PORTRAIT & COUPLING LOADERS
# =========================================================================
def display_boss_portrait(boss_name, specs, size=150):
    """Renders a registered pacer image portrait or falls back gracefully to a custom styled icon."""
    img_path = specs.get('profile_pic')
    fallback_icon = specs.get('icon', '🏃‍♂️')
    
    if img_path and os.path.exists(img_path):
        st.image(img_path, width=size)
    else:
        # High-fidelity dashboard placeholder box enclosing character icon
        box_css = f"""
        <div style='border: 2px dashed rgba(52, 152, 219, 0.4); border-radius: 8px; 
        width: {size}px; height: {size}px; display: flex; align-items: center; 
        justify-content: center; background: rgba(52, 152, 219, 0.02); font-size: 2.8rem;'>
            {fallback_icon}
        </div>
        """
        st.markdown(box_css, unsafe_allow_html=True)


def display_course_image(course_specs, height=180):
    """Renders a circuit map graphic or falls back to an elegant running trail blueprint wrapper."""
    img_path = course_specs.get('course_img')
    bias_factor = course_specs.get('bias', 'Balanced')
    
    # Pick decorative border colors depending on the track bias property
    accent_color = "#f1c40f" if bias_factor == "Speed" else "#2ecc71" if bias_factor == "Fuel" else "#3498db"
    
    if img_path and os.path.exists(img_path):
        st.image(img_path, use_container_width=True)
    else:
        blueprint_css = f"""
        <div style='border: 1px dashed {accent_color}60; border-radius: 6px; padding: 20px; 
        height: {height}px; display: flex; flex-direction: column; align-items: center; 
        justify-content: center; background: rgba(44, 62, 80, 0.02); color: #7f8c8d; text-align: center;'>
            <span style='font-size: 2.2rem; margin-bottom: 6px;'>🗺️</span>
            <span style='font-size: 0.72rem; letter-spacing: 0.5px; font-weight: bold;'>CIRCUIT MAP BLUEPRINT</span>
            <span style='font-size: 0.65rem; opacity: 0.7;'>({bias_factor} Bias Configuration)</span>
        </div>
        """
        st.markdown(blueprint_css, unsafe_allow_html=True)


def evaluate_signature_tokens(player, boss_name, course_name):
    """Checks and permanently appends rare high-prestige tokens for beating legends on home circuits."""
    if "unlocked_badges" not in player.__dict__ and not hasattr(player, 'unlocked_badges'):
        player.unlocked_badges = []
        
    tokens_minted = []
    
    if boss_name == "Kilian [GAZELLE]" and "La Luz" in course_name:
        if "skyrunner_laurel" not in player.unlocked_badges:
            player.unlocked_badges.append("skyrunner_laurel")
            tokens_minted.append("⛰️ The Skyrunner Laurel")
            
    elif boss_name == "Eliud [SPRINTER]" and "Monza" in course_name:
        if "sub2_breaking_token" not in player.unlocked_badges:
            player.unlocked_badges.append("sub2_breaking_token")
            tokens_minted.append("⏱️ The Sub-2 Breaking Token")
            
    elif boss_name == "Usain [CHEETAH]" and "Olympiastadion" in course_name:
        if "lightning_bolt_token" not in player.unlocked_badges:
            player.unlocked_badges.append("lightning_bolt_token")
            tokens_minted.append("⚡ The Lightning Bolt Token")
            
    elif boss_name == "Yiannis [STRIDER]" and ("Mont-Blanc" in course_name or "Western States" in course_name):
        if "ultramarathon_immortal" not in player.unlocked_badges:
            player.unlocked_badges.append("ultramarathon_immortal")
            tokens_minted.append("♾️ The Ultramarathon Immortal Badge")
            
    return tokens_minted


# =========================================================================
# 🏟️ MAIN COLISEUM WORKSPACE VIEW TERMINAL
# =========================================================================
def render_coliseum(player, FILE_PATH):
    st.markdown('## 🏟️ THE BIOMETRIC COLISEUM: HIGH-STAKES CHAMPIONSHIPS')
    st.markdown('Select your Pacer Rival, inspect global circuit tracks, and launch physics-based athletic duels driven entirely by your real-world log history!')
    st.markdown('---')
    
    # Safeguard initialization parameters
    if not hasattr(player, 'boss_clears') or player.boss_clears is None: 
        player.boss_clears = 0
    if not hasattr(player, 'boss_levels') or not isinstance(player.boss_levels, dict): 
        player.boss_levels = {}
        
    # ─── STEP 1: LOAD LIVE RUNNER CHARACTER ATTRIBUTES ───

    # ─── STEP 1: LOAD LIVE RUNNER CHARACTER ATTRIBUTES ───
    raw_history = getattr(player, 'history_logs', [])

    # 🎯 OVERRIDE SETTING: Pull levels straight from memory keys instead of services
    p_fuel = int(st.session_state.get("global_endurance", 7))
    p_nitro = int(st.session_state.get("global_speed", 8))
    p_torque = int(st.session_state.get("global_elevation", 9))
    active_fatigue = int(st.session_state.get("profile", {}).get("final_metric_data", {}).get("fatigue", 0))
    lifetime_miles = float(player.__dict__.get("final_metric_data", {}).get("lifetime_odometer_miles", 0.0))

    # Re-initialize character_stats explicitly right here so check_is_unlocked can read it downstream!
    character_stats = {
        "level": max(1, min(9, int((p_fuel + p_nitro + p_torque) / 3))),
        "endurance_level": p_fuel,
        "speed_level": p_nitro,
        "strength_level": p_torque,
        "fatigue": active_fatigue
    }

    
    # Compile deep match history records
    boss_stats, course_stats, climate_exposure = compile_coliseum_stats(player)
    
    # Calculate acute active training form over the past 21 days
    now_date = datetime.now()
    three_weeks_ago = now_date - timedelta(days=21)
    total_3wk_miles = 0.0
    
    for log in raw_history:
        log_str = str(log)
        if 'miles' in log_str.lower() and 'slept' not in log_str.lower():
            try:
                date_match = re.search(r'\[([0-9-]+)\]', log_str)
                if date_match:
                    log_dt = datetime.strptime(date_match.group(1)[:10], '%Y-%m-%d')
                    if log_dt >= three_weeks_ago:
                        d_match = re.search(r'(?:Run|run|ran|distance):?\s*([0-9.]+)', log_str, re.IGNORECASE)
                        if not d_match:
                            d_match = re.search(r'([0-9.]+)\s*(?:miles|mi)', log_str, re.IGNORECASE)
                        if d_match:
                            total_3wk_miles += float(d_match.group(1))
            except Exception: 
                pass
                
    # Apply Sprint Overdrive form multipliers if player is highly active
    is_on_fire = total_3wk_miles >= 45.0
    if is_on_fire:
        p_fuel = min(9, p_fuel + 2)
        p_nitro = min(9, p_nitro + 2)
        p_torque = min(9, p_torque + 2)
        st.error("🔥 PEAK ATHLETIC FORM ACTIVE: +2 TO ALL SCORING BASELINES ENFORCED !!")

    # ─── STEP 2: RENDER DASHBOARD INTERFACE TABS ───
    tab_arena, tab_pacers, tab_tracks = st.tabs([
        "🏟️ Championship Arena Staging", 
        "👥 Pacer Standings & Profiles", 
        "🗺️ Track Selection Manual"
    ])
    
        # =========================================================================
    # TAB 1: CHAMPIONSHIP ARENA STAGING
    # =========================================================================
    with tab_arena:
        st.markdown("### 🏆 Arena Cockpit Pre-Race Deployment")
        st.caption("Select your target challenge components to calculate win forecasts and calibrate execution vectors.")
        st.write("")

        col_sel1, col_sel2 = st.columns(2)
        with col_sel1:
            selected_boss = st.selectbox("👿 Select Target Pacer Challenger:", options=list(boss_catalog.keys()))
        with col_sel2:
            # Append distance helper labels cleanly into selection menus
            course_options = [f"{k} [{v['dist']:.2f} Mi]" for k, v in course_catalog.items()]
            selected_course_raw = st.selectbox("🗺️  Select Competition Circuit Track:", options=course_options)
            parsed_course_key = selected_course_raw.split(" [")[0]

        boss_specs = boss_catalog[selected_boss]
        course_specs = course_catalog[parsed_course_key]
        curr_level = int(player.boss_levels.get(selected_boss, 1))

        # Scale boss attributes dynamically based on their current clear difficulty level
        b_fuel = min(9, boss_specs['fuel'] + (curr_level - 1))
        b_nitro = min(9, boss_specs['nitro'] + (curr_level - 1))
        b_torque = min(9, boss_specs['torque'] + (curr_level - 1))

        # 🎯 TRACKING UPGRADE FIXED: Replaced old character_stats object mapping values
        # The engine now evaluates your true real-world training level variables
        # (Endurance 7, Speed 8, Climbing 9) stored directly inside the session dictionary!
        boss_unlocked, boss_errs = check_is_unlocked(boss_specs.get("unlock_criteria"), character_stats, lifetime_miles)
        course_unlocked, course_errs = check_is_unlocked(course_specs.get("unlock_criteria"), character_stats, lifetime_miles)

        st.markdown("---")

        # Scenario A: Blocked Content Rendering
        if not boss_unlocked or not course_unlocked:
            st.warning("### 🔒 TARGET SIMULATION SEGMENT LOCKED")
            st.write("You cannot stage this race match yet. Your real-world performance context does not meet registration baselines:")
            
            if not boss_unlocked:
                st.markdown(f"**Challenger Deficit ({selected_boss}):**")
                for err in boss_errs.values():
                    st.markdown(f" * ❌ {err}")
                    
            if not course_unlocked:
                st.markdown(f"**Circuit Track Deficit ({parsed_course_key}):**")
                for err in course_errs.values():
                    st.markdown(f" * ❌ {err}")
                    
            # ─── INJECTED DYNAMIC COACH'S ADVICE NOTEBOOK ───
            st.markdown("<br/>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown("#### 📋 DYNAMIC COACH'S TRAINING REMEDY")
                
                if not course_unlocked and "miles" in course_errs:
                    needed_miles = course_specs["unlock_criteria"]["min_lifetime_miles"] - lifetime_miles
                    st.write(f"_*'Lungs and muscular structural durability aren't conditioned to handle this distance safely yet, athlete. Your career odometer is currently short by **{needed_miles:.1f} miles** to qualify. Your next training assignment is a low-intensity, steady-state long run. Keep your heart rate strictly locked in Zone 1 or 2 to safely expand capillary cushioning and stack that endurance volume.'*_")
                elif not course_unlocked and "power" in course_errs:
                    st.write(f"_*'This mountain grade will absolutely stall your leg velocity if you don't build structural hill strength first. Head out to an incline for your next training session and focus entirely on logging a continuous, uninterrupted uphill vertical ascent to feed your Climbing Power pool.'*_")
                elif not course_unlocked and "efficiency" in course_errs:
                    st.write(f"_*'You need sharper neuromuscular turnover and stride length extension to stay on line with this pacing pack. Add a set of short, fast strides or run an intentional flat mile interval during your next track workout. Speed breeds speed!'*_")
                else:
                    st.write("_*'Your general performance foundation is sitting low. Head out to the pavement, log consistent weekly tracking volume blocks, and harvest experience points to lift your Overall Runner Level status.'*_")
                    
        # Scenario B: Eligible Match Arena Rendering
        else:
            # ─── RENDER VISUAL PORTRAITS AND CIRCUIT GRAPHICS SIDE-BY-SIDE ───
            col_img1, col_img2 = st.columns([1, 2])
            with col_img1:
                st.markdown("<p style='text-align:center; font-weight:bold; margin-bottom:4px;'>PACER CHALLENGER</p>", unsafe_allow_html=True)
                display_boss_portrait(selected_boss, boss_specs, size=160)
            with col_img2:
                st.markdown(f"<p style='font-weight:bold; margin-bottom:4px;'>CIRCUIT LAYOUT: {parsed_course_key.upper()}</p>", unsafe_allow_html=True)
                display_course_image(course_specs, height=160)
                
            st.markdown("<br/>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown(f"##### 📋 COURSE CONDITIONS MANUAL: {parsed_course_key.upper()}")
                st.markdown(f"*{course_specs['desc']}*")
                bm1, bm2, bm3 = st.columns(3)
                with bm1: st.metric("🏁 Track Distance", f"{course_specs['dist']} Miles")
                with bm2: st.metric("⛰️ Vertical Ascent", f"+{course_specs['elev']} Feet")
                with bm3: st.metric("⚖️ Bias Criteria", f"{course_specs['bias']} Weighting")
                st.markdown(f"💡 **Tactical Race Strategy:** {course_specs['strat']}")
                
            # Compute simulation weighting metrics based on course bias factors
            if course_specs['bias'] == 'Speed': 
                w_fuel, w_nitro, w_torque = 0.20, 0.60, 0.20
            elif course_specs['bias'] == 'Torque': 
                w_fuel, w_nitro, w_torque = 0.20, 0.20, 0.60
            else: 
                w_fuel, w_nitro, w_torque = 0.34, 0.33, 0.33
                
            # ─── INJECT CLIMATE & ENVIRONMENTAL MASTERY RESILIENCE MODIFIERS ───
            c_tag = course_specs.get("climate_tag", "Neutral")
            environment_bonus_points = 0.0
            
            if c_tag in ["Hot", "Cold"]:
                has_history_count = climate_exposure.get(c_tag, 0)
                if has_history_count >= 5:
                    environment_bonus_points = 0.5
                    st.success(f"☀️ **CLIMATE ADAPTATION ACTIVE:** Your history shows `{has_history_count}` extreme {c_tag.lower()} weather uploads. You receive a **+0.5 Environmental Mastery bonus**!")
                else:
                    environment_bonus_points = -1.0
                    st.warning(f"🌡️ **ENVIRONMENTAL HAZARD:** Track climate is extreme {c_tag.upper()}. You lack a 5-run acclimatization background (Current: `{has_history_count}`). Applying a **-1.0 track performance penalty**!")

            # Harvest 6-Slot equipment bonuses
            gear_ranks = getattr(player, 'equipped_gear', {})
            sh_bonus = float(gear_ranks.get(getattr(player, 'equipped_shoe_name', None), 0) / 10.0)
            su_bonus = float(gear_ranks.get(getattr(player, 'equipped_sunglasses_name', None), 0) / 25.0)
            hg_bonus = float(gear_ranks.get(getattr(player, 'equipped_headgear_name', None), 0) / 25.0)
            sg_bonus = float(gear_ranks.get(getattr(player, 'equipped_singlet_name', None), 0) / 25.0)
            sr_bonus = float(gear_ranks.get(getattr(player, 'equipped_shorts_name', None), 0) / 30.0)
            wt_bonus = float(gear_ranks.get(getattr(player, 'equipped_watch_name', None), 0) / 25.0)
            total_kit_physics_bonus = sh_bonus + su_bonus + hg_bonus + sg_bonus + sr_bonus + wt_bonus
            
            # ─── INTERACTIVE TACTICAL PACING STANCE SELECTOR ───
            st.markdown("<br/>", unsafe_allow_html=True)
            chosen_stance = st.radio(
                "🏃‍♂️ **Select Pre-Race Tactical Execution Stance:**",
                options=["Steady Paceline (Balanced Risk)", "Front-Runner (Early Sprint)", "Sit and Kick (Closing Home Stretch Surge)"],
                index=0,
                horizontal=True
            )
            
            stance_p_mod, stance_r_mod = 1.0, 1.0
            stance_fatigue_penalty = 0
            
            if "Front-Runner" in chosen_stance:
                # Boosts stride turnover but inflicts fatigue wear upon completion
                w_nitro = min(1.0, w_nitro + 0.15)
                stance_fatigue_penalty = 10
                st.caption("🚀 *Front-Runner: Maximizes Stride Efficiency weighting loops. Accumulates +10 extra Fatigue post-race.*")
            elif "Sit and Kick" in chosen_stance:
                # Highly effective on multi-mile endurance layouts
                if course_specs['dist'] >= 3.0:
                    stance_p_mod = 1.15
                    st.caption("⏱️ *Sit and Kick: Drafting strategy grants an absolute +15% performance scoring boost on multi-mile layouts.*")
                else:
                    st.caption("❌ *Sit and Kick: Ineffective on tracks shorter than 3 Miles. No stance bonus applied.*")
            else:
                st.caption("⚖️ *Steady Paceline: Locks consistent cadence velocity loops. Drops extreme physics pacing variations.*")

            # ─── INJECT RACE DAY READINESS FATIGUE MODIFIERS ───
            fatigue_pace_multiplier = 1.0
            if active_fatigue >= 80:
                fatigue_pace_multiplier = 0.82
                st.error(f"🥵 **ATHLETE EXHAUSTED (Fatigue: {active_fatigue}/100):** Your legs are severely overtrained from heavy recent mileage uploads. Race-day pace calculation penalized by **-18%**!")
            elif active_fatigue <= 20:
                fatigue_pace_multiplier = 1.05
                st.success(f"🔋 **ATHLETE FRESH (Fatigue: {active_fatigue}/100):** Muscle tissue is fully recovered and sharp. Stride physics receiving a **+5% freshness velocity boost**!")

            # Final Track Performance Formulas
            player_track_perf = (((p_fuel * w_fuel) + (p_nitro * w_nitro) + (p_torque * w_torque)) * fatigue_pace_multiplier * stance_p_mod) + total_kit_physics_bonus + environment_bonus_points
            rival_track_perf = ((b_fuel * w_fuel) + (b_nitro * w_nitro) + (b_torque * w_torque)) * stance_r_mod
            win_probability_pct = min(99.0, max(1.0, float((player_track_perf / (player_track_perf + rival_track_perf)) * 100.0)))
            gold_bounty = int(boss_specs['gold_reward'] * curr_level * (course_specs['dist'] / 5.0))
            if gold_bounty < 15: 
                gold_bounty = 15 * curr_level

            # Display Runner Spec Comparison Dashboard Card
            with st.container(border=True):
                st.markdown(f"#### 🏃 CHALLENGE MATRIX ANALYSIS: YOU vs {selected_boss}")
                rc1, rc2, rc3 = st.columns(3)
                with rc1:
                    st.markdown("👤 **YOUR CONDITION RATINGS**")
                    st.markdown(f"🔋 Stamina / Stride / Hill: `[{p_fuel}/{p_nitro}/{p_torque}]`")
                    st.markdown(f"🏅 Apparel Bonus: `+{total_kit_physics_bonus:.2f} Pts` active")
                with rc2:
                    st.markdown(f"👿 **RIVAL PACER SPECS (LV {curr_level})**")
                    st.markdown(f"🔋 Stamina / Stride / Hill: `[{b_fuel}/{b_nitro}/{b_torque}]`")
                with rc3:
                    st.markdown("📊 **CHAMPIONSHIP SPLIT FORECAST**")
                    st.metric("Win Probability", f"{win_probability_pct:.1f}%")
                    st.progress(float(win_probability_pct / 100.0))

            # ─── RUN PHYSICS PACING SIMULATOR ENGINE ───
            st.write("")
            if st.button(f"🏁🟢 START MATCH: Release Pacers vs {selected_boss}", use_container_width=True):
                base_seconds_per_mile = 600.0
                
                # Formulate velocity shifts
                p_speed_factor = (p_fuel * 0.1) + (p_nitro * 0.3) + (p_torque * 0.1) + (total_kit_physics_bonus * 0.5) + environment_bonus_points
                r_speed_factor = (b_fuel * 0.1) + (b_nitro * 0.3) + (b_torque * 0.1)
                
                p_total_seconds = max(240.0, (base_seconds_per_mile - (p_speed_factor * 35.0)) / fatigue_pace_multiplier) * course_specs['dist'] + random.uniform(-4, 4)
                r_total_seconds = max(240.0, base_seconds_per_mile - (r_speed_factor * 35.0)) * course_specs['dist'] + random.uniform(-4, 4)
                
                p_time_str = format_finish_time(p_total_seconds)
                r_time_str = format_finish_time(r_total_seconds)

                # Initialize Live Interface Progress Placeholders
                distance_placeholder = st.empty()
                commentary_placeholder = st.empty()
                player_bar_placeholder = st.empty()
                rival_bar_placeholder = st.empty()
                total_dist = course_specs['dist']

                # Animation Stage 1: The Start Line
                distance_placeholder.markdown(f'### 📍 **Mile 0.00** / {total_dist:.2f} Mi')
                commentary_placeholder.info(f'🟢 **START LINE:** The starter pistol fires! You and **{selected_boss}** surge out of the blocks across the **{parsed_course_key}** using a **{chosen_stance.split(" (")[0]}** stance!')
                player_bar_placeholder.progress(0.15, text='🏃‍♂️ **Your Progress** (15%)')
                rival_bar_placeholder.progress(0.15, text=f'⚡ **{selected_boss}** (15%)')
                time.sleep(2.0)

                # Animation Stage 2: The Mid-Race Breakdown
                mid_mile = round(total_dist * 0.5, 2)
                distance_placeholder.markdown(f'### 📍 **Mile {mid_mile:.2f}** / {total_dist:.2f} Mi')
                if total_3wk_miles >= 30.0:
                    commentary_placeholder.success(f'⚡ **MID-RACE ASSESSMENT:** Your excellent 3-week physical training volume of **{total_3wk_miles:.1f} miles** provides a massive endurance shield. You stay locked stride-for-stride with the challenger!')
                    player_bar_placeholder.progress(0.55, text='🏃‍♂️ **Your Progress** (55%)')
                    rival_bar_placeholder.progress(0.50, text=f'⚡ **{selected_boss}** (50%)')
                else:
                    commentary_placeholder.warning(f'🥵 **MID-RACE ASSESSMENT:** Aerobic pressure spikes! Your restricted 3-week mileage profile of **{total_3wk_miles:.1f} miles** limits your oxygen recovery curves. The pacer moves ahead!')
                    player_bar_placeholder.progress(0.42, text='🏃‍♂️ **Your Progress** (42%)')
                    rival_bar_placeholder.progress(0.55, text=f'⚡ **{selected_boss}** (55%)')
                time.sleep(2.5)

                # Animation Stage 3: The Home Stretch Acceleration
                stretch_mile = round(total_dist * 0.9, 2)
                distance_placeholder.markdown(f'### 📍 **Mile {stretch_mile:.2f}** / {total_dist:.2f} Mi')
                if total_kit_physics_bonus >= 0.50:
                    commentary_placeholder.success(f'👟 **THE HOME STRETCH:** Your equipped pro-shop apparel advantage of **+{total_kit_physics_bonus:.2f} points** activates! High energy-return carbon elements maximize your closing sprint pace!')
                    player_bar_placeholder.progress(0.92, text='🏃‍♂️ **Your Progress** (92%)')
                    rival_bar_placeholder.progress(0.85, text=f'⚡ **{selected_boss}** (85%)')
                else:
                    commentary_placeholder.info('🏁 **THE HOME STRETCH:** Minimal kit enhancements detected. It\'s a high-cadence, raw muscular sprint to the tape!')
                    player_bar_placeholder.progress(0.85, text='🏃‍♂️ **Your Progress** (85%)')
                    rival_bar_placeholder.progress(0.86, text=f'⚡ **{selected_boss}** (86%)')
                time.sleep(2.0)

                # Animation Stage 4: The Tape Crossing Finish Hold
                distance_placeholder.markdown(f'### 🏁 **Mile {total_dist:.2f} (Finished)** / {total_dist:.2f} Mi')
                if p_total_seconds < r_total_seconds:
                    commentary_placeholder.success(f'🏁 **FINISH LINE REACHED:** Absolute tactical triumph! You break the tape fractions of a second ahead of **{selected_boss}**!')
                    player_bar_placeholder.progress(1.00, text='🏃‍♂️ **Your Progress** (100% - Winner)')
                    rival_bar_placeholder.progress(0.98, text=f'⚡ **{selected_boss}** (98% - Finished)')
                else:
                    commentary_placeholder.error(f'🏁 **FINISH LINE REACHED:** Heartbreak at the line! **{selected_boss}** leans forward at the tape to edge you out.')
                    player_bar_placeholder.progress(0.98, text='🏃‍♂️ **Your Progress** (98% - Finished)')
                    rival_bar_placeholder.progress(1.00, text=f'⚡ **{selected_boss}** (100% - Winner)')
                time.sleep(3.5)

                # Clear animation canvas objects smoothly
                distance_placeholder.empty()
                commentary_placeholder.empty()
                player_bar_placeholder.empty()
                rival_bar_placeholder.empty()

                # Score Allocation Calculations
                calc_racing_score = int(10000 * (r_total_seconds / p_total_seconds) * (course_specs['dist'] / 5.0))
                calculated_gold_stake = int(gold_bounty + ((calc_racing_score / 150.0) * curr_level))
                
                # Execute Victory Save State Changes
                if p_total_seconds < r_total_seconds:
                    player.gold = getattr(player, 'gold', 0) + calculated_gold_stake
                    player.boss_clears = getattr(player, 'boss_clears', 0) + 1
                    player.boss_levels[selected_boss] = curr_level + 1
                    
                    # Accumulate localized file fatigue parameters
                    
                    # Calculate and save fatigue inline directly to the player schema matrix
                    new_fatigue = min(100, active_fatigue + 15 + stance_fatigue_penalty)
                    if hasattr(player, 'final_metric_data'):
                        player.final_metric_data['fatigue'] = new_fatigue
                    elif isinstance(player.__dict__.get('final_metric_data'), dict):
                        player.__dict__['final_metric_data']['fatigue'] = new_fatigue

                    # Check for rare home-circuit token awards
                    minted_tokens = evaluate_signature_tokens(player, selected_boss, parsed_course_key)
                    token_msg = f" | Unlocked Milestone Relics: {', '.join(minted_tokens)}" if minted_tokens else ""
                    
                    log_m = f"[{datetime.now().strftime('%Y-%m-%d')}] 🏁 Track Match Victory: Conquered {selected_boss} on the {parsed_course_key}! [WIN] Your Time: {p_time_str} | Rival Time: {r_time_str} | Score: {calc_racing_score} | Gold Impact: +{calculated_gold_stake}g.{token_msg}"
                    if not hasattr(player, 'history_logs'): 
                        player.history_logs = []
                    player.history_logs.append(log_m)
                    
                    # Write updated arrays permanently to JSON file
                    with open(FILE_PATH, 'w', encoding='utf-8') as db_file: 
                        json.dump(player.to_dict() if hasattr(player, 'to_dict') else player.__dict__, db_file, default=str, indent=4)
                        
                    st.session_state.last_race_summary = {
                        "is_win": True, "p_time": p_time_str, "r_time": r_time_str, "score": calc_racing_score, 
                        "gold": calculated_gold_stake, "course": parsed_course_key, "dist": course_specs['dist'], "tokens": minted_tokens
                    }
                    st.balloons()
                    st.rerun()
                    
                # Execute Defeat Save State Changes
                else:
                    calc_racing_score = int(calc_racing_score * 0.4)
                    gold_lost = min(getattr(player, 'gold', 0), calculated_gold_stake // 2)
                    player.gold = getattr(player, 'gold', 0) - gold_lost
                    
                    # Defeat still adds minor muscle fatigue
                    # Calculate and save defeat fatigue inline directly to the player schema matrix
                    new_fatigue = min(100, active_fatigue + 8)
                    if hasattr(player, 'final_metric_data'):
                        player.final_metric_data['fatigue'] = new_fatigue
                    elif isinstance(player.__dict__.get('final_metric_data'), dict):
                        player.__dict__['final_metric_data']['fatigue'] = new_fatigue
                    
                    log_m = f"[{datetime.now().strftime('%Y-%m-%d')}] 🏁 Track Match Defeat: Raced {selected_boss} on the {parsed_course_key}! [LOSS] Your Time: {p_time_str} | Rival Time: {r_time_str} | Score: {calc_racing_score} | Gold Impact: -{gold_lost}g."
                    if not hasattr(player, 'history_logs'): 
                        player.history_logs = []
                    player.history_logs.append(log_m)
                    
                    with open(FILE_PATH, 'w', encoding='utf-8') as db_file: 
                        json.dump(player.to_dict() if hasattr(player, 'to_dict') else player.__dict__, db_file, default=str, indent=4)
                        
                    st.session_state.last_race_summary = {
                        "is_win": False, "p_time": p_time_str, "r_time": r_time_str, "score": calc_racing_score, 
                        "gold": gold_lost, "course": parsed_course_key, "dist": course_specs['dist'], "tokens": []
                    }
                    st.rerun()

    # Render Post-Match Overlay Summaries
    if "last_race_summary" in st.session_state:
        res = st.session_state.last_race_summary
        st.markdown("")
        if res["is_win"]:
            st.success(f"""🏆 **LIVE RACE RESULT: COMPETITIVE TRIUMPH !!**
🥇 **YOU CONQUERED THE PACELINES!**
* 📍 **Course Track:** `{res['course']}`
* 📏 **Race Distance:** `{res['dist']:.2f} Miles`
* ⏱️ Your Finish Time: `{res['p_time']}`
* ⏱️ Rival Finish Time: `{res['r_time']}`
* 🎯 Technical Performance Score: `{res['score']:,} PTS`
* 💰 Championship Purse Awarded: **+{res['gold']}g**""")
            if res.get("tokens"):
                st.warning(f"🏅 **HIGH-PRESTIGE UNLOCK:** Added `{res['tokens']}` permanently into your Athlete Trophy Case cabinet!")
        else:
            st.error(f"""💀 **LIVE RACE RESULT: TRACK CIRCUIT DEFEAT !!**
🏁 **PACER OUT-LEANED YOU AT THE LINE!**
* 📍 **Course Track:** `{res['course']}`
* 📏 **Race Distance:** `{res['dist']:.2f} Miles`
* ⏱️ Your Finish Time: `{res['p_time']}`
* ⏱️ Rival Finish Time: `{res['r_time']}`
* 📉 Performance Score Earned: `{res['score']:,} PTS`
* 💸 High-Stakes Entry Entry Lost: **-{res['gold']}g**""")

    # =========================================================================
    # TAB 2: PACER STANDINGS & PROFILES
    # =========================================================================
    with tab_pacers:
        st.markdown("### 👥 Historical Standings & Scouting dossiers")
        st.caption("Inspect unlock benchmarks, attribute points allocations, and your lifetime win/loss statistics against each legendary opponent.")
        st.write("")
        
        for b_name, b_specs in boss_catalog.items():
            b_lvl = int(player.boss_levels.get(b_name, 1))
            st_data = boss_stats.get(b_name, {"wins": 0, "losses": 0, "total": 0})
            w_rate = (st_data["wins"] / max(1, st_data["total"])) * 100.0
            
            b_unlocked, _ = check_is_unlocked(b_specs.get("unlock_criteria"), character_stats, lifetime_miles)
            lock_label = "🔓 ACTIVE CHALLENGER" if b_unlocked else "🔒 GATED CHALLENGER"
            
            with st.container(border=True):
                # Split row into Portrait column and Profile Data column
                bc1, bc2 = st.columns([1, 4])
                with bc1:
                    display_boss_portrait(b_name, b_specs, size=110)
                with bc2:
                    st.markdown(f"#### {b_name} — `Difficulty Rank {b_lvl}`")
                    st.markdown(f"*{b_specs['desc']}*")
                    st.markdown(f"🏅 **Status Status:** `{lock_label}` | 🔋 Stamina: `{b_specs['fuel']}` | ⚡ Stride Efficiency: `{b_specs['nitro']}` | ⛰️ Climbing Power: `{b_specs['torque']}`")
                    st.markdown(f"📊 **Career Standings vs Them:** Encounters: `{st_data['total']}` | Wins: `{st_data['wins']}` | Defeats: `{st_data['losses']}` (Win Rate: `{w_rate:.1f}%`)")
                    
                    if b_specs.get("unlock_criteria"):
                        st.caption(f"⚙️ Entry Standard: {b_specs['unlock_criteria']}")

    # =========================================================================
    # TAB 3: TRACK SELECTION MANUAL
    # =========================================================================
    with tab_tracks:
        st.markdown("### 🗺️ Global Competition Circuit Manual")
        st.caption("Browse world-renowned trial segments, evaluate physical demands weight arrays, and view circuit statistics.")
        st.write("")
        
        track_cols = st.columns(2)
        for t_idx, (t_name, t_specs) in enumerate(course_catalog.items()):
            t_unlocked, _ = check_is_unlocked(t_specs.get("unlock_criteria"), character_stats, lifetime_miles)
            t_lock_label = "🟢 OPEN CIRCUIT" if t_unlocked else "🔴 REGISTERED GATED LOCK"
            t_data = course_stats.get(t_name, {"raced_count": 0})
            
            # Alternate rendering across twin layout columns
            with track_cols[t_idx % 2]:
                with st.container(border=True):
                    display_course_image(t_specs, height=120)
                    st.markdown(f"#### {t_name}")
                    st.markdown(f"*{t_specs['desc']}*")
                    st.markdown(f"📏 **Distance:** `{t_specs['dist']:.2f} Mi` | ⛰️ Vertical Climb: `+{t_specs['elev']} Ft` | 🌡️ Climate Tag: `{t_specs.get('climate_tag', 'Neutral')}`")
                    st.markdown(f"🔒 **Status Entry:** `{t_lock_label}` | 📊 Career Track Raced: `{t_data['raced_count']} Times`")
                    st.markdown(f"⚖️ **Physics Bias Weight:** `{t_specs['bias']}`")
                    
                    if t_specs.get("unlock_criteria"):
                        st.caption(f"⚙️ Unlock Parameters: {t_specs['unlock_criteria']}")

    # =========================================================================
    # FOOTER: DUAL-COLUMN LEDGER RESULTS HISTORY
    # =========================================================================
    st.markdown("<br/><br/>", unsafe_allow_html=True)
    st.markdown("### 📜 Past Race Circuit Standings Ledger")
    historic_races = []
    
    for log in reversed(raw_history):
        log_str = str(log)
        if "Track Match Victory:" in log_str or "Track Match Defeat:" in log_str:
            try:
                date_match = re.search(r'\[([0-9-]+)\]', log_str)
                is_win = "[WIN]" in log_str or "Victory:" in log_str
                
                # Reconstruct track layout key mapping strings
                parsed_historical_course = "Championship Loop"
                for c_name in course_catalog.keys():
                    clean_c = c_name.split(" [")[0]
                    if clean_c in log_str:
                        parsed_historical_course = c_name
                        break
                        
                boss_match = re.search(r'(?:Victory|Defeat):\s*(?:Conquered|Raced|Defeated)\s*(.*?)\s*on', log_str, re.IGNORECASE)
                p_time_match = re.search(r'Your Time:\s*([0-9:.]+)', log_str)
                r_time_match = re.search(r'Rival Time:\s*([0-9:.]+)', log_str)
                gold_impact_match = re.search(r'Gold Impact:\s*([+\\-][0-9]+g)', log_str)
                
                historic_races.append({
                    "Race Date": date_match.group(1) if date_match else "N/A", 
                    "Outcome": "🏆 WON" if is_win else "❌ LOST",
                    "📍 Circuit Track": parsed_historical_course, 
                    "Rival Athlete": boss_match.group(1).strip() if boss_match else "Pace Master",
                    "Your Time": p_time_match.group(1) if p_time_match else "N/A", 
                    "Rival Time": r_time_match.group(1) if r_time_match else "N/A",
                    "Gold Impact": gold_impact_match.group(1) if gold_impact_match else "0g"
                })
            except Exception: 
                pass
                
    if historic_races: 
        st.dataframe(pd.DataFrame(historic_races), use_container_width=True, hide_index=True)
    else: 
        st.info("🏁 No historic race records discovered yet. Clear a circuit milestone duel to log your first standings data!")

