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
                now_date = datetime.now()
                three_weeks_ago = now_date - timedelta(days=21)
                
                def compute_current_ratings(logs_array):
                    t_miles, max_el, f_pace = 0.0, 0.0, 999.0
                    for entry in logs_array:
                        entry_str = str(entry)
                        if 'miles' in entry_str.lower() and 'slept' not in entry_str.lower():
                            d_m = re.search(r'(?:Run|run|ran|distance):?\s*([0-9.]+)', entry_str, re.IGNORECASE)
                            if not d_m: d_m = re.search(r'([0-9.]+)\s*(?:miles|mi)', entry_str, re.IGNORECASE)
                            p_m = re.search(r'Pace:\s*([0-9.]+)', entry_str, re.IGNORECASE)
                            e_m = re.search(r'Elevation\s*Climbed:\s*\+?([0-9.]+)', entry_str, re.IGNORECASE)
                            dt_m = re.search(r'\[([0-9-]+)\]', entry_str)
                            
                            is_in = True
                            if dt_m and datetime.strptime(dt_m.group(1)[:10], '%Y-%m-%d') < three_weeks_ago: is_in = False
                            if is_in and d_m:
                                t_miles += float(d_m.group(1))
                                if e_m: max_el = max(max_el, float(e_m.group(1)))
                                if p_m and 2.0 < float(p_m.group(1)) < f_pace: f_pace = float(p_m.group(1))
                    
                    fuel = max(1, min(9, int((t_miles / 300.0) * 9)))
                    nitro = max(1, min(9, int(9 - ((f_pace - 5.50) * 1.5)))) if 0 < f_pace < 900.0 else 1
                    torque = max(1, min(9, int((max_el / 6000.0) * 9)))
                    return fuel, nitro, torque, t_miles
                
                pre_logs = getattr(player, 'history_logs', [])
                pre_f, pre_n, pre_t, pre_miles = compute_current_ratings(pre_logs)
                
                total_gold_rewarded = 0
                total_xp_gained = 0
                if not hasattr(player, 'history_logs'): player.history_logs = []
                
                for s in staged_sessions:
                    #gold_rewarded = int(s['dist'] * 10)
                    #xp_gained = int(s['dist'] * 50)
                    #total_gold_rewarded += gold_rewarded
                    #total_xp_gained += xp_gained

                    # --- ENHANCED INGESTION ATTRIBUTE DISTRIBUTOR LOOP ---
                    total_gold_rewarded = 0
                    total_xp_gained = 0
                    
                    # Initialize missing player attributes
                    for attr in ['stamina_xp', 'agility_xp', 'power_xp']:
                        if not hasattr(player, attr): setattr(player, attr, 0)
            
                    for s in staged_sessions:
                        dist_val = float(s['dist'])
                        base_xp = int(dist_val * 10)
                        
                        # Read split variations out of raw Garmin tracks to calculate true zone times
                        s_splits = s.get('splits', [])
                        z1, z2, z3, z4, z5 = 15, 45, 20, 15, 5  # Fallback
                        
                        if isinstance(s_splits, list) and len(s_splits) > 0:
                            paces = []
                            for s_item in s_splits:
                                p_str = str(s_item.get('pace', s_item.get('Pace (/mi)', '08:00')))
                                try:
                                    parts = p_str.split(':')
                                    if len(parts) == 2: paces.append(int(parts[0])*60 + int(parts[1]))
                                except Exception: pass
                            
                            if len(paces) > 1:
                                slowest, fastest = max(paces), min(paces)
                                span = max(1, slowest - fastest)
                                rz1, rz2, rz3, rz4, rz5 = 0, 0, 0, 0, 0
                                for p in paces:
                                    rel = (slowest - p) / span
                                    if rel < 0.2: rz1 += 1
                                    elif rel < 0.5: rz2 += 1
                                    elif rel < 0.75: rz3 += 1
                                    elif rel < 0.92: rz4 += 1
                                    else: rz5 += 1
                                tot = len(paces)
                                z1, z2, z3, z4, z5 = int((rz1/tot)*100), int((rz2/tot)*100), int((rz3/tot)*100), int((rz4/tot)*100), 100-(int((rz1/tot)*100)+int((rz2/tot)*100)+int((rz3/tot)*100)+int((rz4/tot)*100))
            
                        # Distribute weights directly onto your character attributes
                        stamina_xp = max(5, int(base_xp * (z1 + z2) / 50.0)) if dist_val > 0 else 0
                        agility_xp = max(0, int(base_xp * (z3 + z4) / 50.0)) if dist_val > 0 else 0
                        power_xp = max(0, int(base_xp * (z5 * 3) / 50.0)) if dist_val > 0 else 0
                        gold_rewarded = max(2, int(dist_val * 5 + (stamina_xp + agility_xp + power_xp) * 0.1)) if dist_val > 0 else 0
                        # ==================================================================
                        # ADD THIS LINE RIGHT HERE: Sum the attributes to fix the missing variable
                        # ==================================================================
                        xp_gained = stamina_xp + agility_xp + power_xp
                        # ==================================================================

                        # Accumulate and update player stats
                        total_gold_rewarded += gold_rewarded
                        total_xp_gained += xp_gained
            
                        # Accumulate and update player stats
                        player.stamina_xp = getattr(player, 'stamina_xp', 0) + stamina_xp
                        player.agility_xp = getattr(player, 'agility_xp', 0) + agility_xp
                        player.power_xp = getattr(player, 'power_xp', 0) + power_xp
            
                        text_sentence = f"[{s['date']}] Run: {s['dist']:.2f} miles | Earned +{gold_rewarded}g | +{stamina_xp} Stamina, +{agility_xp} Agility, +{power_xp} Power XP."
            
                        # Re-index history_logs to store the new data
                        structured_log = {
                            "Date": s['date'], "Name": s.get('name', 'Run'), "Distance (Miles)": dist_val,
                            "Duration": s['duration'], "text_payload": text_sentence,
                            "z1_pct": z1, "z2_pct": z2, "z3_pct": z3, "z4_pct": z4, "z5_pct": z5
                        }
                        class LegacyStringDict(dict):
                            def __str__(self): return self["text_payload"]
                        player.history_logs.append(LegacyStringDict(structured_log))





















