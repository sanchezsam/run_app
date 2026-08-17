# -*- coding: utf-8 -*-
# PART 1 OF 4: COLISEUM ENGINE INITIALIZATION, DEPENDENCIES, AND 3-WEEK MILEAGE SCRAPERS
import streamlit as st
import re
import pandas as pd
import time
import random
from datetime import datetime, timedelta
from run_utils import save_player_profile

def render_coliseum(player, FILE_PATH):
    st.markdown('### 🏟️ THE BIOMETRIC COLISEUM: HIGH-STAKES CIRCUIT')
    st.markdown('Select your Pacer Rival, choose your Running Course Track, and launch physics-based athletic duels driven by your loadout!')
    st.markdown('---')
    
    if not hasattr(player, 'boss_clears') or player.boss_clears is None: player.boss_clears = 0
    if not hasattr(player, 'boss_levels') or not isinstance(player.boss_levels, dict): player.boss_levels = {}
    
    # --- SCAN PASS: DRIVER RATINGS ---
    now_date = datetime.now()
    three_weeks_ago = now_date - timedelta(days=21)
    total_3wk_miles, max_single_run_elevation, fastest_pace_in_window = 0.0, 0.0, 999.0
    
    for log in getattr(player, 'history_logs', []):
        log_str = str(log)
        if 'miles' in log_str.lower() and 'slept' not in log_str.lower():
            try:
                d_match = re.search(r'(?:Run|run|ran|distance):?\s*([0-9.]+)', log_str, re.IGNORECASE)
                if not d_match: d_match = re.search(r'([0-9.]+)\s*(?:miles|mi)', log_str, re.IGNORECASE)
                p_match = re.search(r'Pace:\s*([0-9.]+)', log_str, re.IGNORECASE)
                e_match = re.search(r'Elevation\s*Climbed:\s*\+?([0-9.]+)', log_str, re.IGNORECASE)
                date_match = re.search(r'\[([0-9-]+)\]', log_str)
                is_within_window = True
                if date_match and datetime.strptime(date_match.group(1)[:10], '%Y-%m-%d') < three_weeks_ago: is_within_window = False
                if is_within_window and d_match:
                    total_3wk_miles += float(d_match.group(1))
                    if e_match: max_single_run_elevation = max(max_single_run_elevation, float(e_match.group(1)))
                    if p_match and 2.0 < float(p_match.group(1)) < fastest_pace_in_window: fastest_pace_in_window = float(p_match.group(1))
            except Exception: pass
            
    p_fuel = max(1, min(9, int((total_3wk_miles / 300.0) * 9)))
    p_nitro = max(1, min(9, int(9 - ((fastest_pace_in_window - 5.50) * 1.5)))) if 0 < fastest_pace_in_window < 900.0 else 1
    p_torque = max(1, min(9, int((max_single_run_elevation / 6000.0) * 9)))
    
    is_on_fire = total_3wk_miles >= 45.0
    if is_on_fire:
        p_fuel, p_nitro, p_torque = min(9, p_fuel+2), min(9, p_nitro+2), min(9, p_torque+2)
        st.error("🔥 SPRINT OVERDRIVE ACTIVE: +2 TO ALL ATTRIBUTES ENFORCED !!")
