# -*- coding: utf-8 -*-
"""
ATHLETIC TRAINING HUB — TELEMETRY SYNC INTERFACE MODULE
Handles multi-file batch uploads for Garmin .FIT and .GPX data streams, implements 
pre-stage de-duplication checks, maps training stress ratings, and updates milestone ledgers.
Completely decoupled from automotive and engine terminology.
"""

import streamlit as st
import json
import os
import re
import math
import random
import time
from datetime import datetime, timedelta
from services import parse_garmin_fit
import pandas as pd
from typing import List
from metrics_config import FINAL_METRIC_CONFIG

# ==============================================================================
# 📊 PART 1: ACUTE MOMENTUM PROFILE RATINGS & PROGRESSION LOGIC
# ==============================================================================

def compute_current_ratings(logs_array, current_stamina_rating=100, current_efficiency_rating=100, current_power_rating=100):
    """
    Calculates dynamic upward and downward level trends based on comparative 
    performance intensity rather than strict calendar date expiration gates.
    """
    # Baseline expected targets per current level ranking tier
    stamina_level = max(1, min(9, int(current_stamina_rating / 100) + 1))
    efficiency_level = max(1, min(9, int(current_efficiency_rating / 100) + 1))
    power_level = max(1, min(9, int(current_power_rating / 100) + 1))
    
    # Calculate baseline expectations based on current tier ranks
    expected_distance = stamina_level * 2.0       # Level 3 expects 6 miles
    expected_pace = 11.0 - (efficiency_level * 0.5) # Level 6 expects an 8:00 min/mi pace
    expected_elevation = power_level * 150.0      # Level 4 expects 600 ft of climbing
    
    total_rolling_miles = 0.0
    
    # Process only the single incoming run batch to calculate trend deltas
    for entry in logs_array[-1:]:  # Focus strictly on processing the latest ingestion log
        if isinstance(entry, dict):
            #dist = float(entry.get("Distance (Miles)", entry.get("dist", 0.0)))
            #pace = float(entry.get("pace", 0.0))
            dist = float(entry.get("Distance (Miles)", entry.get("dist", 0.0)))

            # --- SAFE FORMAT PARSER FOR DECIMAL FLOATS OR CLOCK STRINGS ---
            raw_pace_val = entry.get("pace", 0.0)
            if isinstance(raw_pace_val, (int, float)):
                pace = float(raw_pace_val)
            else:
                try:
                    if isinstance(raw_pace_val, str) and ":" in raw_pace_val:
                        parts = raw_pace_val.strip().split(":")
                        pace_min_part = int(parts[0])
                        pace_sec_part = int(parts[1])
                        pace = float(pace_min_part + (pace_sec_part / 60.0))
                    else:
                        pace = float(raw_pace_val)
                except (ValueError, TypeError, IndexError):
                    pace = 11.0  # Safe recovery baseline pace

            
            ele = entry.get("Elevation (ft)", entry.get("ele", 0.0))
            if isinstance(ele, str):
                ele = float(ele.replace('+', '').replace('ft', '').strip())
            ele = float(ele)
        else:
            # Fallback regex parsing for raw text log blocks
            entry_str = str(entry)
            d_m = re.search(r'(?:Run|run|ran|distance):?\s*([0-9.]+)', entry_str, re.IGNORECASE)
            p_m = re.search(r'(?:Pace|pace):\s*([0-9.]+)', entry_str, re.IGNORECASE)
            e_m = re.search(r'(?:Elevation|elevation|Climbed):\s*\+?([0-9.]+)', entry_str, re.IGNORECASE)
            
            dist = float(d_m.group(1)) if d_m else 0.0
            pace = float(p_m.group(1)) if p_m else 0.0
            ele = float(e_m.group(1)) if e_m else 0.0

        if dist <= 0:
            continue
            
        total_rolling_miles += dist

        # 🔋 1. AEROBIC STAMINA CAPACITY TREND
        dist_delta = dist - expected_distance
        if dist_delta >= 0:
            # Upward Trend: Earn more points for pushing past your current target
            current_stamina_rating += int(dist_delta * 15) + 10
        else:
            # Downward Trend: Lose rating points if the run was shorter than expected
            current_stamina_rating += int(dist_delta * 8) - 5

        # ⚡ 2. STRIDE EFFICIENCY TREND
        if pace > 3.0:
            pace_delta = expected_pace - pace # Positive means you ran faster than expected
            if pace_delta >= 0:
                # Upward Trend
                current_efficiency_rating += int(pace_delta * 40) + 12
            else:
                # Downward Trend
                current_efficiency_rating += int(pace_delta * 20) - 8

        # 🏔️ 3. VERTICAL CLIMBING POWER TREND
        ele_delta = ele - expected_elevation
        if ele_delta >= 0:
            # Upward Trend
            current_power_rating += int(ele_delta * 0.15) + 10
        else:
            # Downward Trend
            current_power_rating += int(ele_delta * 0.08) - 5

    # Enforce minimum boundaries and maximum caps [Level 1 to Level 9]
    current_stamina_rating = max(0, min(899, current_stamina_rating))
    current_efficiency_rating = max(0, min(899, current_efficiency_rating))
    current_power_rating = max(0, min(899, current_power_rating))

    # Recalculate level outputs dynamically from the updated rating numbers
    final_stamina_lvl = int(current_stamina_rating / 100) + 1
    final_efficiency_lvl = int(current_efficiency_rating / 100) + 1
    final_power_lvl = int(current_power_rating / 100) + 1

    return final_stamina_lvl, final_efficiency_lvl, final_power_lvl, total_rolling_miles, current_stamina_rating, current_efficiency_rating, current_power_rating

