# -*- coding: utf-8 -*-
"""
ATHLETIC TRAINING HUB — SERVICES & TELEMETRY PROCESSING CORE
Handles high-precision Garmin .FIT and .GPX data ingestion, localizes time zone coordinates,
and implements the Design B Overall Runner Level tracking matrix. Focused on racing performance.
"""

import xml.etree.ElementTree as ET
import math
import json
from datetime import datetime, timedelta
from fitparse import FitFile
import pandas as pd
from typing import List, Dict, Any

# Import configurations safely
try:
    from metrics_config import FINAL_METRIC_CONFIG
except ImportError:
    # Fallback inline dictionary defaults if config file is missing during bootstrap
    FINAL_METRIC_CONFIG = {
        "athlete_settings": {
            "master_level_factor": 120.0,
            "inactivity_grace_days": 7,
            "inactivity_decay_penalty": 5
        }
    }

# =========================================================================
# 🛰️ HIGH-PRECISION ROLLING PERFORMANCE SCANNERS
# =========================================================================

def calculate_rolling_one_mile_pr(fit_file: FitFile) -> float:
    """
    Scans point-by-point tracking records to extract the absolute fastest 
    continuous, rolling 1-mile (1,609.34 meters) window inside an activity log.
    Returns the minimum time required in decimal minutes.
    """
    trackpoints = []
    
    for record in fit_file.get_messages('record'):
        data = {d.name: d.value for d in record}
        if data.get('distance') is not None and data.get('timestamp') is not None:
            trackpoints.append({
                'distance': float(data['distance']), 
                'timestamp': data['timestamp']
            })
            
    if len(trackpoints) < 2:
        return 0.0
        
    df = pd.DataFrame(trackpoints).sort_values('timestamp').reset_index(drop=True)
    target_meters = 1609.34
    min_seconds_for_mile = float('inf')
    left = 0
    
    for right in range(len(df)):
        while df.loc[right, 'distance'] - df.loc[left, 'distance'] >= target_meters:
            time_delta = (df.loc[right, 'timestamp'] - df.loc[left, 'timestamp']).total_seconds()
            # Eliminate extreme anomalies or watch pauses
            if time_delta > 180 and time_delta < min_seconds_for_mile:
                min_seconds_for_mile = time_delta
            left += 1
            
    if min_seconds_for_mile == float('inf'):
        return 0.0
        
    return round(min_seconds_for_mile / 60.0, 2)


def calculate_continuous_ascent_pr(fit_file: FitFile) -> float:
    """
    Scans coordinate altitude vectors to extract your single greatest continuous, 
    un-interrupted upward vertical climbing push (measuring peak gain before a downhill reset).
    Returns total vertical feet as a float value.
    """
    max_continuous_climb_meters = 0.0
    current_segment_climb_meters = 0.0
    last_altitude_meters = None
    
    for record in fit_file.get_messages('record'):
        data = {d.name: d.value for d in record}
        alt = data.get('enhanced_altitude') or data.get('altitude')
        
        if alt is not None:
            alt_float = float(alt)
            if last_altitude_meters is not None:
                if alt_float > last_altitude_meters:
                    current_segment_climb_meters += (alt_float - last_altitude_meters)
                elif alt_float < last_altitude_meters - 1.5:
                    # A downhill drop exceeding 1.5 meters resets the active climbing surge segment
                    if current_segment_climb_meters > max_continuous_climb_meters:
                        max_continuous_climb_meters = current_segment_climb_meters
                    current_segment_climb_meters = 0.0
            last_altitude_meters = alt_float
            
    if current_segment_climb_meters > max_continuous_climb_meters:
        max_continuous_climb_meters = current_segment_climb_meters
        
    return round(max_continuous_climb_meters * 3.28084, 1)

# =========================================================================
# 📥 TELEMETRY DATA INGESTION ENGINE (.FIT & .GPX)
# =========================================================================

