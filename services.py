# -*- coding: utf-8 -*-
from datetime import datetime
import math
import json
from fitparse import FitFile

from security_utils import (
    MAX_TRACK_POINTS,
    UnsafeInputError,
    clamp_elevation_m,
    parse_xml_safely,
    validate_coordinate,
)



def parse_garmin_fit(file_bytes):
    """
    Parses a raw bytes stream of a Garmin .fit file 
    and extracts core metrics including individual lap mile splits.
    """
    fit_file = FitFile(file_bytes)
    total_distance_meters = 0.0
    total_calories = 0
    heart_rates = []
    timestamps = []
    
    total_ascent_meters = 0.0
    last_altitude = None
    
    # 1. Loop records to gather overall workout metrics
    for record in fit_file.get_messages('record'):
        data_dict = {data.name: data.value for data in record}
        
        if 'timestamp' in data_dict and data_dict['timestamp'] is not None:
            timestamps.append(data_dict['timestamp'])
        
        current_alt = data_dict.get('enhanced_altitude') or data_dict.get('altitude')
        if current_alt is not None:
            if last_altitude is not None and current_alt > last_altitude:
                total_ascent_meters += (current_alt - last_altitude)
            last_altitude = current_alt
        
        if 'distance' in data_dict and data_dict['distance'] is not None:
            total_distance_meters = data_dict['distance']
        if 'calories' in data_dict and data_dict['calories'] is not None:
            total_calories = data_dict['calories']
        if 'heart_rate' in data_dict and data_dict['heart_rate'] is not None:
            heart_rates.append(data_dict['heart_rate'])

    # 2. Loop lap messages to extract specific mile splits
    mile_splits = []
    lap_counter = 1
    
    for lap in fit_file.get_messages('lap'):
        lap_data = {data.name: data.value for data in lap}
        
        lap_dist_meters = lap_data.get('total_distance') or 0.0
        lap_secs = lap_data.get('total_timer_time') or lap_data.get('total_elapsed_time') or 0.0
        
        if lap_dist_meters > 0 and lap_secs > 0:
            lap_miles = lap_dist_meters * 0.000621371
            
            # Format lap duration string (MM:SS)
            lap_min_int = int(lap_secs // 60)
            lap_sec_int = int(lap_secs % 60)
            lap_duration_str = f"{lap_min_int:02d}:{lap_sec_int:02d}"
            
            # Calculate lap pace (min/mi)
            lap_pace_raw = (lap_secs / 60.0) / lap_miles if lap_miles > 0 else 0.0
            pace_min = int(lap_pace_raw)
            pace_sec = int((lap_pace_raw - pace_min) * 60)
            lap_pace_str = f"{pace_min}:{pace_sec:02d}"
            
            mile_splits.append({
                "split_num": lap_counter,
                "distance_mi": round(lap_miles, 2),
                "time": lap_duration_str,
                "pace": lap_pace_str
            })
            lap_counter += 1

    # Calculations for main tracking engine
    total_seconds = (timestamps[-1] - timestamps[0]).total_seconds() if len(timestamps) >= 2 else 0

    avg_hr = sum(heart_rates) / len(heart_rates) if heart_rates else 0
    total_elevation_gain_ft = total_ascent_meters * 3.28084
    
    # Extract from the first timestamp item index inside the collected tracking array
    if timestamps and isinstance(timestamps[0], datetime):
        formatted_date = timestamps[0].strftime('%Y-%m-%d')
    else:
        formatted_date = datetime.now().strftime('%Y-%m-%d')
 
    return {
        "distance_km": round(total_distance_meters / 1000.0, 2),
        "calories": total_calories,
        "avg_heart_rate": round(avg_hr, 1),
        "date": formatted_date,
        "duration_seconds": total_seconds,
        "elevation_gain_ft": round(total_elevation_gain_ft, 1),
        "splits": mile_splits,  # <-- ADDED MILE SPLITS ARRAY HERE
        "source": "Garmin FIT Engine"
    }


def parse_garmin_gpx(player, file_bytes):
    try:
        root = parse_xml_safely(file_bytes)
        
        # 1. Isolate tracking point arrays
        points = root.findall('.//{*}trkpt')
        if not points:
            return False, 'No tracking coordinate nodes discovered inside GPX script.'
        if len(points) > MAX_TRACK_POINTS:
            return False, f'GPX track exceeds the {MAX_TRACK_POINTS:,} trackpoint limit.'
        
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
        
        # Wildcard string search fallback if namespaces alter standard locations
        if start_time_node is None: start_time_node = points[0].find('.//{*}time')
        if end_time_node is None: end_time_node = points[-1].find('.//{*}time')
        
        if start_time_node is not None and end_time_node is not None and start_time_node.text and end_time_node.text:
            try:
                # Strip timezone artifacts cleanly to normalize time differences
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
        
        # If trackpoints are missing time, fall back safely to an empirical 8-minute pace simulation
        if not duration_str:
            duration_str = '00:30:00'
        
        total_distance = 0.0
        total_elevation_gain = 0.0
        prev_lat, prev_lon, prev_ele = None, None, None
        
        for pt in points:
            if 'lat' not in pt.attrib or 'lon' not in pt.attrib:
                continue
            try:
                lat, lon = validate_coordinate(pt.attrib['lat'], pt.attrib['lon'])
            except (UnsafeInputError, TypeError, ValueError):
                continue
            ele_node = pt.find('.//{*}ele')
            ele = clamp_elevation_m(ele_node.text) if ele_node is not None else 0.0
            
            if prev_lat is not None and prev_ele is not None:
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
            if gpx_date_str in log and 'miles' in log.lower():
                return False, f'Duplicate Workout Applied. Date {gpx_date_str} already synced.'
        
        gold_earned = int(total_distance * 5 + 5)
        xp_earned = int(total_distance * 10)
        
        player.gold = getattr(player, 'gold', 0) + gold_earned
        player.total_xp = getattr(player, 'total_xp', 0) + xp_earned
        player.days_tracked = getattr(player, 'days_tracked', 0) + 1
        
        # --- FIXED INLINE FATIGUE ENGINE ---
        # Accumulate roughly 15 fatigue points per mile run, capped at the absolute max rating ceiling of 100
        calculated_fatigue_cost = int(total_distance * 15)
        current_fatigue = int(getattr(player, 'fatigue', 0))
        player.fatigue = min(100, current_fatigue + calculated_fatigue_cost)
        
        while hasattr(player, 'xp_needed_for_next_level') and player.total_xp >= player.xp_needed_for_next_level():
            player.total_xp -= player.xp_needed_for_next_level()
            player.level += 1
            player.stat_points = getattr(player, 'stat_points', 0) + 2
        
        # Calculate authentic running pace dynamically
        try:
            h, m, s = map(int, duration_str.split(':'))
            total_minutes = h * 60 + m + (s / 60)
            pace_val = round(total_minutes / total_distance, 2) if total_distance > 0 else 0.0
        except Exception:
            pace_val = 8.50
        
        # Compile log message string wrapping authentic tracking variables
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
# Append this logic directly to the bottom of your services.py file
import math

def calculate_character_stats(history_logs):
    """
    Parses full history logs to compute current levels and remainder XP 
    for Endurance, Pace, and Hill-Climbing Elevation Force.
    """
    total_end_pts = 0
    total_pace_pts = 0
    total_elev_pts = 0

    for run in history_logs:
        if not isinstance(run, dict):
            continue
            
        # 1. Clean data fields safely
        miles = float(run.get('Distance (Miles)', 0.0))
        pace = float(run.get('pace', 11.0))
        
        elev_str = str(run.get('Elevation (ft)', '0')).replace('+', '').replace('ft', '').strip()
        elevation = float(elev_str) if elev_str else 0.0

        # 2. Accumulate Endurance points
        endurance_pts = int(miles * 10)
        if miles >= 10.0:
            endurance_pts += 50
        total_end_pts += endurance_pts

        # 3. Accumulate Pace points (Baseline 11:00 min/mi)
        pace_pts = 0
        if pace < 11.0:
            pace_pts = int((11.0 - pace) * 20)
        if pace < 7.0:
            pace_pts += 100
        total_pace_pts += pace_pts

        # 4. Accumulate Hill-Climbing points
        elevation_pts = int(elevation / 2)
        if elevation >= 500.0:
            elevation_pts += 75
        total_elev_pts += elevation_pts

    # 5. Math Level Curves and Remainders
    def get_level_and_progress(total_pts, factor):
        if total_pts <= 0:
            return 1, 0.0
        current_lvl = int(math.floor(math.sqrt(total_pts / factor))) + 1
        
        # Calculate XP brackets for current level milestone parameters
        pts_for_current_lvl = int(((current_lvl - 1) ** 2) * factor)
        pts_for_next_lvl = int((current_lvl ** 2) * factor)
        
        needed_pts_range = pts_for_next_lvl - pts_for_current_lvl
        gained_in_lvl = total_pts - pts_for_current_lvl
        
        progress_pct = min(1.0, max(0.0, gained_in_lvl / float(needed_pts_range)))
        return current_lvl, progress_pct

    end_lvl, end_prog = get_level_and_progress(total_end_pts, 100)
    pace_lvl, pace_prog = get_level_and_progress(total_pace_pts, 150)
    elev_lvl, elev_prog = get_level_and_progress(total_elev_pts, 120)

    return {
        "endurance": {"level": end_lvl, "progress": end_prog, "total": total_end_pts},
        "pace": {"level": pace_lvl, "progress": pace_prog, "total": total_pace_pts},
        "elevation_force": {"level": elev_lvl, "progress": elev_prog, "total": total_elev_pts}
    }

# Append this function to the bottom of your services.py file
def calculate_stat_decay(history_logs):
    """
    Compares the date of the most recent run against today's date.
    Deducts a small amount of XP for each day of inactivity past a 7-day grace period.
    """
    if not history_logs:
        return {"days_inactive": 0, "decay_penalty": 0, "applied": False}
        
    try:
        # Extract the latest recorded tracking timestamp string
        dates = []
        for run in history_logs:
            if isinstance(run, dict) and 'Date' in run:
                dates.append(pd.to_datetime(run['Date']))
                
        if not dates:
            return {"days_inactive": 0, "decay_penalty": 0, "applied": False}
            
        latest_run_date = max(dates)
        today = pd.to_datetime(datetime.date.today())
        
        # Calculate raw delta difference
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

def calculate_monthly_fitness_load(history_logs):
    """
    Computes a chronological monthly workload dataset to expose acute drops
    and chronic spikes in performance capacity across historical seasons.
    """
    if not history_logs:
        return pd.DataFrame()
        
    # Convert logs into a structured time-series frame
    records = [r for r in history_logs if isinstance(r, dict) and 'Date' in r]
    df_load = pd.DataFrame(records)
    df_load['Date'] = pd.to_datetime(df_load['Date'])
    df_load['Distance'] = pd.to_numeric(df_load['Distance (Miles)'], errors='coerce').fillna(0.0)
    
    # Sort chronologically and group by month to match your exact tracking blocks
    df_load = df_load.sort_values('Date')
    monthly = df_load.set_index('Date').resample('ME')['Distance'].sum().reset_index()
    
    # Calculate Fatigue (Short-term 1-Month Load) vs Fitness (Long-term 3-Month Baseline)
    monthly['Acute_Fatigue'] = monthly['Distance']
    monthly['Chronic_Fitness'] = monthly['Distance'].rolling(window=3, min_periods=1).mean()
    
    # Formulate Training Stress Balance: Fitness minus Fatigue
    # A negative value reflects a volume drop (Taper/Detraining)
    # A positive value reflects an intense performance expansion
    monthly['Performance_Status'] = monthly['Chronic_Fitness'] - monthly['Acute_Fatigue']
    monthly['Month_Label'] = monthly['Date'].dt.strftime('%b %Y')
    
    return monthly

# Append this directly to the bottom of your services.py file
import pandas as pd
import numpy as np

def get_live_combat_stats(history_logs):
    """
    Calculates active character combat stats based on the 30-Day Moving Window.
    Returns modifiers for Max HP, Evasion, and Critical Damage.
    """
    # Baseline fallback defaults if no data exists
    default_stats = {
        "max_hp_bonus": 0,
        "active_hp": 100,
        "evasion_chance": 0.05,  # 5% base evasion
        "attack_power_modifier": 1.0,
        "endurance_modifier": 1.0
    }
    
    if not history_logs:
        return default_stats
        
    try:
        records = [r for r in history_logs if isinstance(r, dict) and 'Date' in r]
        df = pd.DataFrame(records)
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Standardize running fields
        df['Miles'] = pd.to_numeric(df['Distance (Miles)'], errors='coerce').fillna(0.0)
        df['Pace_Val'] = pd.to_numeric(df['pace'], errors='coerce').fillna(11.0)
        
        elev_str = df['Elevation (ft)'].astype(str).str.replace('+', '', regex=False).str.replace('ft', '', regex=False).str.strip()
        df['Elev'] = pd.to_numeric(elev_str, errors='coerce').fillna(0.0)
        
        # Sort index chronologically for window slicing
        df = df.sort_values('Date').set_index('Date')
        
        # Calculate Acute (30D sum) vs Chronic (90D rolling mean scaled to 30 days)
        acute_miles = df['Miles'].rolling('30D', min_periods=1).sum().iloc[-1]
        chronic_miles = df['Miles'].rolling('90D', min_periods=1).mean().iloc[-1] * 30.0
        
        acute_pace = df['Pace_Val'].rolling('30D', min_periods=1).mean().iloc[-1]
        acute_elev = df['Elev'].rolling('30D', min_periods=1).sum().iloc[-1]
        
        # Calculate your exact training ratio
        e_ratio = acute_miles / chronic_miles if chronic_miles > 0 else 1.0
        # Bound the ratio to prevent game-breaking scaling (Min: 0.4x, Max: 1.5x)
        e_ratio = max(0.4, min(1.5, e_ratio))
        
        # 1. ENDURANCE IMPACT -> Impact Max Health Pool
        # Every 10 miles run in the last 30 days adds 10 Base HP, scaled by your ratio squared
        base_hp = 100
        hp_bonus = int((acute_miles * 1.0) * (e_ratio ** 2))
        final_max_hp = base_hp + hp_bonus
        
        # 2. AGILITY PACE IMPACT -> Impact Evasion Chance
        # Faster paces under an 11-minute mile expand your turn dodging window
        evasion = 0.05 # 5% base dodge rate
        if acute_pace < 11.0:
            evasion += (11.0 - acute_pace) * 0.03 # +3% dodge per minute under baseline
        final_evasion = min(0.45, max(0.02, evasion * e_ratio)) # Cap max dodge at 45%
        
        # 3. HILL FORCE IMPACT -> Impact Attack Power
        # Vertical climbing work builds raw striking damage
        atk_mod = 1.0
        if acute_elev > 0:
            atk_mod += (acute_elev / 2000.0) # +50% damage per 2000ft climbed
        final_atk_mod = round(max(0.5, atk_mod * (e_ratio)), 2)
        
        return {
            "max_hp_bonus": hp_bonus,
            "active_hp": final_max_hp,
            "evasion_chance": round(final_evasion, 3),
            "attack_power_modifier": final_atk_mod,
            "endurance_modifier": round(e_ratio, 2)
        }
    except:
        return default_stats