# ==============================================================================
# 🎨 PART 2: TELEMETRY SYNC DASHBOARD VIEWPORT INTERFACE TERMINAL
# ==============================================================================

def render_upload_interface(player, FILE_PATH, database_file_path=None):
    st.markdown('## 🛰️ Telemetry Sync Dashboard')
    st.markdown('Ingest fresh Garmin GPX/FIT workout tracking files to update your odometer, generate career experience, and harvest performance gold.')
    st.markdown('---')
    
    if 'uploader_reset_token' not in st.session_state:
        st.session_state.uploader_reset_token = 0
        
    st.markdown('### 📥 Bulk Upload Workout Tracks')
    
    uploaded_files = st.file_uploader(
        'Choose one or more Garmin activity files:', 
        type=["tcx", "gpx", "csv", "fit"],
        accept_multiple_files=True, 
        key=f'gpx_uploader_bulk_token_{st.session_state.uploader_reset_token}'
    )
    if uploaded_files:
        st.markdown('---')
        st.markdown(f"### 📋 Staged Queue Batch Analysis ({len(uploaded_files)} Activities)")
        
        staged_sessions = []
        total_batch_distance = 0.0
        historical_logs = getattr(player, 'history_logs', [])
        
        for idx, file_obj in enumerate(uploaded_files):
            try:
                file_extension = file_obj.name.split('.')[-1].lower()
                file_bytes = file_obj.read()
                
                # --- PRE-STAGE DE-DUPLICATION CHECKER ---
                chk_date = datetime.now().strftime('%Y-%m-%d')
                chk_dist = 0.0
                chk_dur = "00:00:00"
                fit_metrics_temp = None
                
                if file_extension == "fit":
                    fit_metrics_temp = parse_garmin_fit(file_bytes)
                    chk_date = fit_metrics_temp.get("date", chk_date)[:10]
                    chk_dist = round(fit_metrics_temp.get("distance_mi", 0.0), 2)
                    
                    t_secs = int(fit_metrics_temp.get("duration_seconds", 0))
                    chk_dur = f"{t_secs // 3600:02d}:{(t_secs % 3600) // 60:02d}:{t_secs % 60:02d}"
                else:
                    file_text_temp = file_bytes.decode('utf-8', errors='ignore')
                    t_strings = re.findall(r'<time>(.*?)</time>', file_text_temp, re.IGNORECASE)
                    if t_strings:
                        chk_date = t_strings[0][:10]
                    
                    track_points_temp = re.findall(r'<trkpt\s+lat="([-0-9.]+)"\s+lon="([-0-9.]+)".*?>(.*?)</trkpt>', file_text_temp, re.DOTALL)
                    calculated_distance_miles_temp = 0.0
                    total_moving_seconds_temp = 0.0
                    
                    for i in range(len(track_points_temp) - 1):
                        lat1 = math.radians(float(track_points_temp[i][0]))
                        lon1 = math.radians(float(track_points_temp[i][1]))
                        lat2 = math.radians(float(track_points_temp[i+1][0]))
                        lon2 = math.radians(float(track_points_temp[i+1][1]))
                        
                        dlat = lat2 - lat1
                        dlon = lon2 - lon1
                        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
                        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                        seg_dist = 3958.8 * c
                        
                        seg_sec = 4.0
                        try:
                            pt1_t = re.search(r'<time>(.*?)</time>', track_points_temp[i][2], re.IGNORECASE)
                            pt2_t = re.search(r'<time>(.*?)</time>', track_points_temp[i+1][2], re.IGNORECASE)
                            if pt1_t and pt2_t:
                                t1 = datetime.strptime(pt1_t.group(1)[:19].replace('T', ' '), '%Y-%m-%d %H:%M:%S')
                                t2 = datetime.strptime(pt2_t.group(1)[:19].replace('T', ' '), '%Y-%m-%d %H:%M:%S')
                                seg_sec = max(0.0, float((t2 - t1).total_seconds()))
                        except Exception: pass
                        
                        seg_mph = (seg_dist / seg_sec) * 3600.0 if seg_sec > 0 else 0.0
                        if seg_dist > 0 and seg_mph > 0.5:
                            calculated_distance_miles_temp += seg_dist
                            total_moving_seconds_temp += seg_sec
                            
                    if total_moving_seconds_temp == 0 and len(t_strings) >= 2:
                        try:
                            t_start = datetime.strptime(t_strings[0][:19].replace('T', ' '), '%Y-%m-%d %H:%M:%S')
                            t_end = datetime.strptime(t_strings[-1][:19].replace('T', ' '), '%Y-%m-%d %H:%M:%S')
                            total_moving_seconds_temp = max(60, int((t_end - t_start).total_seconds()))
                        except Exception: pass
                        
                    chk_dist = round(calculated_distance_miles_temp, 2)
                    chk_dur = str(timedelta(seconds=int(total_moving_seconds_temp)))

                is_file_duplicate = False
                for log_row in historical_logs:
                    if isinstance(log_row, dict):
                        h_date = str(log_row.get("Date", log_row.get("date", "")))[:10]
                        h_dist = round(float(log_row.get("Distance (Miles)", log_row.get("distance_mi", 0.0))), 2)
                        h_dur = str(log_row.get("Duration", log_row.get("duration", ""))).strip()
                        
                        if h_date == chk_date and h_dist == chk_dist and h_dur == chk_dur:
                            is_file_duplicate = True
                            break
                    elif isinstance(log_row, str):
                        log_str = str(log_row)
                        if f"[{chk_date}]" in log_str:
                            d_m = re.search(r'(?:Run|run|ran|distance):?\s*([0-9.]+)', log_str, re.IGNORECASE)
                            if not d_m: d_m = re.search(r'([0-9.]+)\s*(?:miles|mi)', log_str, re.IGNORECASE)
                            dur_m = re.search(r'Duration:\s*([0-9:]+)', log_str, re.IGNORECASE)
                            
                            if d_m and dur_m:
                                h_dist = round(float(d_m.group(1)), 2)
                                h_dur = dur_m.group(1).strip()
                                if h_dist == chk_dist and h_dur == chk_dur:
                                    is_file_duplicate = True
                                    break

                if is_file_duplicate:
                    st.warning(f"⚠️ **Pre-Staging Warning:** `{file_obj.name}` has been filtered out of the batch queue. An identical workout record (Distance: `{chk_dist:.2f} Mi` | Duration: `{chk_dur}`) already exists for date `{chk_date}`.")
                    continue
                    
                file_obj.seek(0)
                
                if file_extension == "fit":
                    if fit_metrics_temp is None:
                        fit_metrics_temp = parse_garmin_fit(file_bytes)
                    
                    calculated_distance_miles = fit_metrics_temp["distance_mi"]
                    total_secs = int(fit_metrics_temp["duration_seconds"])
                    
                    staged_sessions.append({
                        "name": file_obj.name, "date": fit_metrics_temp["date"],  
                        "dist": round(calculated_distance_miles, 2), "duration": chk_dur,  
                        "pace": fit_metrics_temp["pace"], "ele": fit_metrics_temp["elevation_gain_ft"], 
                        "calories": fit_metrics_temp["calories"], "splits": fit_metrics_temp["splits"],
                        "type": "FIT Activity"
                    })
                    total_batch_distance += calculated_distance_miles
                    continue

                file_text = file_bytes.decode('utf-8', errors='ignore')
                track_points = re.findall(r'<trkpt\s+lat="([-0-9.]+)"\s+lon="([-0-9.]+)".*?>(.*?)</trkpt>', file_text, re.DOTALL)
                
                if not track_points:
                    st.warning(f"⚠️ **File Error:** Could not resolve geographic coordinates inside `{file_obj.name}`. Skipping track.")
                    continue
                
                calculated_distance_miles = 0.0
                max_single_elevation_gain = 0.0
                total_moving_seconds = 0.0
                elevations_list = []
                
                time_strings = re.findall(r'<time>(.*?)</time>', file_text, re.IGNORECASE)
                parsed_date_str = time_strings[0][:10] if time_strings else datetime.now().strftime('%Y-%m-%d')
                
                for i in range(len(track_points) - 1):
                    lat1 = math.radians(float(track_points[i][0]))
                    lon1 = math.radians(float(track_points[i][1]))
                    lat2 = math.radians(float(track_points[i+1][0]))
                    lon2 = math.radians(float(track_points[i+1][1]))
                    
                    dlat = lat2 - lat1
                    dlon = lon2 - lon1
                    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
                    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                    segment_distance = 3958.8 * c
                    
                    segment_seconds = 4.0
                    try:
                        pt1_time_match = re.search(r'<time>(.*?)</time>', track_points[i][2], re.IGNORECASE)
                        pt2_time_match = re.search(r'<time>(.*?)</time>', track_points[i+1][2], re.IGNORECASE)
                        if pt1_time_match and pt2_time_match:
                            t1 = datetime.strptime(pt1_time_match.group(1)[:19].replace('T', ' '), '%Y-%m-%d %H:%M:%S')
                            t2 = datetime.strptime(pt2_time_match.group(1)[:19].replace('T', ' '), '%Y-%m-%d %H:%M:%S')
                            segment_seconds = max(0.0, float((t2 - t1).total_seconds()))
                    except Exception: pass
                    
                    segment_mph = (segment_distance / segment_seconds) * 3600.0 if segment_seconds > 0 else 0.0
                    if segment_distance > 0 and segment_mph > 0.5:
                        calculated_distance_miles += segment_distance
                        total_moving_seconds += segment_seconds
                    
                    ele_match = re.search(r'<ele>([-0-9.]+)</ele>', track_points[i][2], re.IGNORECASE)
                    if ele_match:
                        elevations_list.append(float(ele_match.group(1)) * 3.28084)
                        
                for i in range(len(elevations_list) - 1):
                    diff = elevations_list[i+1] - elevations_list[i]
                    if diff > 0: max_single_elevation_gain += diff
                
                if total_moving_seconds == 0 and len(time_strings) >= 2:
                    try:
                        t_start = datetime.strptime(time_strings[0][:19].replace('T', ' '), '%Y-%m-%d %H:%M:%S')
                        t_end = datetime.strptime(time_strings[-1][:19].replace('T', ' '), '%Y-%m-%d %H:%M:%S')
                        total_moving_seconds = max(60, int((t_end - t_start).total_seconds()))
                    except Exception: pass
                
                parsed_distance = round(calculated_distance_miles, 2)
                parsed_elevation = int(max_single_elevation_gain)
                parsed_pace = round((total_moving_seconds / 60.0) / parsed_distance, 2) if parsed_distance > 0.05 else 8.50
                duration_string_hud = str(timedelta(seconds=int(total_moving_seconds)))
                
                total_batch_distance += parsed_distance
                staged_sessions.append({
                    'name': file_obj.name, 'dist': parsed_distance, 'ele': parsed_elevation, 
                    'pace': parsed_pace, 'date': parsed_date_str, 'duration': duration_string_hud,
                    'splits': None, 'type': 'GPX Activity'
                })
            except Exception as e:
                st.error(f"Parsing failure on item {file_obj.name}: {str(e)}")

        if staged_sessions:
            bm1, bm2, bm3 = st.columns(3)
            with bm1: st.metric("Accumulated Batch Distance", f"{total_batch_distance:.2f} Miles")
            with bm2: st.metric("Staged Gold Yield (+10g/mi)", f"+{int(total_batch_distance * 10)}g")
            with bm3: st.metric("Staged Experience Yield", f"+{int(total_batch_distance * 50)} XP")
            
            with st.expander("🔍 View Staged Track Telemetry Breakdown Details", expanded=True):
                for s in staged_sessions:
                    #st.markdown(f"📄 **{s['name']}** — `[{s['date']}]` — `{s['dist']:.2f} Mi` | Running Time: `{s['duration']}` | `{s['pace']:.2f} min/mi` Pace | `+{s['ele']} ft` Climbing")
                    st.markdown(f"📄 **{s['name']}** — `[{s['date']}]` — `{s['dist']:.2f} Mi` | Running Time: `{s['duration']}` | `{s['pace']} min/mi` Pace | `+{s['ele']} ft` Climbing")

                    
                    if "splits" in s and s["splits"] is not None and len(s["splits"]) > 0:
                        with st.expander("⏱️ View Mile Splits Breakdown"):
                            df_splits = pd.DataFrame(s["splits"])
                            df_splits.columns = ["Split #", "Distance (Mi)", "Split Time", "Pace (/mi)", "Avg HR (bpm)", "Max HR (bpm)"]

                            st.dataframe(df_splits, use_container_width=True, hide_index=True)
        
        st.markdown('')

        if staged_sessions and st.button("🟢 Commit All Staged Tracks to Save Profile", key='commit_bulk_gpx_telemetry_btn'):
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
                         # --- FIX: IF IT IS ALREADY A CLOCK STRING, PRESERVE IT WITHOUT CASTING ---
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
                         "Date": s['date'], 
                         "Name": s.get('name', 'Run'), 
                         "Distance (Miles)": float(s['dist']),
                         "Duration": s.get('duration', '00:00:00'),
                         "pace": clean_pace_val,
                         "Elevation (ft)": f"+{s.get('ele', 0)} ft",
                         "splits": s.get('splits', []),
                         "text_payload": text_sentence,
                         "aerobic_decoupling_percent": float(s.get("aerobic_decoupling_percent", 0.0)),
                         "ambient_temp_f": float(s.get("ambient_temp_f", 72.0)),
                         "zone_1_2_duration_percent": round(((z1 + z2) / max(1, z1 + z2 + z3 + z4 + z5)) * 100.0, 2)
                     }
                     player.history_logs.append(structured_log)
         
                 # Update profile values and calorie pools
                 player.gold = getattr(player, 'gold', 50) + total_gold_rewarded
                 player.total_xp = getattr(player, 'total_xp', 0) + total_xp_gained
                 player.calorie_bank_balance += total_calories_ingested
                 player.calorie_bank_total_earned += total_calories_ingested
                 
                 # Extract core trend performance skill attributes
                 st_rating = getattr(player, 'stamina_rating', 100)
                 ef_rating = getattr(player, 'efficiency_rating', 100)
                 pw_rating = getattr(player, 'power_rating', 100)

                 # Run the rating trend calculator engine
                 post_st, post_ef, post_pw, miles_added, new_st, new_ef, new_pw = compute_current_ratings(
                     player.history_logs, st_rating, ef_rating, pw_rating
                 )
                 
                 # Assign updated ratings and levels to the player object
                 player.stamina_rating, player.efficiency_rating, player.power_rating = new_st, new_ef, new_pw
                 player.stamina_level, player.efficiency_level, player.power_level = post_st, post_ef, post_pw
                 
                 if player.history_logs:
                     # ─── 🏆 DYNAMIC BATCH REWARDS PROFILER ───
                     for entry in player.history_logs[-len(staged_sessions):]:
                         discovered_patches = check_single_run_patches(entry.copy())
                         entry["earned_patches"] = list(discovered_patches) if isinstance(discovered_patches, list) else discovered_patches
                         
                         emoji_strip = "".join([p.get("icon", "") for p in discovered_patches if p.get("icon")])
                         if emoji_strip and "🎖️ Rewards:" not in entry.get("text_payload", ""):
                             entry["text_payload"] = entry.get("text_payload", "").strip() + f" | 🎖️ Rewards: {emoji_strip}"

                         for patch in discovered_patches:
                             if patch["id"] not in player.unlocked_badges:
                                 player.unlocked_badges.append(patch["id"])
                 
                 # Commit save structures to disk
                 save_data = player.to_dict() if hasattr(player, 'to_dict') else dict(player.__dict__)
                 save_data['calorie_bank_balance'] = player.calorie_bank_balance
                 save_data['calorie_bank_total_earned'] = player.calorie_bank_total_earned
                 save_data['pantry_purchase_counts'] = player.pantry_purchase_counts
                 save_data['pantry_single_trophies'] = player.pantry_single_trophies
                 save_data['pantry_cuisine_trophies'] = player.pantry_cuisine_trophies
                 
                 with open(FILE_PATH, 'w', encoding='utf-8') as db_file:
                     json.dump(save_data, db_file, default=str, indent=4)
                 
                 if player.history_logs:
                     process_and_award_metrics(player.history_logs[-1])
                 
                 with open(FILE_PATH, 'r', encoding='utf-8') as db_file:
                     fresh_disk_data = json.load(db_file)
                     
                 player.history_logs = fresh_disk_data.get("history_logs", [])
                 player.unlocked_badges = fresh_disk_data.get("unlocked_badges", [])
                 if hasattr(player, 'final_metric_data'):
                     player.final_metric_data = fresh_disk_data.get("final_metric_data", {})
                 
                 post_upload_badges = fresh_disk_data.get("unlocked_badges", [])
                 st.session_state.last_sync_deltas = {
                     "gold": total_gold_rewarded,
                     "xp": total_xp_gained,  
                     "count": len(staged_sessions),
                     "miles_added": sum(float(s['dist']) for s in staged_sessions),
                     "batch_patches_earned": max(0, len(post_upload_badges) - pre_upload_badge_count)  
                 }
                 
                 if total_calories_ingested > 0:
                     st.toast(f"🔥 CALORIE BANK DEPOSIT SUCCESSFUL: +{total_calories_ingested} kcal credited!", icon="🏦")

                 st.cache_data.clear()
                 st.session_state.uploader_reset_token += 1
                 st.balloons()
                 st.rerun()
                 
             except Exception as e:
                 st.error(f"Save batch error: {str(e)}")

    if "last_sync_deltas" in st.session_state:
        dt = st.session_state.last_sync_deltas
        st.markdown("")
        with st.container(border=True):
            st.markdown("### 📊 WORKOUT COMMIT PERFORMANCE REPORT")
            st.caption(f"Successfully evaluated and logged `{dt['count']}` unique track activities into your profile history:")

            unlocked_badges = getattr(player, 'unlocked_badges', [])
            total_patches_count = len(unlocked_badges)
            batch_patches_count = dt.get('batch_patches_earned', 0)

            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Gold Earned", f"+{dt['gold']}g")
            with c2: st.metric("Experience Gained", f"+{dt['xp']} XP")
            with c3: st.metric("Distance Added", f"+{dt['miles_added']:.1f} Mi")
            with c4: st.metric(
                label="Rewards Unlocked", 
                value=f"+{batch_patches_count} New", 
                delta=f"{total_patches_count} Career Total"
            )

            if batch_patches_count > 0 and unlocked_badges:
                st.markdown("---")
                st.markdown("#### 🎖️ NEW UNLOCKED PERFORMANCE REWARDS")
                
                recent_badge_ids = []
                if hasattr(player, 'history_logs') and player.history_logs:
                    staged_count = st.session_state.last_sync_deltas.get("count", 1)
                    for entry in player.history_logs[-staged_count:]:
                        earned_list = entry.get("earned_patches", [])
                        for patch in earned_list:
                            if isinstance(patch, dict) and "id" in patch:
                                recent_badge_ids.append(patch["id"])
                            elif isinstance(patch, str):
                                recent_badge_ids.append(patch)
                
                if not recent_badge_ids:
                    recent_badge_ids = unlocked_badges[-batch_patches_count:]
                
                from collections import Counter
                badge_counts = Counter(recent_badge_ids)
                
                config_patch_map = {}
                single_run_patches = FINAL_METRIC_CONFIG.get("single_run_patches", {})
                
                for pillar, content in single_run_patches.items():
                    for tier in content.get("tiers", []):
                        config_patch_map[tier["id"]] = {
                            "name": tier["name"],
                            "icon": tier["icon"]
                        }

                unique_badge_ids = list(badge_counts.keys())
                patch_cols = st.columns(max(1, len(unique_badge_ids)))
                
                for idx, b_id in enumerate(unique_badge_ids):
                    count_val = badge_counts[b_id]
                    meta = config_patch_map.get(b_id, {"name": b_id.replace('_', ' ').title(), "icon": "🎖️"})
                    name = meta["name"]
                    icon = meta["icon"]
                    
                    if count_val > 1:
                        display_text = f"{icon} {name} **x {count_val}**"
                    else:
                        display_text = f"{icon} {name}"
                        
                    with patch_cols[idx]:
                        st.success(display_text)

            st.markdown("---")
            if st.button("❌ Close Telemetry Report", key="clear_telemetry_report_btn"):
                del st.session_state.last_sync_deltas
                st.rerun()

    st.markdown('---')
    st.markdown('### 📜 Activity Processing Backlog History')
    historical_logs = getattr(player, 'history_logs', [])
    if historical_logs:
        for log in reversed(historical_logs[-15:]):
            if isinstance(log, dict) and "text_payload" in log:
                st.text(log["text_payload"])
            else:
                st.text(str(log))
    else:
        st.info('No recorded activity logs found inside save database memory.')