# PART 2 OF 4: MEN'S LEGEND ROSTER AND 30 INTERNATIONAL COURSE CATALOG ENTRIES [C1]
    boss_catalog = {
        'Kilian [GAZELLE]': {'fuel': 3, 'nitro': 4, 'torque': 6, 'gold_reward': 30, 'desc': '🧗 Kilian the Grade Specialist. Unmatched mountain single-track efficiency and vertical ascent torque.'},
        'Usain [CHEETAH]': {'fuel': 2, 'nitro': 9, 'torque': 1, 'gold_reward': 50, 'desc': '⚡ Usain the Sprint Phenomenon. Absolute maximum explosive power that dominates short ovals.'},
        'Eliud [SPRINTER]': {'fuel': 5, 'nitro': 7, 'torque': 3, 'gold_reward': 40, 'desc': '🏃 Eliud the Cadence Rhythm Master. Maintains mechanical marathon pacelines on flat asphalt roads.'},
        'Yiannis [STRIDER]': {'fuel': 9, 'nitro': 3, 'torque': 4, 'gold_reward': 65, 'desc': '🇬🇷 Yiannis the Endurance Beast. Relentless aerobic capacity engine tailored for 100-mile survival bounds.'},
        'Pre [ROADRUNNER]': {'fuel': 4, 'nitro': 6, 'torque': 2, 'gold_reward': 55, 'desc': '🌵 Pre the Desert Predator. High-tempo execution strategy focused on mid-distance tracking channels.'},
        'Haile [FLASH]': {'fuel': 6, 'nitro': 8, 'torque': 4, 'gold_reward': 120, 'desc': '👑 Haile the Multi-Distance King. Flawless versatility balancing heavy endurance splits with extreme closing speed.'}
    }
    
    course_catalog = {
        'Berlin Olympiastadion Track': {'dist': 0.25, 'elev': 0, 'bias': 'Speed', 'desc': '🇩🇪 The historic, lightning-fast 400m track in Germany.', 'strat': 'Pure anaerobic sprint power. Max out your Sunglasses and Footwear tuning ranks to slice lap splits.'},
        'Monaco Diamond League 1500m': {'dist': 0.93, 'elev': 2, 'bias': 'Speed', 'desc': '🇲🇨 Premium middle-distance stadium circuit on the Mediterranean coast.', 'strat': 'Aggressive threshold velocity test. Requires high Sprint Velocity and max performance watches.'},
        'Monza F1 Breaking2 Grid': {'dist': 1.50, 'elev': 0, 'bias': 'Speed', 'desc': '🇮🇹 The legendary flat Formula 1 tarmac in Italy used for elite marathon barriers.', 'strat': 'Dead flat, hyper-optimized racing lines. Keeps cadence velocity locked at 100% output efficiency.'},
        'Boston Marathon (Hopkinton to Copley)': {'dist': 26.22, 'elev': 850, 'bias': 'Balanced', 'desc': '🇺🇸 World’s oldest annual marathon course, featuring Newton’s notorious Heartbreak Hill.', 'strat': 'Pushes both pacing endurance and descending muscle durability. Balanced weights (34% Aerobic, 33% Speed, 33% Strength).'},
        'London Marathon Highway Grid': {'dist': 26.22, 'elev': 120, 'bias': 'Speed', 'desc': '🇬🇧 Flat, fast road course tracing the River Thames alongside millions of roaring spectators.', 'strat': 'Elite pace execution circuit. Leverages high carbon-plated Footwear and streamlined racing Singlets.'},
        'Berlin Speedway (World Record Flat)': {'dist': 26.22, 'elev': 45, 'bias': 'Speed', 'desc': '🇩🇪 The absolute flattest major marathon course on Earth. Home of human pacing limits.', 'strat': 'Shifts scoring weights heavily toward Sprint Velocity. Lock in elite pacing split telemetry via Garmin watches.'},
        'Zegama-Aizkorri Mountain Skyrun': {'dist': 26.10, 'elev': 8970, 'bias': 'Torque', 'desc': '🇪🇸 Legendary technical alpine marathon in the Basque Country under heavy downpours.', 'strat': 'Absolute mountain torture. Shifts 60% of physics weight to Hill Climb Power. Rugged trail Footwear is non-negotiable.'},
        'UTMB Mont-Blanc Core Loop': {'dist': 106.00, 'elev': 32800, 'bias': 'Fuel', 'desc': '🇫🇷 The pinnacle of global trail running. Encircles the Mont-Blanc massif across France, Italy, and Switzerland.', 'strat': 'Extreme high-altitude ultramarathon. Pushes Fuel Capacity to the absolute threshold. Full 6-slot kit upgrades shape survival scores.'},
        'Western States 100 Canyons': {'dist': 100.00, 'elev': 18000, 'bias': 'Fuel', 'desc': '🇺🇸 World’s oldest 100-mile trail race, tracing hot, rugged singletracks in California Sierra Nevada.', 'strat': 'Severe canyon heat endurance test. Maximizes Aerobic Capacity. Requires max-tier headwear cooling and hydration belt layouts.'},
        'Comrades Ultra Marathon (Up-Run)': {'dist': 54.00, 'elev': 5900, 'bias': 'Fuel', 'desc': '🇿🇦 Legendary paved ultra between Durban and Pietermaritzburg in South Africa.', 'strat': 'Relentless highway climbing and muscle fatigue. Demands maximum 3-week log volume to build necessary stamina buffers.'},
        'UNM 400-Meter Olympic Track': {'dist': 0.25, 'elev': 0, 'bias': 'Speed', 'desc': '🏟️ Pure 400-meter oval track speedway at UNM in Albuquerque.', 'strat': 'Pure, absolute maximum velocity test. Shifts 60% of the weight to Sprint Velocity.'},
        'UNM 800-Meter Tactical Oval': {'dist': 0.50, 'elev': 5, 'bias': 'Speed', 'desc': '⚡ Two-lap tactical middle-distance oval.', 'strat': 'Demands explosive initial sprint velocity balanced with visual focus.'},
        'Santa Fe 1600-Meter Milestoning Grid': {'dist': 1.00, 'elev': 25, 'bias': 'Speed', 'desc': '🏃 Classic 1-Mile premium high-altitude asphalt circuit.', 'strat': 'Tests anaerobic stride efficiency.'},
        'White Sands 5K Desert Horizon': {'dist': 3.11, 'elev': 40, 'bias': 'Speed', 'desc': '☀️ Flat 5-Kilometer speedway loop across gypsum sands.', 'strat': 'Dead flat sands require high cadence. Favors high Sprint Velocity.'},
        'White Sands Desert Speedway': {'dist': 4.00, 'elev': 50, 'bias': 'Speed', 'desc': '☀️ Extended dead-flat white gypsum dunes trail profile.', 'strat': 'Max out your Sprint Velocity traits.'},
        'Los Alamos Canyon Trail Loop': {'dist': 5.20, 'elev': 450, 'bias': 'Balanced', 'desc': '🏜️ Balanced canyon loop right in Los Alamos.', 'strat': 'Evenly distributes scoring weights (34% Aerobic, 33% Sprint, 33% Hill Climb).'},
        'Bayo Canyon Track Circuit': {'dist': 6.00, 'elev': 180, 'bias': 'Speed', 'desc': '⚡ Flat, high-speed volcanic flats.', 'strat': 'Shifts 60% of the scoring weight to your Sprint Velocity.'},
        'Acoma Pueblo Horizon Dash': {'dist': 6.20, 'elev': 300, 'bias': 'Speed', 'desc': '🏜️ Fast, historic 10K high-desert dirt roads circling the Sky City mesa.', 'strat': 'Elite high-velocity velocity course.'},
        'The Perimeter Mountain Loop': {'dist': 7.50, 'elev': 1250, 'bias': 'Torque', 'desc': '⛰️ Severe technical single-track mesa rim.', 'strat': 'Shifts 60% of the scoring weight to your Hill Climb Torque force.'},
        'Taos Ski Valley Ridge Run': {'dist': 8.50, 'elev': 3100, 'bias': 'Torque', 'desc': '❄️ Extreme technical sky-running circuit across high alpine scree.', 'strat': 'Hardcore mountain climbing test with thin air blockades.'},
        'La Luz Trail (Sandia Peak)': {'dist': 9.00, 'elev': 3775, 'bias': 'Torque', 'desc': '🧗 Legendary vertical climbing beast in Albuquerque.', 'strat': 'Severe vertical torture test. Amplifies Engine Torque demands.'},
        'Santa Fe Crest Trail Pipeline': {'dist': 12.00, 'elev': 2100, 'bias': 'Balanced', 'desc': '🌲 Alpine single-track navigating high elevation heights from Ski Santa Fe.', 'strat': 'High-altitude lung burner. Balanced criteria matrix.'},
        'Gila Wilderness River Canyon': {'dist': 15.00, 'elev': 1100, 'bias': 'Fuel', 'desc': '🌲 Deep wilderness track with multiple river crossings.', 'strat': 'Demands heavy rugged endurance reserves and maximum footwear protection.'},
        'Albuquerque Half-Marathon Highway': {'dist': 13.11, 'elev': 250, 'bias': 'Fuel', 'desc': '🛣️ Flat, paved continuous road thoroughfare tracing the Rio Grande.', 'strat': 'Shifts scoring weights heavily to Aerobic Capacity (Endurance).'},
        'Jemez Mountain 25K Technical Loop': {'dist': 15.53, 'elev': 2800, 'bias': 'Torque', 'desc': '🌲 Punishing technical single-track loop circling ancient volcanic rims.', 'strat': 'Severe mountain test. Demands high Hill Climb Power.'},
        'Sandia Crest 50K Skymarathon': {'dist': 31.07, 'elev': 6200, 'bias': 'Torque', 'desc': '🧗 Brutal 50-Kilometer skyrunning loop climbing from base to peak.', 'strat': 'Ultramarathon endurance mixed with vertical torture.'},
        'Shiprock Ultra Desert Horizon': {'dist': 31.00, 'elev': 850, 'bias': 'Fuel', 'desc': '🦅 Brutal, high-mileage volcanic desert flats in the Navajo Nation.', 'strat': 'Pushes your Fuel Tank Aerobic Capacity to the absolute maximum.'},
        'Jemez Mountain 50-Mile Ultra Rim': {'dist': 50.00, 'elev': 10500, 'bias': 'Fuel', 'desc': '🌲 Massive mountain 50-miler climbing across raw caldera ridges.', 'strat': 'Extreme distance testing. Aerobic Capacity dictates survival ratios.'},
        'Gila Wilderness 100-Kilometer Spine': {'dist': 62.14, 'elev': 7400, 'bias': 'Fuel', 'desc': '🌲 Remote, deep continental divide wilderness single-track trail corridor.', 'strat': 'Elite endurance loop. Pushes Fuel Capacity to the absolute brink.'},
        'Taos Alpine 100-Mile Torture Loop': {'dist': 100.00, 'elev': 22000, 'bias': 'Fuel', 'desc': '❄️ Pinnacle century ultramarathon traversing high altitude ridges.', 'strat': 'The ultimate test of human endurance. Dominantly weighted toward Aerobic Capacity (Fuel).'}
    }