def parse_garmin_fit(file_bytes) -> Dict[str, Any]:
    """
    Parses a raw bytes stream of a Garmin .fit file and extracts core metrics.
    Localizes UTC timestamps to Mountain Time (MDT) and runs rolling PR maps.
    """
    #fit_file = FitFile(file_bytes)
    #total_distance_meters = 0.0
    #total_calories = None
    #heart_rates = []
    #timestamps = []
    #total_ascent_meters = 0.0
    #last_altitude = None
    #
    ## Mountain Time Zone Correction Offset: Subtract 6 hours from raw UTC
    #tz_offset = timedelta(hours=6)

    ## 1. Loop records to gather overall workout metrics
    #for record in fit_file.get_messages('record'):
    #    data_dict = {data.name: data.value for data in record}
    #    
    #    if 'timestamp' in data_dict and data_dict['timestamp'] is not None:
    #        timestamps.append(data_dict['timestamp'] - tz_offset)
    #    
    #    current_alt = data_dict.get('enhanced_altitude') or data_dict.get('altitude')
    #    if current_alt is not None:
    #        current_alt = float(current_alt)
    #        if last_altitude is not None and current_alt > last_altitude:
    #            total_ascent_meters += (current_alt - last_altitude)
    #        last_altitude = current_alt
    #    
    #    if 'distance' in data_dict and data_dict['distance'] is not None:
    #        total_distance_meters = float(data_dict['distance'])
    #    if 'calories' in data_dict and data_dict['calories'] is not None:
    #        total_calories = int(data_dict['calories'])
    #    if 'heart_rate' in data_dict and data_dict['heart_rate'] is not None:
    #        heart_rates.append(int(data_dict['heart_rate']))


    fit_file = FitFile(file_bytes)
    total_distance_meters = 0.0
    total_seconds = 0.0
    total_ascent_meters = 0.0
    total_calories = None
    heart_rates = []
    timestamps = []
    
    # Mountain Time Zone Correction Offset: Subtract 6 hours from raw UTC
    tz_offset = timedelta(hours=6)

    # 1. Pull pre-filtered summary stats calculated directly by the Garmin device
    for session in fit_file.get_messages('session'):
        session_data = {d.name: d.value for d in session}
        if session_data.get('total_timer_time') is not None:
            total_seconds = float(session_data['total_timer_time'])
        if session_data.get('total_distance') is not None:
            total_distance_meters = float(session_data['total_distance'])
        if session_data.get('total_ascent') is not None:
            total_ascent_meters = float(session_data['total_ascent'])
        if session_data.get('total_calories') is not None:
            total_calories = int(session_data['total_calories'])

    # 2. Loop records to gather timestamp timelines and heart rate metrics safely
    for record in fit_file.get_messages('record'):
        data_dict = {data.name: data.value for data in record}
        
        if 'timestamp' in data_dict and data_dict['timestamp'] is not None:
            timestamps.append(data_dict['timestamp'] - tz_offset)
        
        # --- THE NOISY ALTITUDE ACCUMULATION IS COMPLETELY REMOVED FROM HERE ---
        
        if total_distance_meters == 0.0 and 'distance' in data_dict and data_dict['distance'] is not None:
            total_distance_meters = float(data_dict['distance'])
        if total_calories is None and 'calories' in data_dict and data_dict['calories'] is not None:
            total_calories = int(data_dict['calories'])
        if 'heart_rate' in data_dict and data_dict['heart_rate'] is not None:
            heart_rates.append(int(data_dict['heart_rate']))









    #### 2. Loop lap messages to extract specific mile splits
    ###mile_splits = []
    ###lap_counter = 1
    ###
    ###for lap in fit_file.get_messages('lap'):
    ###    lap_data = {data.name: data.value for data in lap}
    ###    lap_dist_meters = lap_data.get('total_distance') or 0.0
    ###    lap_secs = lap_data.get('total_timer_time') or lap_data.get('total_elapsed_time') or 0.0
    ###    
    ###    if lap_dist_meters > 0.05 and lap_secs > 0:
    ###        lap_miles = lap_dist_meters * 0.000621371
    ###        lap_min_int = int(lap_secs // 60)
    ###        lap_sec_int = int(lap_secs % 60)
    ###        
    ###        lap_pace_raw = (lap_secs / 60.0) / lap_miles if lap_miles > 0 else 0.0
    ###        pace_min = int(lap_pace_raw)
    ###        pace_sec = int((lap_pace_raw - pace_min) * 60)
    ###        
    ###        mile_splits.append({
    ###            "split_num": lap_counter,
    ###            "distance_mi": round(lap_miles, 2),
    ###            "time": f"{lap_min_int:02d}:{lap_sec_int:02d}",
    ###            "pace": f"{pace_min}:{pace_sec:02d}"
    ###        })
    ###        lap_counter += 1
    # 2. Loop lap messages to extract specific mile splits
    mile_splits = []
    lap_counter = 1
    
    for lap in fit_file.get_messages('lap'):
        lap_data = {data.name: data.value for data in lap}
        lap_dist_meters = lap_data.get('total_distance') or 0.0
        lap_secs = lap_data.get('total_timer_time') or lap_data.get('total_elapsed_time') or 0.0
        
        if lap_dist_meters > 0.05 and lap_secs > 0:
            lap_miles = lap_dist_meters * 0.000621371
            
            # --- FIX #1: ROUND TO THE NEAREST WHOLE SECOND TO PREVENT TRUNCATION ---
            rounded_lap_secs = int(round(lap_secs))
            lap_min_int = rounded_lap_secs // 60
            lap_sec_int = rounded_lap_secs % 60
            
            lap_pace_raw = (lap_secs / 60.0) / lap_miles if lap_miles > 0 else 0.0
            pace_min = int(lap_pace_raw)
            pace_sec = int(round((lap_pace_raw - pace_min) * 60))
            
            # Adjust if seconds round up to 60
            if pace_sec >= 60:
                pace_min += 1
                pace_sec = 0
            
            mile_splits.append({
                "split_num": lap_counter,
                "distance_mi": round(lap_miles, 2),
                "time": f"{lap_min_int:02d}:{lap_sec_int:02d}",
                "pace": f"{pace_min}:{pace_sec:02d}"
            })
            lap_counter += 1

    # =========================================================================
    # ⏱ FIX #2: CONVERT OVERALL DECIMAL PACE TO CLOCK STRING (e.g., 7.18 -> "7:11")
    # =========================================================================
    avg_hr = sum(heart_rates) / len(heart_rates) if heart_rates else 0
    total_miles_calculated = total_distance_meters * 0.000621371
    
    if total_miles_calculated > 0.05 and total_seconds > 0:
        total_minutes_float = total_seconds / 60.0
        overall_decimal_pace = total_minutes_float / total_miles_calculated
        
        # Split decimal into clear minutes and seconds clock components
        overall_pace_min = int(overall_decimal_pace)
        overall_pace_sec = int(round((overall_decimal_pace - overall_pace_min) * 60))
        
        if overall_pace_sec >= 60:
            overall_pace_min += 1
            overall_pace_sec = 0
            
        pace_display_string = f"{overall_pace_min}:{overall_pace_sec:02d}"
    else:
        pace_display_string = "00:00"











    # Ingestion metrics consolidation
    ###total_seconds = (timestamps[-1] - timestamps[0]).total_seconds() if len(timestamps) >= 2 else 0
    # Extracts pre-filtered actual moving timer time computed directly by the Garmin device
    total_seconds=0.0
    for session in fit_file.get_messages('session'):
        s_data = {d.name: d.value for d in session}
        if s_data.get('total_timer_time') is not None:
            total_seconds = float(s_data['total_timer_time'])

    # Fallback wrapper remains active just in case the metadata message is missing
    if total_seconds == 0.0 and len(timestamps) >= 2:
        total_seconds = (timestamps[-1] - timestamps[0]).total_seconds()


    avg_hr = sum(heart_rates) / len(heart_rates) if heart_rates else 0
    total_miles_calculated = total_distance_meters * 0.000621371
    
    # Calculate overall pace float metric
    overall_decimal_pace = (total_seconds / 60.0) / total_miles_calculated if total_miles_calculated > 0.05 else 0.0

    # Metabolic Fallback Safeguard (Distance * 100 kcal) if file is missing calorie metadata
    if total_calories is None or total_calories <= 0:
        total_calories = int(total_miles_calculated * 100)
    
    # High-precision localized timestamp extraction
    formatted_date = timestamps[0].strftime('%Y-%m-%d %H:%M:%S') if timestamps else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
 
    return {
        "distance_km": round(total_distance_meters / 1000.0, 2),
        "distance_mi": round(total_miles_calculated, 2),
        "calories": total_calories,
        "avg_heart_rate": round(avg_hr, 1),
        "date": formatted_date,
        "duration_seconds": total_seconds,
        "elevation_gain_ft": round(total_ascent_meters * 3.28084, 1),
        "pace":pace_display_string,
        "splits": mile_splits,
        "rolling_mile_pr": calculate_rolling_one_mile_pr(fit_file),
        "continuous_climb_pr": calculate_continuous_ascent_pr(fit_file),
        "source": "Garmin FIT Engine"
    }