# ==============================================================================
# 🎨 PART 3: ARITHMETIC PERFORMANCE EVALUATION UTILITIES
# ==============================================================================

def pace_to_seconds(pace_str: str) -> int:
    """Converts a pace string 'MM:SS' into total raw seconds."""
    try:
        parts = pace_str.strip().split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        return 0
    except (ValueError, AttributeError):
        return 0

def calculate_split_variance(splits_list: List[str], total_distance: float) -> float:
    """
    Drops the first split (warm-up mile) and calculates the delta 
    between the slowest and fastest remaining miles.
    """
    if total_distance < 3.0 or len(splits_list) < 3:
        return -1.0
        
    remaining_splits = splits_list[1:]
    splits_in_seconds = [pace_to_seconds(s) for s in remaining_splits if pace_to_seconds(s) > 0]
    
    if not splits_in_seconds:
        return -1.0
        
    variance_seconds = max(splits_in_seconds) - min(splits_in_seconds)
    return float(variance_seconds)

def calculate_final_kick(avg_pace_str: str, final_mile_str: str) -> float:
    """
    Calculates what percentage faster the final mile was compared to the average pace.
    """
    avg_seconds = pace_to_seconds(avg_pace_str)
    final_seconds = pace_to_seconds(final_mile_str)
    
    if avg_seconds <= 0 or final_seconds <= 0:
        return 0.0
        
    delta = avg_seconds - final_seconds
    kick_percent = (delta / avg_seconds) * 100.0
    return round(kick_percent, 2)