##########
                    
                    text_sentence = f"[{s['date']}] Run: {s['dist']:.2f} miles | Duration: {s['duration']} | Pace: {s['pace']:.2f} min/mi | Elevation Climbed: +{s['ele']} ft. [REWARD] Earned +{gold_rewarded}g and +{xp_gained} XP."
                    
                    structured_log = {
                        "Date": s['date'], "Name": s.get('name', 'Run'), "Distance (Miles)": float(s['dist']),
                        "Duration": s['duration'], "pace": float(s['pace']), "Elevation (ft)": f"+{s['ele']} ft",
                        "splits": s.get('splits', []), "text_payload": text_sentence   
                    }
                    
                    class LegacyStringDict(dict):
                        def __str__(self): return self["text_payload"]
                        def __repr__(self): return self["text_payload"]
                            
                    player.history_logs.append(LegacyStringDict(structured_log))
                
                player.gold = getattr(player, 'gold', 50) + total_gold_rewarded
                player.total_xp = getattr(player, 'total_xp', 0) + total_xp_gained
                
                save_data = player.to_dict() if hasattr(player, 'to_dict') else player.__dict__
                # 2. TRIGGER THE AUTOMATIC REWARD SYSTEM UPDATES
                # Pass the most recently added run log from your history list into the pipeline
                if "history_logs" in save_data and len(save_data["history_logs"]) > 0:
                    latest_run = save_data["history_logs"][-1]
                    
                    # This runs the math parser, awards patches, and appends the trophy cases
                    process_and_award_metrics(latest_run)
                    
                    # 3. KEEP ACTIVE VARIABLES IN SYNC
                    # Re-read the updated file structure back into your active player instance 
                    # so your live application dashboard doesn't experience state desynchronization
                    with open(FILE_PATH, 'r', encoding='utf-8') as db_file:
                        updated_profile_data = json.load(db_file)
                        
                    # Sync the live runtime object with the file's fresh calculations
                    if hasattr(player, 'final_metric_data'):
                        player.final_metric_data = updated_profile_data.get("final_metric_data", {})
                    if hasattr(player, 'unlocked_badges'):
                        player.unlocked_badges = updated_profile_data.get("unlocked_badges", [])
                    if hasattr(player, 'lifetime_elevation_gain'):
                        player.lifetime_elevation_gain = updated_profile_data.get("lifetime_elevation_gain", 0.0)
       




                with open(FILE_PATH, 'w', encoding='utf-8') as db_file:
                    json.dump(save_data, db_file, default=str, indent=4)
                
                post_f, post_n, post_t, post_miles = compute_current_ratings(player.history_logs)
                df_f, df_n, df_t, df_miles = post_f - pre_f, post_n - pre_n, post_t - pre_t, post_miles - pre_miles
                
                f_txt = f"[ {post_f} / 9 ] 📈 (+{df_f} Node Boost)" if df_f > 0 else f"[ {post_f} / 9 ] (Sustained)"
                n_txt = f"[ {post_n} / 9 ] 📈 (+{df_n} Node Boost)" if df_n > 0 else f"[ {post_n} / 9 ] (Sustained)"
                t_txt = f"[ {post_t} / 9 ] 📈 (+{df_t} Node Boost)" if df_t > 0 else f"[ {post_t} / 9 ] (Sustained)"
                
                st.session_state.last_sync_deltas = {
                    "gold": total_gold_rewarded, "xp": total_xp_gained, "count": len(staged_sessions),
                    "miles_add": round(df_miles, 1), "fuel": f_txt, "nitro": n_txt, "torque": t_txt
                }
                
                st.cache_data.clear()
                st.session_state.uploader_reset_token += 1
                st.balloons(); st.rerun()
            except Exception as e:
                st.error(f"Consolidated save batch error: {str(e)}")
    if "last_sync_deltas" in st.session_state:
        dt = st.session_state.last_sync_deltas
        st.markdown("")
        with st.container(border=True):
            st.markdown("### 📊 LIVE DRIVER UPGRADE PERFORMANCE TELEMETRY")
            st.caption(f"Successfully processed `{dt['count']}` unique track profiles into your profile account save data:")
            c1, c2, c3 = st.columns(3)
            with c1: st.metric("Currency Harvested", f"+{dt['gold']}g")
            with c2: st.metric("Experience Harvested", f"+{dt['xp']} XP")
            with c3: st.metric("3-Week Odometer Delta", f"+{dt['miles_add']} Miles")
            st.markdown("#### 🕹️ RE-CALCULATED RETRO CABINET ATTRIBUTE METERS")
            st.markdown(f"🔋 **AEROBIC CAPACITY / FUEL TANK:** {dt['fuel']}")
            st.markdown(f"⚡ **SPRINT VELOCITY / NITRO BOOST:** {dt['nitro']}")
            st.markdown(f"⛰️ **HILL FORCE / ENGINE TORQUE:** {dt['torque']}")
            st.info("⚡ *Your active floating cockpit stats header has successfully realigned to match these new machine specs!*")

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
    
    # 1. Extract values using our payload keys and conversion helpers
    # 1. Extract values using our payload keys and conversion helpers
    import math

    run_distance = float(new_run_log.get("Distance (Miles)", 0.0))
    
    # Safely handle the decimal pace value
    raw_pace_val = new_run_log.get("pace", 0.0)
    if raw_pace_val is None or (isinstance(raw_pace_val, float) and math.isnan(raw_pace_val)) or raw_pace_val <= 0:
        raw_pace_val = 0.0

    run_pace_seconds = decimal_pace_to_seconds(raw_pace_val)
    run_elevation = clean_elevation_string(new_run_log.get("Elevation (ft)", "0"))
    
    raw_splits_array = new_run_log.get("splits", [])
    pace_splits_list = [item.get("pace", "") for item in raw_splits_array if "pace" in item]
    final_mile_str = pace_splits_list[-1] if pace_splits_list else ""
    
    # FIXED: Added fallback protection before running integer truncation conversion
    if raw_pace_val > 0:
        avg_min = int(raw_pace_val)
        avg_sec = int(round((raw_pace_val - avg_min) * 60))
        if avg_sec == 60:
            avg_min += 1
            avg_sec = 0
    else:
        avg_min, avg_sec = 0, 0
        
    avg_pace_str = f"{avg_min:02d}:{avg_sec:02d}"
    
    final_kick_percent = calculate_final_kick(avg_pace_str, final_mile_str)
    split_variance = calculate_split_variance(pace_splits_list, run_distance)
            
    # 2. Map our calculated numbers to match our config keys exactly
    compiled_run_metrics = {
        "average_pace_seconds": run_pace_seconds,
        "total_elevation_gain_ft": run_elevation,
        "final_mile_kick_percent": final_kick_percent,
        "total_distance_miles": run_distance,
        "split_variance_seconds": split_variance
    }

    # 3. Dynamic loop through your configuration file rules
    for pillar_id, config in FINAL_METRIC_CONFIG["single_run_patches"].items():
        m_key = config["metric_key"]
        val = compiled_run_metrics.get(m_key)
        
        # Skip if missing heart rate/weather data or flagged as uncalculated (-1.0)
        if val is None or val == -1.0:
            continue
            
        # Enforce minimum distance criteria rules (like Pillar 5's 3-mile rule)
        if "requires_min_distance" in config and run_distance < config["requires_min_distance"]:
            continue
            
        # Evaluate bounds based on inversion rules
        for tier in config["tiers"]:
            if config.get("is_inverted"):
                # Fast paces/low deltas: Smaller numbers are superior
                if tier["min_val"] <= val <= tier["max_val"]:
                    earned_patches.append({
                        "pillar": pillar_id,
                        "id": tier["id"],
                        "name": tier["name"],
                        "icon": tier["icon"]
                    })
                    break  # Found our tier match, exit to next pillar
            else:
                # High volume/high climbing: Bigger numbers are superior
                if tier["min_val"] <= val <= tier["max_val"]:
                    earned_patches.append({
                        "pillar": pillar_id,
                        "id": tier["id"],
                        "name": tier["name"],
                        "icon": tier["icon"]
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
    run_patches = check_single_run_patches(new_run_log)
    
    # Attach the badges permanently inside the individual workout log dictionary object
    new_run_log["earned_patches"] = run_patches
    
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