# PART 3 OF 4: DROPDOWN EXTRACTORS WITH EMBEDDED MILEAGE AND SCOUTING BUFFS
    sel_c1, sel_c2 = st.columns(2)
    with sel_c1: selected_boss = st.selectbox("Select Men's Pacer Legend:", options=list(boss_catalog.keys()))
    
    # FIXED INTEGRATION FEATURE: Dynamically append the exact track distance directly into selection drop-down labels [C1]
    formatted_dropdown_options = [f"{c_name} [{c_info['dist']:.2f} Mi]" for c_name, c_info in course_catalog.items()]
    
    with sel_c2:
        selected_course_raw = st.selectbox('Select Running Course Track:', options=formatted_dropdown_options)
        
    # Unpack raw dictionary keys by slicing out the embedded distance suffix at the bracket anchor [C1]
    parsed_course_key = selected_course_raw.split(" [")[0]
        
    boss_specs = boss_catalog[selected_boss]
    course_specs = course_catalog[parsed_course_key]
    curr_level = int(player.boss_levels.get(selected_boss, 1))
    b_fuel, b_nitro, b_torque = min(9, boss_specs['fuel']+(curr_level-1)), min(9, boss_specs['nitro']+(curr_level-1)), min(9, boss_specs['torque']+(curr_level-1))
    
    with st.container(border=True):
        st.markdown(f"### 🗺️ COURSE BRIEFING MANUAL: {parsed_course_key.upper()}")
        st.markdown(f"*{course_specs['desc']}*")
        bm1, bm2, bm3 = st.columns(3)
        with bm1: st.metric("🏁 Track Distance", f"{course_specs['dist']} Miles")
        with bm2: st.metric("⛰️ Vertical Ascent", f"+{course_specs['elev']} Feet")
        with bm3: st.metric("⚖️ Dominant Bias Factor", f"{course_specs['bias']} Power")
        st.markdown(f"💡 **Tactical Race Strategy:** {course_specs['strat']}")
    
    if course_specs['bias'] == 'Speed': w_fuel, w_nitro, w_torque = 0.20, 0.60, 0.20
    elif course_specs['bias'] == 'Torque': w_fuel, w_nitro, w_torque = 0.20, 0.20, 0.60
    else: w_fuel, w_nitro, w_torque = 0.34, 0.33, 0.33
    
    # --- HARVEST 6-SLOT APPAREL KIT MODULE BONUSES --- [C1, C3]
    gear_ranks = getattr(player, 'equipped_gear', {})
    sh_bonus = float(gear_ranks.get(getattr(player, 'equipped_shoe_name', None), 0) / 10.0)
    su_bonus = float(gear_ranks.get(getattr(player, 'equipped_sunglasses_name', None), 0) / 25.0)
    hg_bonus = float(gear_ranks.get(getattr(player, 'equipped_headgear_name', None), 0) / 25.0)
    sg_bonus = float(gear_ranks.get(getattr(player, 'equipped_singlet_name', None), 0) / 25.0)
    sr_bonus = float(gear_ranks.get(getattr(player, 'equipped_shorts_name', None), 0) / 30.0)
    wt_bonus = float(gear_ranks.get(getattr(player, 'equipped_watch_name', None), 0) / 25.0)
    total_kit_physics_bonus = sh_bonus + su_bonus + hg_bonus + sg_bonus + sr_bonus + wt_bonus
    
    player_track_perf = (p_fuel * w_fuel) + (p_nitro * w_nitro) + (p_torque * w_torque) + total_kit_physics_bonus
    rival_track_perf = (b_fuel * w_fuel) + (b_nitro * w_nitro) + (b_torque * w_torque)
    win_probability_pct = min(99.0, max(1.0, float((player_track_perf / (player_track_perf + rival_track_perf)) * 100.0)))
    gold_bounty = int(boss_specs['gold_reward'] * curr_level * (course_specs['dist'] / 5.0))
    
    with st.container(border=True):
        st.markdown(f"#### 🏃 RUNNER SPEC CARDS: {selected_boss} vs YOU")
        rc1, rc2, rc3 = st.columns(3)
        with rc1:
            st.markdown("👤 **YOUR TRAIT RATINGS**")
            st.markdown(f"🔋 Aerobic / Speed / Hill: `[{p_fuel}/{p_nitro}/{p_torque}]`")
            st.markdown(f"🏅 Kit Advantage: `+{total_kit_physics_bonus:.2f} Pts` active.")
        with rc2:
            st.markdown(f"👿 **RIVAL PACER SPECS (LV {curr_level})**")
            st.markdown(f"🔋 Aerobic / Speed / Hill: `[{b_fuel}/{b_nitro}/{b_torque}]`")
        with rc3:
            st.markdown("📊 **CHAMPIONSHIP SPLIT FORECAST**")
            st.metric("Win Probability", f"{win_probability_pct:.1f}%")
            st.progress(float(win_probability_pct / 100.0))