def check_single_run_patches(new_run_log: dict) -> list:
    """
    Evaluates a single run's data payload against all single_run_patches 
    defined in metrics_config.py. Returns a list of earned patch dictionaries.
    """          
    earned_patches = []
    run_distance = float(new_run_log.get("Distance (Miles)", new_run_log.get("dist", 0.0)))
    raw_ele_val = new_run_log.get("Elevation (ft)", new_run_log.get("ele", new_run_log.get("Elevation", "0")))
    run_elevation = clean_elevation_string(str(raw_ele_val))
    raw_pace_val = new_run_log.get("pace", 0.0)
    # Initialize baseline defaults
    run_pace_seconds = 0
    avg_pace_str = "00:00"
    if raw_pace_val and raw_pace_val != "00:00":
        if isinstance(raw_pace_val, str) and ":" in raw_pace_val:
            try:
                # Cleanly decode the "MM:SS" clock string back into integer components
                parts = raw_pace_val.strip().split(":")
                avg_min = int(parts[0])
                avg_sec = int(parts[1])
                # Compute total duration in seconds for badge criteria limits
                run_pace_seconds = (avg_min * 60) + avg_sec
                avg_pace_str = f"{avg_min}:{avg_sec:02d}"
            except (ValueError, TypeError, IndexError):    
                run_pace_seconds = 660  # 11:00 min/mi backup baseline
                avg_pace_str = "11:00"
        else:
            try:     
                # Secure fallback processing if pace is passed down as a raw numeric float
                pace_float = float(raw_pace_val)
                if not math.isnan(pace_float) and pace_float > 0:
                    avg_min = int(pace_float)
                    avg_sec = int(round((pace_float - avg_min) * 60))
                    if avg_sec >= 60:
                        avg_min += 1
                        avg_sec = 0
                    run_pace_seconds = (avg_min * 60) + avg_sec
                    avg_pace_str = f"{avg_min}:{avg_sec:02d}"
            except (ValueError, TypeError):
                run_pace_seconds = 660
                avg_pace_str = "11:00"
    raw_splits_array = new_run_log.get("splits", [])
    if isinstance(raw_splits_array, list):
        pace_splits_list = [item.get("pace", "") for item in raw_splits_array if isinstance(item, dict) and "pace" in item]
    else:
        pace_splits_list = []
        
    final_mile_str = pace_splits_list[-1] if pace_splits_list else ""
    
    if run_pace_seconds and final_mile_str:
        final_kick_percent = calculate_final_kick(avg_pace_str, final_mile_str)
    else:
        final_kick_percent = 0.0
    split_variance = calculate_split_variance(pace_splits_list, run_distance) if pace_splits_list else 0.0
    compiled_run_metrics = {
        "average_pace_seconds": run_pace_seconds,
        "total_elevation_gain_ft": run_elevation,
        "final_mile_kick_percent": final_kick_percent,
        "total_distance_miles": run_distance,
        "split_variance_seconds": split_variance,
        "aerobic_decoupling_percent": float(new_run_log.get("aerobic_decoupling_percent", 0.0)),
        "ambient_temp_f": float(new_run_log.get("ambient_temp_f", 72.0)),
        "zone_1_2_duration_percent": float(new_run_log.get("zone_1_2_duration_percent", 50.0))
    }

    for pillar_id, config in FINAL_METRIC_CONFIG["single_run_patches"].items():
        m_key = config["metric_key"]
        val = compiled_run_metrics.get(m_key)
        
        if val is None or val == -1.0:
            continue
            
        if "requires_min_distance" in config and run_distance < config["requires_min_distance"]:
            continue
            
        for tier in config["tiers"]:
            if "min_val" not in tier or "max_val" not in tier:
                continue
            min_bound = float(tier["min_val"])
            max_bound = float(tier["max_val"])
            
            if config.get("is_inverted"):
                if min_bound <= val <= max_bound:
                    earned_patches.append({
                        "pillar": pillar_id, "id": tier["id"], "name": tier["name"], "icon": tier["icon"]
                    })
                    break  
            else:
                if min_bound <= val <= max_bound:
                    earned_patches.append({
                        "pillar": pillar_id, "id": tier["id"], "name": tier["name"], "icon": tier["icon"]
                    })
                    break
    return earned_patches