def parse_garmin_gpx(player, file_bytes):
    """
    Parses open standard XML GPX track logs, updates player attributes,
    and stores historical training logs.
    """
    try:
        root = ET.fromstring(file_bytes)
        
        # 1. Isolate tracking point arrays
        points = root.findall('.//{*}trkpt')
        if not points:
            return False, 'No tracking coordinate nodes discovered inside GPX script.'
        
        # 2. Extract primary calendar date string dynamically
        gpx_date_str = None
        time_node = root.find('.//{*}time')
        if time_node is not None and time_node.text:
            gpx_date_str = time_node.text[:10]
        else:
            gpx_date_str = datetime.now().strftime('%Y-%m-%d')
        
        # 3. Precision calculation of authentic Elapsed Run Duration
        duration_str = None
        start_time_node = points[0].find('{*}time') if hasattr(points[0], 'find') else None
        end_time_node = points[-1].find('{*}time') if hasattr(points[-1], 'find') else None
        
        if start_time_node is None: start_time_node = points[0].find('.//{*}time')
        if end_time_node is None: end_time_node = points[-1].find('.//{*}time')
        
        if start_time_node is not None and end_time_node is not None and start_time_node.text and end_time_node.text:
            try:
                t_start = start_time_node.text.replace('Z', '').split('.')[0]
                t_end = end_time_node.text.replace('Z', '').split('.')[0]
                dt_start = datetime.strptime(t_start, '%Y-%m-%dT%H:%M:%S')
                dt_end = datetime.strptime(t_end, '%Y-%m-%dT%H:%M:%S')
                elapsed_seconds = int((dt_end - dt_start).total_seconds())
                
                if elapsed_seconds > 0:
                    hrs = elapsed_seconds // 3600
                    mins = (elapsed_seconds % 3600) // 60
                    secs = elapsed_seconds % 60
                    duration_str = f'{hrs:02d}:{mins:02d}:{secs:02d}'
            except Exception:
                pass
        
        if not duration_str:
            duration_str = '00:30:00'
        
        total_distance = 0.0
        total_elevation_gain = 0.0
        prev_lat, prev_lon, prev_ele = None, None, None
        
        for pt in points:
            lat = float(pt.attrib['lat'])
            lon = float(pt.attrib['lon'])
            ele_node = pt.find('.//{*}ele')
            ele = float(ele_node.text) if ele_node is not None else 0.0
            
            if prev_lat is not None:
                dlat = math.radians(lat - prev_lat)
                dlon = math.radians(lon - prev_lon)
                a = math.sin(dlat/2)**2 + math.cos(math.radians(prev_lat)) * math.cos(math.radians(lat)) * math.sin(dlon/2)**2
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                distance_miles = (6371 * c) * 0.621371
                total_distance += distance_miles
                if ele > prev_ele:
                    total_elevation_gain += (ele - prev_ele) * 3.28084
            
            prev_lat, prev_lon, prev_ele = lat, lon, ele
        
        total_distance = round(total_distance, 2)
        total_elevation_gain = round(total_elevation_gain, 1)
        
        if total_distance <= 0.0:
            return False, 'GPX coordinate spatial logic resolves to 0 miles covered.'

        if not hasattr(player, 'history_logs'): player.history_logs = []
        for log in player.history_logs:
            if isinstance(log, str) and gpx_date_str in log and 'miles' in log.lower():
                return False, f'Duplicate Workout Applied. Date {gpx_date_str} already synced.'
        
        gold_earned = int(total_distance * 5 + 5)
        xp_earned = int(total_distance * 10)
        
        player.gold = getattr(player, 'gold', 0) + gold_earned
        player.total_xp = getattr(player, 'total_xp', 0) + xp_earned
        player.days_tracked = getattr(player, 'days_tracked', 0) + 1
        
        # Accumulate fatigue points from physical running efforts, capped at 100
        calculated_fatigue_cost = int(total_distance * 15)
        current_fatigue = int(getattr(player, 'fatigue', 0))
        player.fatigue = min(100, current_fatigue + calculated_fatigue_cost)
        
        while hasattr(player, 'xp_needed_for_next_level') and player.total_xp >= player.xp_needed_for_next_level():
            player.total_xp -= player.xp_needed_for_next_level()
            player.level += 1
            player.stat_points = getattr(player, 'stat_points', 0) + 2
        
        try:
            h, m, s = map(int, duration_str.split(':'))
            total_minutes = h * 60 + m + (s / 60)
            pace_val = round(total_minutes / total_distance, 2) if total_distance > 0 else 0.0
        except Exception:
            pace_val = 8.50
        
        log_msg = f'[{gpx_date_str}] Run: {total_distance:.2f} miles (+{gold_earned}g) [Duration: {duration_str}, Pace: {pace_val:.2f} min/mi, Elevation Climbed: +{total_elevation_gain} ft.]'
        player.history_logs.append(log_msg)
        
        try:
            save_payload = player.to_dict() if hasattr(player, 'to_dict') else player.__dict__
            with open('save_file.json', 'w', encoding='utf-8') as db_file:
                json.dump(save_payload, db_file, default=str, indent=4)
        except Exception: pass
        
        return True, log_msg
    except Exception as e:
        return False, str(e)