# PART 4 OF 4: TIME TRACK SIMULATORS, DYNAMIC BANNERS, AND DUAL-COLUMN LEDGER HISTORY RECORDS [C1]
    if st.button(f"🏁🟢 GREEN LIGHT: Launch Track Match vs {selected_boss}"):
        base_seconds_per_mile = 600.0
        p_speed_factor = (p_fuel * 0.1) + (p_nitro * 0.3) + (p_torque * 0.1) + (total_kit_physics_bonus * 0.5) + (wt_bonus * 0.2)
        r_speed_factor = (b_fuel * 0.1) + (b_nitro * 0.3) + (b_torque * 0.1)
        p_total_seconds = max(240.0, base_seconds_per_mile - (p_speed_factor * 35.0) + random.uniform(-5, 5)) * course_specs['dist']
        r_total_seconds = max(240.0, base_seconds_per_mile - (r_speed_factor * 35.0) + random.uniform(-5, 5)) * course_specs['dist']
        
        def format_finish_time(secs):
            ts = str(timedelta(seconds=int(secs)))
            ms = int((secs - int(secs)) * 1000)
            return f"{ts}.{ms:03d}"
            
        p_time_str = format_finish_time(p_total_seconds)
        r_time_str = format_finish_time(r_total_seconds)

        # =========================================================================
        # INJECTED: LIVE PROGRESS BARS WITH MILE SELECTION AND 5-SECOND FINISH FREEZE
        # =========================================================================
        distance_placeholder = st.empty()
        commentary_placeholder = st.empty()
        player_bar_placeholder = st.empty()
        rival_bar_placeholder = st.empty()
        total_dist = course_specs['dist']

        # STAGE 1: THE START LINE
        distance_placeholder.markdown('### 📍 **Mile 0.00** / ' + str(round(total_dist, 2)) + ' Mi')
        commentary_placeholder.info('🟢 **START LINE:** The starter pistol fires! You and **' + str(selected_boss) + '** surge out of the blocks across the **' + str(parsed_course_key) + '**!')
        player_bar_placeholder.progress(0.15, text='🏃‍♂️ **Your Progress** (15%)')
        rival_bar_placeholder.progress(0.15, text='⚡ **' + str(selected_boss) + '** (15%)')
        time.sleep(3.0)

        # STAGE 2: THE MID-RACE ACCELERATION
        mid_mile = round(total_dist * 0.5, 2)
        distance_placeholder.markdown('### 📍 **Mile ' + str(mid_mile) + '** / ' + str(round(total_dist, 2)) + ' Mi')
        if total_3wk_miles >= 30.0:
            commentary_placeholder.success('⚡ **MID-RACE BREAKDOWN:** Your strong 3-week fitness load of **' + str(round(total_3wk_miles, 1)) + ' miles** is providing a solid aerobic stamina buffer. You match **' + str(selected_boss) + '** stride-for-stride!')
            player_bar_placeholder.progress(0.55, text='🏃‍♂️ **Your Progress** (55%)')
            rival_bar_placeholder.progress(0.50, text='⚡ **' + str(selected_boss) + '** (50%)')
        else:
            commentary_placeholder.warning('🥵 **MID-RACE BREAKDOWN:** Aerobic pressure mounting! Your limited 3-week volume of **' + str(round(total_3wk_miles, 1)) + ' miles** leaves you searching for deep recovery reserves. Pacer takes the lead!')
            player_bar_placeholder.progress(0.42, text='🏃‍♂️ **Your Progress** (42%)')
            rival_bar_placeholder.progress(0.55, text='⚡ **' + str(selected_boss) + '** (55%)')
        time.sleep(3.5)

        # STAGE 3: THE HOME STRETCH
        stretch_mile = round(total_dist * 0.9, 2)
        distance_placeholder.markdown('### 📍 **Mile ' + str(stretch_mile) + '** / ' + str(round(total_dist, 2)) + ' Mi')
        if total_kit_physics_bonus >= 0.50:
            commentary_placeholder.success('👟 **THE HOME STRETCH:** Your equipped gear advantage of **+' + str(round(total_kit_physics_bonus, 2)) + ' points** activates! Carbon-plated shoes grant maximum closing velocity!')
            player_bar_placeholder.progress(0.92, text='🏃‍♂️ **Your Progress** (92%)')
            rival_bar_placeholder.progress(0.85, text='⚡ **' + str(selected_boss) + '** (85%)')
        else:
            commentary_placeholder.info('🏁 **THE HOME STRETCH:** Minimal kit enhancements detected. It\'s a dead heat, high-cadence sprint to the tape!')
            player_bar_placeholder.progress(0.85, text='🏃‍♂️ **Your Progress** (85%)')
            rival_bar_placeholder.progress(0.86, text='⚡ **' + str(selected_boss) + '** (86%)')
        time.sleep(2.5)

        # STAGE 4: THE FINISH LINE WITH A 5-SECOND STATE HOLD
        distance_placeholder.markdown('### 🏁 **Mile ' + str(round(total_dist, 2)) + ' (Finished)** / ' + str(round(total_dist, 2)) + ' Mi')
        if p_total_seconds < r_total_seconds:
            commentary_placeholder.success('🏁 **FINISH LINE REACHED:** Absolute triumph! You cross the finish line tape fractions of a second ahead of **' + str(selected_boss) + '**!')
            player_bar_placeholder.progress(1.00, text='🏃‍♂️ **Your Progress** (100% - Finished)')
            rival_bar_placeholder.progress(0.98, text='⚡ **' + str(selected_boss) + '** (98% - Finished)')
        else:
            commentary_placeholder.error('🏁 **FINISH LINE REACHED:** Heartbreak at the line! **' + str(selected_boss) + '** out-leans you at the tape to claim victory.')
            player_bar_placeholder.progress(0.98, text='🏃‍♂️ **Your Progress** (98% - Finished)')
            rival_bar_placeholder.progress(1.00, text='⚡ **' + str(selected_boss) + '** (100% - Finished)')
        time.sleep(5.0)

        # Dismount animation canvases to smoothly reveal summary boxes
        distance_placeholder.empty()
        commentary_placeholder.empty()
        player_bar_placeholder.empty()
        rival_bar_placeholder.empty()
        # =========================================================================

        
        calc_racing_score = int(10000 * (r_total_seconds / p_total_seconds) * (course_specs['dist'] / 5.0))
        base_gold_pool = int(boss_specs['gold_reward'] * (course_specs['dist'] / 5.0))
        calculated_gold_stake = int(base_gold_pool + ((calc_racing_score / 120.0) * curr_level))
        
        if calculated_gold_stake < 10: calculated_gold_stake = int(10 * curr_level)
        
        if player_track_perf >= rival_track_perf and p_total_seconds < r_total_seconds:
            player.gold = getattr(player, 'gold', 0) + calculated_gold_stake
            player.boss_clears = getattr(player, 'boss_clears', 0) + 1
            player.boss_levels[selected_boss] = curr_level + 1
            log_m = f"[{datetime.now().strftime('%Y-%m-%d')}] 🏁 Track Match Victory: Conquered {selected_boss} on the {parsed_course_key}! [WIN] Your Time: {p_time_str} | Rival Time: {r_time_str} | Score: {calc_racing_score} | Gold Impact: +{calculated_gold_stake}g."
            if not hasattr(player, 'history_logs'): player.history_logs = []
            player.history_logs.append(log_m)
            save_player_profile(player, FILE_PATH)
            st.session_state.last_race_summary = {
                "is_win": True, "p_time": p_time_str, "r_time": r_time_str, "score": calc_racing_score, 
                "gold": calculated_gold_stake, "course": parsed_course_key, "dist": course_specs['dist']
            }
            st.balloons(); st.rerun()
        else:
            calc_racing_score = int(calc_racing_score * 0.4)
            gold_lost = min(getattr(player, 'gold', 0), calculated_gold_stake)
            player.gold = getattr(player, 'gold', 0) - gold_lost
            log_m = f"[{datetime.now().strftime('%Y-%m-%d')}] 🏁 Track Match Defeat: Raced {selected_boss} on the {parsed_course_key}! [LOSS] Your Time: {p_time_str} | Rival Time: {r_time_str} | Score: {calc_racing_score} | Gold Impact: -{gold_lost}g."
            if not hasattr(player, 'history_logs'): player.history_logs = []
            player.history_logs.append(log_m)
            save_player_profile(player, FILE_PATH)
            st.session_state.last_race_summary = {
                "is_win": False, "p_time": p_time_str, "r_time": r_time_str, "score": calc_racing_score, 
                "gold": gold_lost, "course": parsed_course_key, "dist": course_specs['dist']
            }
            st.rerun()

    if "last_race_summary" in st.session_state:
        res = st.session_state.last_race_summary
        st.markdown("")
        if res["is_win"]:
            st.success(f"""🏆 **LIVE RACE RESULT: VICTORY !!**

🥇 **YOU WON THE MATCH!**
* 📍 **Course Track:** `{res['course']}`
* 📏 **Race Distance:** `{res['dist']:.2f} Miles`
* ⏱️ Your Finish Time: `{res['p_time']}`
* ⏱️ Rival Finish Time: `{res['r_time']}`
* 🎯 Racing Score: `{res['score']:,} PTS`
* 💰 Performance Gold Won: **+{res['gold']}g**""")
        else:
            st.error(f"""💀 **LIVE RACE RESULT: DEFEAT !!**

🏁 **YOU LOST THE MATCH!**
* 📍 **Course Track:** `{res['course']}`
* 📏 **Race Distance:** `{res['dist']:.2f} Miles`
* ⏱️ Your Finish Time: `{res['p_time']}`
* ⏱️ Rival Finish Time: `{res['r_time']}`
* 📉 Racing Score: `{res['score']:,} PTS`
* 💸 High-Stakes Penalty Lost: **-{res['gold']}g**""")

    st.markdown("---")
    st.markdown("### 🏆 Past Race Circuit Results & Standings")
    historic_races = []
    for log in getattr(player, 'history_logs', []):
        log_str = str(log)
        if "Track Match Victory:" in log_str or "Track Match Defeat:" in log_str or "Circuit Victory:" in log_str or "Circuit Defeat:" in log_str:
            try:
                date_match = re.search(r'\[([0-9-]+)\]', log_str)
                is_win = "[WIN]" in log_str or "Victory:" in log_str
                course_match = re.search(r'on\s+the\s+(.*?)\s*\!', log_str, re.IGNORECASE)
                if not course_match: course_match = re.search(r'Conquered\s+(.*?)\s*on', log_str, re.IGNORECASE)
                if not course_match: course_match = re.search(r'Raced\s+(.*?)\s*on', log_str, re.IGNORECASE)
                parsed_historical_course = course_match.group(1).strip() if course_match else "Championship Loop"
                
                matched_distance_str = "N/A"
                for c_name, c_data in course_catalog.items():
                    if c_name.lower() in parsed_historical_course.lower() or parsed_historical_course.lower() in c_name.lower():
                        matched_distance_str = f"{c_data['dist']:.2f} Miles"
                        parsed_historical_course = c_name
                        break
                
                boss_match = re.search(r'(?:Victory|Defeat):\s*(?:Conquered|Raced|Defeated)\s*(.*?)\s*on', log_str, re.IGNORECASE)
                p_time_match = re.search(r'Your Time:\s*([0-9:.]+)', log_str)
                r_time_match = re.search(r'Rival Time:\s*([0-9:.]+)', log_str)
                gold_impact_match = re.search(r'Gold Impact:\s*([+\\-][0-9]+g)', log_str)
                
                historic_races.append({
                    "Race Date": date_match.group(1) if date_match else "N/A", "Outcome": "🏆 WON" if is_win else "❌ LOST",
                    "📍 Selected Circuit Track": parsed_historical_course, "📏 Route Distance": matched_distance_str,
                    "Rival Athlete": boss_match.group(1).strip() if boss_match else "Pace Master",
                    "Your Time": p_time_match.group(1) if p_time_match else "N/A", "Rival Time": r_time_match.group(1) if r_time_match else "N/A",
                    "Gold Impact": gold_impact_match.group(1) if gold_impact_match else "0g"
                })
            except Exception: pass
    if historic_races: st.dataframe(pd.DataFrame(historic_races).sort_values(by="Race Date", ascending=False), use_container_width=True, hide_index=True)
    else: st.info("🏁 No historic race records discovered yet. Clear a circuit milestone duel to log your first standings data!")