def process_and_award_metrics(new_run_log: dict):
    """
    Main evaluation pipeline. Processes incoming run payloads, updates 
    profile statistics counters, awards single-run patches, and appends earned trophies.
    """
    SAVE_FILE = "save_file.json"
    
    if not os.path.exists(SAVE_FILE):
        print(f"Error: {SAVE_FILE} not found during metric integration.")
        return
        
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        profile = json.load(f)
        
    if "final_metric_data" not in profile:
        print("Warning: final_metric_data container missing from save file.")
        return
        
    m_data = profile["final_metric_data"]
    
    run_distance = float(new_run_log.get("Distance (Miles)", 0.0))
    # --- FIX: SAFELY RESOLVE CLOCK STRINGS OR FLOATS INTO TOTAL SECONDS ---
    raw_pace = new_run_log.get("pace", 0.0)
    if isinstance(raw_pace, str) and ":" in raw_pace:
        try:
            parts = raw_pace.strip().split(":")
            run_pace_seconds = (int(parts[0]) * 60) + int(parts[1])
        except (ValueError, IndexError):
            run_pace_seconds = 660  # Safe 11:00 min/mi fallback
    else:
        try:
            run_pace_seconds = decimal_pace_to_seconds(float(raw_pace))
        except (ValueError, TypeError):
            run_pace_seconds = 660
    run_elevation = clean_elevation_string(str(new_run_log.get("Elevation (ft)", "0")))
    
    run_patches = check_single_run_patches(new_run_log.copy())
    new_run_log["earned_patches"] = list(run_patches) if isinstance(run_patches, list) else run_patches
    
    for patch in run_patches:
        if patch["id"] not in profile["unlocked_badges"]:
            profile["unlocked_badges"].append(patch["id"])

    if "history_logs" not in profile:
        profile["history_logs"] = []
        
    is_duplicate = any(
        run.get("Date") == new_run_log.get("Date") and 
        abs(float(run.get("Distance (Miles)", 0.0)) - run_distance) < 0.01
        for run in profile["history_logs"] if isinstance(run, dict)
    )
    
    if not is_duplicate:
        profile["history_logs"].append(new_run_log)
    
    m_data["lifetime_odometer_miles"] = round(m_data["lifetime_odometer_miles"] + run_distance, 2)
    
    run_calories = int(run_distance * 100) 
    m_data["lifetime_calories_burned"] += run_calories
    profile["lifetime_elevation_gain"] = float(profile.get("lifetime_elevation_gain", 0.0)) + run_elevation
    
    # Shelf A: Mileage
    mileage_config = FINAL_METRIC_CONFIG["trophy_cabinet"]["shelf_a_mileage"]
    for trophy in mileage_config["trophies"]:
        if m_data["lifetime_odometer_miles"] >= trophy["threshold"] and trophy["id"] not in m_data["trophy_cabinet"]["shelf_a_mileage"]:
            m_data["trophy_cabinet"]["shelf_a_mileage"].append(trophy["id"])
            
    # Shelf B: Elevation
    elev_config = FINAL_METRIC_CONFIG["trophy_cabinet"]["shelf_b_elevation"]
    for trophy in elev_config["trophies"]:
        if profile["lifetime_elevation_gain"] >= trophy["threshold"] and trophy["id"] not in m_data["trophy_cabinet"]["shelf_b_elevation"]:
            m_data["trophy_cabinet"]["shelf_b_elevation"].append(trophy["id"])
            
    # Shelf C: Calories
    cal_config = FINAL_METRIC_CONFIG["trophy_cabinet"]["shelf_c_calories"]
    for trophy in cal_config["trophies"]:
        if m_data["lifetime_calories_burned"] >= trophy["threshold"] and trophy["id"] not in m_data["trophy_cabinet"]["shelf_c_calories"]:
            m_data["trophy_cabinet"]["shelf_c_calories"].append(trophy["id"])

    if m_data["lifetime_odometer_miles"] > 2000:
        extra_miles = m_data["lifetime_odometer_miles"] - 2000
        m_data["trophy_cabinet"]["prestige_loops"]["mileage_loops_count"] = int(extra_miles // mileage_config["loop_increment"])
        
    if profile["lifetime_elevation_gain"] > 100000:
        extra_vert = profile["lifetime_elevation_gain"] - 100000
        m_data["trophy_cabinet"]["prestige_loops"]["elevation_loops_count"] = int(extra_vert // elev_config["loop_increment"])

    if m_data["lifetime_calories_burned"] > 100000:
        extra_cal = m_data["lifetime_calories_burned"] - 100000
        m_data["trophy_cabinet"]["prestige_loops"]["calorie_loops_count"] = int(extra_cal // cal_config["loop_increment"])

    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=4, ensure_ascii=False)


def decimal_pace_to_seconds(decimal_pace: float) -> int:
    """Converts a decimal pace float (like 8.82) into raw total seconds."""
    try:
        minutes = int(decimal_pace)
        seconds = int(round((decimal_pace - minutes) * 60))
        return (minutes * 60) + seconds
    except (ValueError, TypeError):
        return 0

def clean_elevation_string(elev_str: str) -> int:
    """Strips formatting symbols '+', 'ft', and whitespace to return a clean integer."""
    try:
        cleaned = elev_str.replace("+", "").replace("ft", "").strip()
        return int(float(cleaned))
    except (ValueError, AttributeError):
        return 0


# =========================================================================
# 🎛️ HEART RATE ZONE STYLING UTILITY
# =========================================================================

def get_hr_zone_style(avg_hr: int) -> tuple:
    """
    Determines the background color, zone label, and text contrast color 
    based on traditional running intensity heart rate zones.
    """
    if not avg_hr or avg_hr <= 0:
        return "#4A5568", "No Data", "#FFFFFF"
        
    # Standard zones based on typical performance athlete thresholds (e.g., Max HR ~190)
    if avg_hr < 115:
        return "#A0AEC0", "Zone 1 (Recovery)", "#1A202C"
    elif avg_hr < 135:
        return "#38A169", "Zone 2 (Aerobic)", "#FFFFFF"
    elif avg_hr < 155:
        return "#ECC94B", "Zone 3 (Tempo)", "#1A202C"
    elif avg_hr < 175:
        return "#ED8936", "Zone 4 (Threshold)", "#FFFFFF"
    else:
        return "#E53E3E", "Zone 5 (Anaerobic)", "#FFFFFF"

# =========================================================================
# ⚙️ SAFETY TELEMETRY CONVERTERS
# =========================================================================

def safe_pace_to_decimal(pace_val) -> float:
    """Converts either a clock string 'MM:SS' or a float into a decimal minute float."""
    if isinstance(pace_val, (int, float)):
        return float(pace_val)
    try:
        if isinstance(pace_val, str) and ":" in pace_val:
            parts = pace_val.strip().split(":")
            minutes = int(parts[0])
            seconds = int(parts[1])
            return float(minutes + (seconds / 60.0))
        return float(pace_val)
    except (ValueError, TypeError, IndexError):
        return 11.0 # Safe baseline fallback pace
