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
                    gold_rewarded = int(s['dist'] * 10)
                    xp_gained = int(s['dist'] * 50)
                    total_gold_rewarded += gold_rewarded
                    total_xp_gained += xp_gained
                    
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

