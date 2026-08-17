# -*- coding: utf-8 -*-
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



import re
import math

def compute_current_ratings(logs_array, current_fuel_rating=100, current_nitro_rating=100, current_torque_rating=100):
    """
    Calculates dynamic upward and downward level trends based on comparative 
    performance intensity rather than strict calendar date expiration gates.
    """
    # Baseline expected targets per current level ranking tier
    fuel_level = max(1, min(9, int(current_fuel_rating / 100) + 1))
    nitro_level = max(1, min(9, int(current_nitro_rating / 100) + 1))
    torque_level = max(1, min(9, int(current_torque_rating / 100) + 1))
    
    # Calculate baseline expectations based on current tier ranks
    expected_distance = fuel_level * 2.0     # Level 3 expects 6 miles
    expected_pace = 11.0 - (nitro_level * 0.5) # Level 6 expects an 8:00 min/mi pace
    expected_elevation = torque_level * 150.0  # Level 4 expects 600 ft of climbing
    
    total_rolling_miles = 0.0
    
    # Process only the single incoming run batch to calculate trend deltas
    for entry in logs_array[-1:]:  # Focus strictly on processing the latest ingestion log
        if isinstance(entry, dict):
            dist = float(entry.get("Distance (Miles)", entry.get("dist", 0.0)))
            pace = float(entry.get("pace", 0.0))
            
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

        # 🔋 1. ENDURANCE TREND (FUEL)
        dist_delta = dist - expected_distance
        if dist_delta >= 0:
            # Upward Trend: Earn more points for pushing past your current target
            current_fuel_rating += int(dist_delta * 15) + 10
        else:
            # Downward Trend: Lose rating points if the run was shorter than expected
            current_fuel_rating += int(dist_delta * 8) - 5

        # ⚡ 2. SPEED TREND (NITRO)
        if pace > 3.0:
            pace_delta = expected_pace - pace # Positive means you ran faster than expected
            if pace_delta >= 0:
                # Upward Trend
                current_nitro_rating += int(pace_delta * 40) + 12
            else:
                # Downward Trend
                current_nitro_rating += int(pace_delta * 20) - 8

        # 🏔️ 3. ELEVATION TREND (TORQUE)
        ele_delta = ele - expected_elevation
        if ele_delta >= 0:
            # Upward Trend
            current_torque_rating += int(ele_delta * 0.15) + 10
        else:
            # Downward Trend
            current_torque_rating += int(ele_delta * 0.08) - 5

    # Enforce minimum boundaries and maximum caps [Level 1 to Level 9]
    current_fuel_rating = max(0, min(899, current_fuel_rating))
    current_nitro_rating = max(0, min(899, current_nitro_rating))
    current_torque_rating = max(0, min(899, current_torque_rating))

    # Recalculate level outputs dynamically from the updated rating numbers
    final_fuel_lvl = int(current_fuel_rating / 100) + 1
    final_nitro_lvl = int(current_nitro_rating / 100) + 1
    final_torque_lvl = int(current_torque_rating / 100) + 1

    return final_fuel_lvl, final_nitro_lvl, final_torque_lvl, total_rolling_miles, current_fuel_rating, current_nitro_rating, current_torque_rating






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
                    chk_date = fit_metrics_temp.get("date", chk_date)
                    calculated_distance_miles = fit_metrics_temp["distance_km"] * 0.621371
                    chk_dist = round(calculated_distance_miles, 2)
                    
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
                        h_date = str(log_row.get("Date", log_row.get("Activity Date", "")))[:10]
                        h_dist = round(float(log_row.get("Distance (Miles)", log_row.get("dist", 0.0))), 2)
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
                        calculated_distance_miles = fit_metrics_temp["distance_km"] * 0.621371
                        t_secs = int(fit_metrics_temp.get("duration_seconds", 0))
                        chk_dur = f"{t_secs // 3600:02d}:{(t_secs % 3600) // 60:02d}:{t_secs % 60:02d}"
                    
                    total_secs = int(fit_metrics_temp["duration_seconds"])
                    if calculated_distance_miles > 0 and total_secs > 0:
                        total_minutes = total_secs / 60.0
                        calculated_pace = total_minutes / calculated_distance_miles
                    else:
                        calculated_pace = 0.0
                    
                    staged_sessions.append({
                        "name": file_obj.name, "date": fit_metrics_temp["date"],  
                        "dist": round(calculated_distance_miles, 2), "duration": chk_dur,  
                        "pace": calculated_pace, "ele": fit_metrics_temp["elevation_gain_ft"], 
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
                    st.markdown(f"📄 **{s['name']}** — `[{s['date']}]` — `{s['dist']:.2f} Mi` | Running Time: `{s['duration']}` | `{s['pace']:.2f} min/mi` Pace | `+{s['ele']} ft` Climbing")
                    
                    if "splits" in s and s["splits"] is not None and len(s["splits"]) > 0:
                        with st.expander("⏱️ View Mile Splits Breakdown"):
                            df_splits = pd.DataFrame(s["splits"])
                            df_splits.columns = ["Split #", "Distance (Mi)", "Split Time", "Pace (/mi)"]
                            st.dataframe(df_splits, use_container_width=True, hide_index=True)
        
        st.markdown('')



        if staged_sessions and st.button("🟢 Commit All Staged Tracks to Save Profile", key='commit_bulk_gpx_telemetry_btn'):
             try:
                 if not hasattr(player, 'history_logs'):
                     player.history_logs = []
                 if not hasattr(player, 'unlocked_badges'):
                     player.unlocked_badges = []
    
                 # 1. Take a baseline snapshot of your career badges before running calculations
                 pre_upload_badge_count = len(player.unlocked_badges)
                 
                 total_gold_rewarded, total_xp_gained = 0, 0
                 for s in staged_sessions:
                     z1, z2, z3, z4, z5 = 15, 45, 20, 15, 5 
                     gold = max(2, int(float(s['dist']) * 10))
                     xp = max(5, int(float(s['dist']) * 50))
                     total_gold_rewarded += gold
                     total_xp_gained += xp
         
                     raw_s_pace = s.get('pace', 0.0)
                     if raw_s_pace is None or (isinstance(raw_s_pace, float) and (math.isnan(raw_s_pace) or raw_s_pace <= 0)):
                         clean_pace_val = 0.0
                         pace_text = "—"
                     else:
                         clean_pace_val = float(raw_s_pace)
                         pace_text = f"{clean_pace_val:.2f}"

                     # FIXED: Added explicit labels so the regex text parser can read elevation metrics safely
                     text_sentence = f"[{s['date']}] Run: {s['dist']:.2f} miles | Pace: {pace_text} min/mi | Elevation Climbed: +{s.get('ele', 0)} ft | [REWARD] +{gold}g, +{xp} XP."
                     
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
         
                 # Update core profile character values
                 player.gold = getattr(player, 'gold', 50) + total_gold_rewarded
                 player.total_xp = getattr(player, 'total_xp', 0) + total_xp_gained
                 
                 # 2. EXTRACT OR SAFE-INITIALIZE TREND SKILL RATINGS
                 f_rating = getattr(player, 'fuel_rating', 100)
                 n_rating = getattr(player, 'nitro_rating', 100)
                 t_rating = getattr(player, 'torque_rating', 100)

                 # Run the rating trend calculator engine
                 post_f, post_n, post_t, miles_added, new_f, new_n, new_t = compute_current_ratings(
                     player.history_logs, f_rating, n_rating, t_rating
                 )
                 
                 # Assign updated ratings and levels to the player object
                 player.fuel_rating, player.nitro_rating, player.torque_rating = new_f, new_n, new_t
                 player.fuel_level, player.nitro_level, player.torque_level = post_f, post_n, post_t
                 
                 # Run calculations in memory before disk writes to bypass duplication lockout filters
                 if player.history_logs:
                     # ─── 🏆 DYNAMIC BATCH PROFILER BLOCK ───
                     for entry in player.history_logs[-len(staged_sessions):]:
                         discovered_patches = check_single_run_patches(entry.copy())
                         entry["earned_patches"] = list(discovered_patches) if isinstance(discovered_patches, list) else discovered_patches
                         
                         for patch in discovered_patches:
                             if patch["id"] not in player.unlocked_badges:
                                 player.unlocked_badges.append(patch["id"])
                 
                 # Commit fully stamped memory structures to disk
                 save_data = player.to_dict() if hasattr(player, 'to_dict') else player.__dict__
                 with open(FILE_PATH, 'w', encoding='utf-8') as db_file:
                     json.dump(save_data, db_file, default=str, indent=4)
                 
                 # Run legacy background engines to refresh lifelong odometers and trophy shelves
                 if player.history_logs:
                     process_and_award_metrics(player.history_logs[-1])
                 
                 # Re-sync memory tracking objects from disk
                 with open(FILE_PATH, 'r', encoding='utf-8') as db_file:
                     fresh_disk_data = json.load(db_file)
                     
                 player.history_logs = fresh_disk_data.get("history_logs", [])
                 player.unlocked_badges = fresh_disk_data.get("unlocked_badges", [])
                 if hasattr(player, 'final_metric_data'):
                     player.final_metric_data = fresh_disk_data.get("final_metric_data", {})
                 
                 # Calculate accurate badge deltas to display in the Streamlit interface panel
                 post_upload_badges = fresh_disk_data.get("unlocked_badges", [])
                 st.session_state.last_sync_deltas = {
                     "gold": total_gold_rewarded,
                     "xp": total_xp_gained,  
                     "count": len(staged_sessions),
                     "miles_added": sum(float(s['dist']) for s in staged_sessions),
                     "batch_patches_earned": max(0, len(post_upload_badges) - pre_upload_badge_count)  
                 }

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

            # Read career accomplishments directly from live memory metrics lists
            unlocked_badges = getattr(player, 'unlocked_badges', [])
            total_patches_count = len(unlocked_badges)
            batch_patches_count = dt.get('batch_patches_earned', 0)

            # 4-Column Summary Layout Grid
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.metric("Gold Earned", f"+{dt['gold']}g")
            with c2: st.metric("Experience Gained", f"+{dt['xp']} XP")
            with c3: st.metric("Distance Added", f"+{dt['miles_added']:.1f} Mi")
            with c4: st.metric(
                label="Patches Earned", 
                value=f"+{batch_patches_count} New", 
                delta=f"{total_patches_count} Career Total"
            )

            # --- RENDER NEWLY EARNED PATCHES WITH MULTIPLIERS FROM CURRENT UPLOAD ---
            if batch_patches_count > 0 and unlocked_badges:
                st.markdown("---")
                st.markdown("#### 🎖️ NEW UNLOCKED PERFORMANCE PATCHES")
                
                # 1. Slice the last N items added to the career list during this specific upload
                recent_badge_ids = unlocked_badges[-batch_patches_count:]
                
                # 2. Count occurrences of each badge ID in the current upload batch
                from collections import Counter
                badge_counts = Counter(recent_badge_ids)
                
                # 3. Create a dictionary map from metrics_config to extract the real names and icons
                config_patch_map = {}
                single_run_patches = FINAL_METRIC_CONFIG.get("single_run_patches", {})
                
                for pillar, content in single_run_patches.items():
                    for tier in content.get("tiers", []):
                        config_patch_map[tier["id"]] = {
                            "name": tier["name"],
                            "icon": tier["icon"]
                        }

                # 4. Render clean layout columns based on unique grouped tiers count
                unique_badge_ids = list(badge_counts.keys())
                patch_cols = st.columns(max(1, len(unique_badge_ids)))
                
                for idx, b_id in enumerate(unique_badge_ids):
                    count_val = badge_counts[b_id]
                    
                    # Fetch metadata from configuration dictionary, or fallback gracefully if not found
                    meta = config_patch_map.get(b_id, {"name": b_id.replace('_', ' ').title(), "icon": "🎖️"})
                    name = meta["name"]
                    icon = meta["icon"]
                    
                    # Append multiplier suffix to string format if more than one was earned
                    if count_val > 1:
                        display_text = f"{icon} {name} **x {count_val}**"
                    else:
                        display_text = f"{icon} {name}"
                        
                    with patch_cols[idx]:
                        st.success(display_text)

            # Manual report dismiss action layout row
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
    Returns variance in seconds, or -1.0 if ineligible.
    """
    # Rule validation: Must be at least 3 miles and have matching splits data
    if total_distance < 3.0 or len(splits_list) < 3:
        return -1.0
        
    # Surgical removal of the first warm-up mile split
    remaining_splits = splits_list[1:]
    
    # Convert all remaining splits to seconds for precise arithmetic
    splits_in_seconds = [pace_to_seconds(s) for s in remaining_splits if pace_to_seconds(s) > 0]
    
    if not splits_in_seconds:
        return -1.0
        
    # Calculate absolute delta between the slowest (max seconds) and fastest (min seconds)
    variance_seconds = max(splits_in_seconds) - min(splits_in_seconds)
    return float(variance_seconds)
def calculate_final_kick(avg_pace_str: str, final_mile_str: str) -> float:
    """
    Calculates what percentage faster the final mile was compared to the average pace.
    Formula: (Avg Pace Seconds - Final Mile Seconds) / Avg Pace Seconds * 100
    """
    avg_seconds = pace_to_seconds(avg_pace_str)
    final_seconds = pace_to_seconds(final_mile_str)
    
    if avg_seconds <= 0 or final_seconds <= 0:
        return 0.0
        
    # If final mile is slower than average, percentage is <= 0 (no patch earned)
    delta = avg_seconds - final_seconds
    kick_percent = (delta / avg_seconds) * 100.0
    return round(kick_percent, 2)




def check_single_run_patches(new_run_log: dict) -> list:
    """
    Evaluates a single run's data payload against all 8 single_run_patches 
    defined in metrics_config.py. Returns a list of earned patch dictionaries.
    """          
    earned_patches = []
    import math
                 
    # 1. Check all potential key variations for distance and elevation safely
    run_distance = float(new_run_log.get("Distance (Miles)", new_run_log.get("dist", 0.0)))
    raw_ele_val = new_run_log.get("Elevation (ft)", new_run_log.get("ele", new_run_log.get("Elevation", "0")))
    run_elevation = clean_elevation_string(str(raw_ele_val))

    # 2. Safe conversion handling for plain decimal floats (e.g., 8.45 -> 8 min 45 sec)
    raw_pace_val = new_run_log.get("pace", 0.0)
    if raw_pace_val is None or (isinstance(raw_pace_val, float) and (math.isnan(raw_pace_val) or raw_pace_val <= 0)):
        run_pace_seconds = None
        avg_pace_str = "00:00"
    else:            
        pace_float = float(raw_pace_val)
        avg_min = int(pace_float)
        avg_sec = int(round((pace_float - avg_min) * 100))
        if avg_sec >= 60:
            avg_sec = min(59, avg_sec)
            
        run_pace_seconds = (avg_min * 60) + avg_sec
        avg_pace_str = f"{avg_min:02d}:{avg_sec:02d}"

    # 3. Parse splits arrays and structure variables
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
            
    # 4. Map calculated numbers to match config keys exactly
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

    # 5. Dynamic loop through configuration file rules
    for pillar_id, config in FINAL_METRIC_CONFIG["single_run_patches"].items():
        m_key = config["metric_key"]
        val = compiled_run_metrics.get(m_key)
        
        # Skip if missing valid telemetry numbers
        if val is None or val == -1.0:
            continue
            
        # Enforce minimum distance rules
        if "requires_min_distance" in config and run_distance < config["requires_min_distance"]:
            continue
            
        # Evaluate tier bounds based on inversion properties
        for tier in config["tiers"]:
            # FIXED: Added fallback protection to prevent KeyError crashes on special non-bounded tiers
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
def check_single_run_patches(new_run_log: dict) -> list:
    """
    Evaluates a single run's data payload against all 8 single_run_patches 
    defined in metrics_config.py. Returns a list of earned patch dictionaries.
    """          
    earned_patches = []
    import math
                 
    # 1. Check all potential key variations for distance and elevation safely
    run_distance = float(new_run_log.get("Distance (Miles)", new_run_log.get("dist", 0.0)))
    raw_ele_val = new_run_log.get("Elevation (ft)", new_run_log.get("ele", new_run_log.get("Elevation", "0")))
    run_elevation = clean_elevation_string(str(raw_ele_val))

    # 2. Safe conversion handling for plain decimal floats (e.g., 8.45 -> 8 min 45 sec)
    raw_pace_val = new_run_log.get("pace", 0.0)
    if raw_pace_val is None or (isinstance(raw_pace_val, float) and (math.isnan(raw_pace_val) or raw_pace_val <= 0)):
        run_pace_seconds = None
        avg_pace_str = "00:00"
    else:            
        pace_float = float(raw_pace_val)
        avg_min = int(pace_float)
        avg_sec = int(round((pace_float - avg_min) * 100))
        if avg_sec >= 60:
            avg_sec = min(59, avg_sec)
            
        run_pace_seconds = (avg_min * 60) + avg_sec
        avg_pace_str = f"{avg_min:02d}:{avg_sec:02d}"

    # 3. Parse splits arrays and structure variables
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
            
    # 4. Map calculated numbers to match config keys exactly
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

    # 5. Dynamic loop through configuration file rules
    for pillar_id, config in FINAL_METRIC_CONFIG["single_run_patches"].items():
        m_key = config["metric_key"]
        val = compiled_run_metrics.get(m_key)
        
        # Skip if missing valid telemetry numbers
        if val is None or val == -1.0:
            continue
            
        # Enforce minimum distance rules
        if "requires_min_distance" in config and run_distance < config["requires_min_distance"]:
            continue
            
        # Evaluate tier bounds based on inversion properties
        for tier in config["tiers"]:
            # FIXED: Added fallback protection to prevent KeyError crashes on special non-bounded tiers
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
        
    # 1. Read your existing profile data safely
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        profile = json.load(f)
        
    # Safeguard initialization if user hasn't run the migration snippet yet
    if "final_metric_data" not in profile:
        print("Warning: final_metric_data container missing from save file. Run initializer.")
        return
        
    m_data = profile["final_metric_data"]
    
    # --- A. DATA CONVERSION EXTRACTORS ---
    run_distance = float(new_run_log.get("Distance (Miles)", 0.0))
    run_pace_seconds = decimal_pace_to_seconds(new_run_log.get("pace", 0.0))
    run_elevation = clean_elevation_string(new_run_log.get("Elevation (ft)", "0"))
    
    # --- B. EXECUTE THE SINGLE-RUN PATCH ROUTINE (INTEGRATED HERE) ---
    run_patches = check_single_run_patches(new_run_log.copy())
    
    # Attach the badges permanently inside the individual workout log dictionary object
    new_run_log["earned_patches"] = list(run_patches) if isinstance(run_patches, list) else run_patches
    
    # Also push any unique patches to your permanent top-level unlocked list
    for patch in run_patches:
        if patch["id"] not in profile["unlocked_badges"]:
            profile["unlocked_badges"].append(patch["id"])

    # =========================================================================
    # 💥 CRITICAL FIX: APPEND RUN TO CALENDAR ARRAY LIST IF NOT PRESENT 💥
    # =========================================================================
    if "history_logs" not in profile:
        profile["history_logs"] = []
        
    # Cross-check date and distance to prevent adding duplicate rows
    is_duplicate = any(
        run.get("Date") == new_run_log.get("Date") and 
        abs(float(run.get("Distance (Miles)", 0.0)) - run_distance) < 0.01
        for run in profile["history_logs"] if isinstance(run, dict)
    )
    
    if not is_duplicate:
        profile["history_logs"].append(new_run_log)
    else:
        print(f"ℹ️ Duplicate Filter: Activity on {new_run_log.get('Date')} already saved in history.")
    # =========================================================================
    
    # --- C. TICK UP LIFETIME ODOMETERS & COUNTERS ---
    m_data["lifetime_odometer_miles"] = round(m_data["lifetime_odometer_miles"] + run_distance, 2)
    
    # Estimate standard average metabolic running burn of 100 kcal per mile for your logs
    run_calories = int(run_distance * 100) 
    m_data["lifetime_calories_burned"] += run_calories
    
    # Update your original game profile total elevation value to keep everything synchronized
    profile["lifetime_elevation_gain"] = float(profile.get("lifetime_elevation_gain", 0.0)) + run_elevation
    
    # --- D. EVALUATE THREE-SHELF TROPHY CABINETS ---
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

    # --- E. INFINITE PRESTIGE PROGRESSION LOOPS ---
    if m_data["lifetime_odometer_miles"] > 2000:
        extra_miles = m_data["lifetime_odometer_miles"] - 2000
        m_data["trophy_cabinet"]["prestige_loops"]["mileage_loops_count"] = int(extra_miles // mileage_config["loop_increment"])
        
    if profile["lifetime_elevation_gain"] > 100000:
        extra_vert = profile["lifetime_elevation_gain"] - 100000
        m_data["trophy_cabinet"]["prestige_loops"]["elevation_loops_count"] = int(extra_vert // elev_config["loop_increment"])

    if m_data["lifetime_calories_burned"] > 100000:
        extra_cal = m_data["lifetime_calories_burned"] - 100000
        m_data["trophy_cabinet"]["prestige_loops"]["calorie_loops_count"] = int(extra_cal // cal_config["loop_increment"])

    # --- F. WRITE EVERYTHING REFRESHED BACK TO YOUR DATABASE ---
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=4, ensure_ascii=False)
    print("Ledger Complete: Lifelong odometers, patches, and award cases refreshed successfully.")

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