def parse_garmin_tcx(player, file_bytes): return True, 'TCX module active'
def parse_garmin_sleep_csv(player, file_bytes): return True, 'Sleep CSV module active'

# =========================================================================
# 📈 DESIGN B PROGRESSION ALGORITHMS (OVERALL RUNNER LEVEL)
# =========================================================================

def calculate_character_stats(history_logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Parses full history logs to compute current individual metrics points,
    and applies Design B to sum mate them into an overall unified Runner Level.
    """
    total_end_pts = 0
    total_pace_pts = 0
    total_elev_pts = 0

    for run in history_logs:
        if not isinstance(run, dict):
            continue
            
        miles = float(run.get('Distance (Miles)', run.get('distance_mi', 0.0)))
        
        raw_pace = run.get('pace', 11.0)
        if isinstance(raw_pace, str) and ":" in raw_pace:
            try:
                parts = raw_pace.split(":")
                pace = float(parts[0]) + (float(parts[1]) / 60.0)
            except (ValueError, IndexError):
                pace = 11.0
        else:
            try:
                pace = float(raw_pace)
            except (ValueError, TypeError):
                pace = 11.0

        
        elev_str = str(run.get('Elevation (ft)', run.get('elevation_gain_ft', '0'))).replace('+', '').replace('ft', '').strip()
        elevation = float(elev_str) if elev_str else 0.0

        # 2. Accumulate Aerobic Stamina points
        endurance_pts = int(miles * 10)
        if miles >= 10.0:
            endurance_pts += 50
        total_end_pts += endurance_pts

        # 3. Accumulate Stride Pace points (Baseline 11:00 min/mi)
        pace_pts = 0
        if pace < 11.0 and pace > 3.0:
            pace_pts = int((11.0 - pace) * 100)
        if pace <= 7.0 and pace > 3.0:
            pace_pts += 100
        total_pace_pts += pace_pts

        # 4. Accumulate Vertical Climbing points
        elevation_pts = int(elevation / 2)
        if elevation >= 500.0:
            elevation_pts += 75
        total_elev_pts += elevation_pts

    # 5. Math Level Curves and Progressions
    def get_level_and_progress(total_pts, factor):
        if total_pts <= 0:
            return 1, 0.0
        current_lvl = int(math.floor(math.sqrt(total_pts / factor))) + 1
        
        pts_for_current_lvl = int(((current_lvl - 1) ** 2) * factor)
        pts_for_next_lvl = int((current_lvl ** 2) * factor)
        
        needed_pts_range = pts_for_next_lvl - pts_for_current_lvl
        gained_in_lvl = total_pts - pts_for_current_lvl
        
        progress_pct = min(1.0, max(0.0, gained_in_lvl / float(needed_pts_range or 1)))
        return current_lvl, progress_pct

    # Calculate sub-metric profiles for backward compatibility components
    end_lvl, end_prog = get_level_and_progress(total_end_pts, 100)
    pace_lvl, pace_prog = get_level_and_progress(total_pace_pts, 150)
    elev_lvl, elev_prog = get_level_and_progress(total_elev_pts, 120)

    # DESIGN B FUSION: Master Runner Core Power Pool is the sum of all performance attributes
    total_power_pool = total_end_pts + total_pace_pts + total_elev_pts
    level_scaling_factor = FINAL_METRIC_CONFIG["athlete_settings"]["master_level_factor"]

    overall_runner_level, overall_progress_pct = get_level_and_progress(total_power_pool, level_scaling_factor)

    return {
        "overall_level": overall_runner_level,
        "overall_progress_pct": round(overall_progress_pct * 100, 1),
        "total_power_pool": total_power_pool,
        "endurance": {"level": end_lvl, "progress": end_prog, "total": total_end_pts},
        "pace": {"level": pace_lvl, "progress": pace_prog, "total": total_pace_pts},
        "elevation_force": {"level": elev_lvl, "progress": elev_prog, "total": total_elev_pts}
    }


def calculate_stat_decay(history_logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compares the date of the most recent run against today's date.
    Deducts a small amount of XP for each day of inactivity past a 7-day grace period.
    """
    if not history_logs:
        return {"days_inactive": 0, "decay_penalty": 0, "applied": False}
        
    try:
        dates = []
        for run in history_logs:
            if isinstance(run, dict):
                date_val = run.get('Date') or run.get('date')
                if date_val:
                    dates.append(pd.to_datetime(str(date_val).split(' ')[0]))
                
        if not dates:
            return {"days_inactive": 0, "decay_penalty": 0, "applied": False}
            
        latest_run_date = max(dates)
        today = pd.to_datetime(datetime.now().date())
        
        days_inactive = (today - latest_run_date).days
        
        # Rule: Grace period of 7 days. After that, lose 5 XP per day.
        if days_inactive > 7:
            decay_days = days_inactive - 7
            decay_penalty = decay_days * 5
            return {
                "days_inactive": days_inactive,
                "decay_penalty": decay_penalty,
                "applied": True
            }
            
        return {"days_inactive": max(0, days_inactive), "decay_penalty": 0, "applied": False}
    except:
        return {"days_inactive": 0, "decay_penalty": 0, "applied": False}


def calculate_monthly_fitness_load(history_logs: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Computes a chronological monthly workload dataset to expose acute drops
    and chronic spikes in performance capacity across historical seasons.
    """
    if not history_logs:
        return pd.DataFrame()
        
    records = []
    for r in history_logs:
        if isinstance(r, dict):
            date_val = r.get('Date') or r.get('date')
            dist_val = r.get('Distance (Miles)', r.get('distance_mi', 0.0))
            if date_val:
                records.append({'Date': date_val, 'Distance (Miles)': dist_val})
                
    if not records:
        return pd.DataFrame()
        
    df_load = pd.DataFrame(records)
    df_load['Date'] = pd.to_datetime(df_load['Date'])
    df_load['Distance'] = pd.to_numeric(df_load['Distance (Miles)'], errors='coerce').fillna(0.0)
    
    df_load = df_load.sort_values('Date')
    monthly = df_load.set_index('Date').resample('ME')['Distance'].sum().reset_index()
    
    monthly['Acute_Fatigue'] = monthly['Distance']
    monthly['Chronic_Fitness'] = monthly['Distance'].rolling(window=3, min_periods=1).mean()
    
    monthly['Performance_Status'] = monthly['Chronic_Fitness'] - monthly['Acute_Fatigue']
    monthly['Month_Label'] = monthly['Date'].dt.strftime('%b %Y')
    
    return monthly


def get_live_combat_stats(history_logs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculates active racing modifiers based on a 30-Day Moving Window.
    Returns tracking multipliers for Stamina Pool Capacity and Pace Maintenance.
    Focused on pure athletic performance limits with zero automotive lingo.
    """
    default_stats = {
        "race_stamina_bonus": 0,
        "active_stamina_pool": 100,
        "pacing_efficiency_rating": 0.05,
        "climbing_power_modifier": 1.0,
        "endurance_ratio": 1.0
    }
    
    if not history_logs:
        return default_stats
        
    try:
        records = []
        for r in history_logs:
            if isinstance(r, dict):
                date_val = r.get('Date') or r.get('date')
                dist_val = r.get('Distance (Miles)', r.get('distance_mi', 0.0))
                pace_val = r.get('pace', 11.0)
                elev_val = r.get('Elevation (ft)', r.get('elevation_gain_ft', 0.0))
                if date_val:
                    records.append({
                        'Date': date_val, 
                        'Distance (Miles)': dist_val, 
                        'pace': pace_val, 
                        'Elevation (ft)': elev_val
                    })
                    
        if not records:
            return default_stats
            
        df = pd.DataFrame(records)
        df['Date'] = pd.to_datetime(df['Date'])
        
        #df['Miles'] = pd.to_numeric(df['Distance (Miles)'], errors='coerce').fillna(0.0)
        #df['Pace_Val'] = pd.to_numeric(df['pace'], errors='coerce').fillna(11.0)
        df['Miles'] = pd.to_numeric(df['Distance (Miles)'], errors='coerce').fillna(0.0)

        # --- NEW STRING INSULATED PACE PARSER ---
        def parse_pace_to_float(p):
            if isinstance(p, (int, float)):
                return float(p)
            if isinstance(p, str) and ":" in p:
                try:
                    parts = p.split(":")
                    # Converts "7:11" into 7 + (11 / 60) = 7.1833
                    return float(parts[0]) + (float(parts[1]) / 60.0)
                except (ValueError, IndexError):
                    return 11.0
            try:
                return float(p)
            except (ValueError, TypeError):
                return 11.0

        df['Pace_Val'] = df['pace'].apply(parse_pace_to_float)

        elev_str = df['Elevation (ft)'].astype(str).str.replace('+', '', regex=False).str.replace('ft', '', regex=False).str.strip()
        df['Elev'] = pd.to_numeric(elev_str, errors='coerce').fillna(0.0)
        
        df = df.sort_values('Date').set_index('Date')
        
        acute_miles = df['Miles'].rolling('30D', min_periods=1).sum().iloc[-1]
        chronic_miles = df['Miles'].rolling('90D', min_periods=1).mean().iloc[-1] * 30.0
        
        acute_pace = df['Pace_Val'].rolling('30D', min_periods=1).mean().iloc[-1]
        acute_elev = df['Elev'].rolling('30D', min_periods=1).sum().iloc[-1]
        
        e_ratio = acute_miles / chronic_miles if chronic_miles > 0 else 1.0
        e_ratio = max(0.4, min(1.5, e_ratio))
        






        # 1. Aerobic Stamina Capacity: Scales baseline race endurance tank
        base_stamina = 100
        stamina_bonus = int((acute_miles * 1.0) * (e_ratio ** 2))
        final_stamina_pool = base_stamina + stamina_bonus
        
        # 2. Pacing Efficiency: High tempo loads reduce racing energy drops
        pacing_rating = 0.05
        if acute_pace < 11.0:
            pacing_rating += (11.0 - acute_pace) * 0.03
        final_efficiency = min(0.45, max(0.02, pacing_rating * e_ratio))
        
        # 3. Vertical Climbing Surge Modifier: Uphill work builds acceleration leverage
        climb_mod = 1.0
        if acute_elev > 0:
            climb_mod += (acute_elev / 2000.0)
        final_climb_mod = round(max(0.5, climb_mod * e_ratio), 2)
        
        return {
            "race_stamina_bonus": stamina_bonus,
            "active_stamina_pool": final_stamina_pool,
            "pacing_efficiency_rating": round(final_efficiency, 3),
            "climbing_power_modifier": final_climb_mod,
            "endurance_ratio": round(e_ratio, 2)
        }
    except:
        return default_stats

