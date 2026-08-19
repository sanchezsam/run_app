import pandas as pd
import numpy as np
import datetime
import re
import json
import ast
import traceback
import streamlit as st

# ==============================================================================
# ⚙️ TROPHY ENGINE: CORE MATHEMATICAL ENGINE PIPELINE WITH STREAMLIT UI INJECTION
# ==============================================================================

def _clean_numeric_series(series):
    """Safely extracts clean floating-point values from mixed text/string fields (e.g. '12.50 Mi' -> 12.50)."""
    if series is None:
        return pd.Series(dtype=float)
    
    def extract_float(val):
        if isinstance(val, (int, float)):
            return float(val)
        if not val or not isinstance(val, str):
            return np.nan
        cleaned = val.replace(',', '').strip()
        matches = re.findall(r"[-+]?\d*\.\d+|\d+", cleaned)
        if matches:
            try:
                return float(matches[0])
            except (ValueError, TypeError):
                return np.nan
        return np.nan

    return series.apply(extract_float)


def _parse_pace_to_seconds(pace_val):
    """Helper to convert duration/pace strings like '5:42' or '5:42 /mi' into pure float seconds."""
    if isinstance(pace_val, (int, float)):
        return float(pace_val)
    if not isinstance(pace_val, str):
        return 0.0
        
    cleaned_pace = pace_val.strip().split()[0] if pace_val.strip() else ""
    
    if ':' in cleaned_pace:
        try:
            parts = [int(p) for p in cleaned_pace.split(':')]
            if len(parts) == 2:  # MM:SS
                return float(parts[0] * 60 + parts[1])
            elif len(parts) == 3:  # HH:MM:SS
                return float(parts[0] * 3600 + parts[1] * 60 + parts[2])
        except (ValueError, TypeError):
            pass
            
    try:
        return float(cleaned_pace)
    except (ValueError, TypeError):
        return 0.0


def _parse_time_to_seconds_fallback(val):
    """Helper to convert duration tokens or arbitrary time strings into numeric seconds for sorting."""
    if isinstance(val, (int, float)):
        return float(val)
    if not val or not isinstance(val, str):
        return float('inf')
        
    cleaned = val.strip()
    if ':' in cleaned:
        try:
            parts = [int(p) for p in cleaned.split(':')]
            if len(parts) == 2:    # MM:SS
                return float(parts[0] * 60 + parts[1])
            elif len(parts) == 3:  # HH:MM:SS
                return float(parts[0] * 3600 + parts[1] * 60 + parts[2])
        except (ValueError, TypeError):
            pass
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return float('inf')


def sanitize_json_history_logs(raw_history_list):
    """Safely extracts dictionary payloads out of a mixed string/object list."""
    if isinstance(raw_history_list, str):
        try:
            raw_history_list = json.loads(raw_history_list)
        except json.JSONDecodeError:
            return pd.DataFrame()

    if not raw_history_list or not isinstance(raw_history_list, list):
        return pd.DataFrame()
        
    sanitized_records = []
    
    for item in raw_history_list:
        if not isinstance(item, dict):
            continue
            
        date_val = item.get('Date', item.get('date', item.get('DATE', None)))
        if not date_val:
            continue
            
        record = {
            'Date': str(date_val),
            'Display_Distance': 0.0,
            'Avg_Pace': 0.0,
            'Total_Ascent': 0.0,
            'Five_K_Time': item.get('Five_K_Time', item.get('5k_time', ''))
        }
        
        dist = item.get('Distance (Miles)', item.get('Display_Distance', item.get('distance', item.get('Distance', 0.0))))
        if isinstance(dist, str):
            cleaned_dist = dist.replace(',', '')
            cleaned_dist = "".join(re.findall(r"[-+]?\d*\.\d+|\d+", cleaned_dist))
            try:
                record['Display_Distance'] = float(cleaned_dist)
            except (ValueError, TypeError):
                pass
        else:
            try:
                record['Display_Distance'] = float(dist)
            except (ValueError, TypeError):
                pass
            
        pace = item.get('pace', item.get('Avg_Pace', item.get('pace_mi', 0.0)))
        record['Avg_Pace'] = _parse_pace_to_seconds(pace)
            
        elev = item.get('Elevation (ft)', item.get('Total_Ascent', item.get('elevation', item.get('Elevation', 0.0))))
        if isinstance(elev, str):
            cleaned_elev = elev.replace(',', '')
            cleaned_elev = "".join(re.findall(r"[-+]?\d*\.\d+|\d+", cleaned_elev))
            try:
                record['Total_Ascent'] = abs(float(cleaned_elev))
            except (ValueError, TypeError):
                pass
        else:
            try:
                record['Total_Ascent'] = float(elev)
            except (ValueError, TypeError):
                pass
                
        sanitized_records.append(record)
        
    return pd.DataFrame(sanitized_records)


def calculate_personal_records(df_logs, target_year=None):
    """
    Evaluates individual historical records across 5 custom calculation patterns.
    If target_year is None, it bypasses all date grouping constraints to process
    absolute career 'All Time' records.
    """
    import personal_records_config as pr_cfg
    
    calculated_prs = {}
    
    for record in pr_cfg.PERSONAL_RECORDS_REGISTRY:
        rec_id = record["id"]
        # Pre-seed results array with configuration defaults
        calculated_prs[rec_id] = {"val": record["fallback_value"], "date": record["fallback_date"]}
                
        if df_logs is None or df_logs.empty:
            continue

        # --- DYNAMIC COLUMN RESOLUTION COCKPIT ---
        col_target = record["data_column"]
        existing_cols_lower = {c.lower(): c for c in df_logs.columns}
        
        if col_target not in df_logs.columns:
            low_target = str(col_target).lower()
            if low_target in existing_cols_lower:
                col_target = existing_cols_lower[low_target]
            elif any(x in low_target for x in ["dist", "mile", "display_distance"]):
                match = next((c for c in df_logs.columns if any(x in c.lower() for x in ["dist", "mile"])), None)
                col_target = match if match else "Display_Distance"
            elif any(x in low_target for x in ["pace", "avg_pace", "speed"]):
                match = next((c for c in df_logs.columns if any(x in c.lower() for x in ["pace", "speed"])), None)
                col_target = match if match else "Avg_Pace"
            elif any(x in low_target for x in ["ascent", "elev", "climb", "total_ascent"]):
                match = next((c for c in df_logs.columns if any(x in c.lower() for x in ["ascent", "elev", "climb"])), None)
                col_target = match if match else "Total_Ascent"
            elif any(x in low_target for x in ["5k", "five_k", "five"]):
                match = next((c for c in df_logs.columns if "5k" in c.lower()), None)
                col_target = match if match else "Five_K_Time"
                
        if col_target not in df_logs.columns:
            continue

        try:
            valid_df = df_logs[df_logs[col_target].notna()].copy()
            valid_df['Parsed_Year_Date'] = pd.to_datetime(valid_df['Date'], errors='coerce')
            
            # Conditionally apply annual slicing. Bypassed entirely when year is None (All Time)
            if target_year is not None:
                valid_df = valid_df[valid_df['Parsed_Year_Date'].dt.year == int(target_year)]
                
            if valid_df.empty:
                continue
            
            calc_mode = record.get("calculation_type", "").lower()
            
            # --- SELECTION CALCULATIONS ENGINE ---
            if calc_mode == "max":
                valid_df[col_target] = _clean_numeric_series(valid_df[col_target])
                valid_df = valid_df.dropna(subset=[col_target])
                if not valid_df.empty:
                    max_idx = valid_df[col_target].idxmax()
                    calculated_prs[rec_id]["val"] = f"{float(valid_df.loc[max_idx, col_target]):.2f} {record['metric_suffix']}".strip()
                    calculated_prs[rec_id]["date"] = str(valid_df.loc[max_idx, 'Date'])

            elif calc_mode == "min":
                valid_df['_Sort_Seconds'] = valid_df[col_target].apply(_parse_time_to_seconds_fallback)
                valid_df = valid_df[valid_df['_Sort_Seconds'] != float('inf')]
                if not valid_df.empty:
                    min_pos = valid_df['_Sort_Seconds'].values.argmin()
                    calculated_prs[rec_id]["val"] = f"{valid_df[col_target].iloc[min_pos]} {record['metric_suffix']}".strip()
                    calculated_prs[rec_id]["date"] = str(valid_df['Date'].iloc[min_pos])
                        
            elif calc_mode == "min_pace":
                valid_df['_Sort_Seconds'] = valid_df[col_target].apply(_parse_time_to_seconds_fallback)
                numeric_df = valid_df[(valid_df['_Sort_Seconds'] > 0) & (valid_df['_Sort_Seconds'] != float('inf'))]
                if not numeric_df.empty:
                    min_idx = numeric_df['_Sort_Seconds'].idxmin()
                    total_seconds = numeric_df.loc[min_idx, '_Sort_Seconds']
                    mins = int(total_seconds // 60)
                    secs = int(round(total_seconds % 60))
                    if secs == 60: 
                        mins += 1
                        secs = 0
                    calculated_prs[rec_id]["val"] = f"{mins}:{secs:02d} {record['metric_suffix']}".strip()
                    calculated_prs[rec_id]["date"] = str(numeric_df.loc[min_idx, 'Date'])
                        
            elif calc_mode == "peak_year":
                valid_df['Temp_Year'] = valid_df['Parsed_Year_Date'].dt.year
                valid_df[col_target] = _clean_numeric_series(valid_df[col_target])
                valid_df = valid_df.dropna(subset=['Temp_Year', col_target])
                if not valid_df.empty:
                    ann_sums = valid_df.groupby('Temp_Year')[col_target].sum()
                    if not ann_sums.empty:
                        if target_year is not None:
                            val_out = ann_sums.get(int(target_year), 0.0)
                            calculated_prs[rec_id]["val"] = f"{float(val_out):.1f} {record['metric_suffix']}".strip()
                            calculated_prs[rec_id]["date"] = f"Year: {int(target_year)}"
                        else:
                            calculated_prs[rec_id]["val"] = f"{float(ann_sums.max()):.1f} {record['metric_suffix']}".strip()
                            calculated_prs[rec_id]["date"] = f"Year: {int(ann_sums.idxmax())}"

            elif calc_mode == "peak_week":
                # Tracks highest weekly volume using math-safe ISO calendar aggregations
                valid_df['Temp_ISO_Year'] = valid_df['Parsed_Year_Date'].dt.isocalendar().year
                valid_df['Temp_ISO_Week'] = valid_df['Parsed_Year_Date'].dt.isocalendar().week
                valid_df[col_target] = _clean_numeric_series(valid_df[col_target])
                valid_df = valid_df.dropna(subset=['Temp_ISO_Year', 'Temp_ISO_Week', col_target])
                if not valid_df.empty:
                    weekly_sums = valid_df.groupby(['Temp_ISO_Year', 'Temp_ISO_Week'])[col_target].sum().reset_index()
                    if not weekly_sums.empty:
                        max_idx = weekly_sums[col_target].idxmax()
                        peak_row = weekly_sums.loc[max_idx]
                        calculated_prs[rec_id]["val"] = f"{float(peak_row[col_target]):.1f} {record['metric_suffix']}".strip()
                        calculated_prs[rec_id]["date"] = f"Year {int(peak_row['Temp_ISO_Year'])}, Wk {int(peak_row['Temp_ISO_Week'])}"
            
        except Exception:
            pass  # Silent error execution context for background processing safety
                
    return calculated_prs

def compile_all_award_instances(df_logs):
    """Completely data-driven milestone harvester. ZERO hardcoded logic."""
    import arena_tournaments_config as arena_cfg
    instances = []
    if df_logs is None or df_logs.empty:
        return pd.DataFrame(columns=["award_code", "date", "metric", "type", "details"])
        
    df = df_logs.copy()
    df['Date_Parsed'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df[df['Date_Parsed'].notna()]

    for idx, row in df.iterrows():
        lbl = row['Date_Parsed'].strftime("%Y-%m-%d")
        try:
            raw_dist = row.get('Display_Distance', row.get('Distance (Miles)', 0.0))
            dist_val = f"{float(raw_dist):.2f} Mi"
        except (ValueError, TypeError):
            dist_val = "0.00 Mi"
            
        duration_val = str(row.get('Duration', 'N/A'))
        try:
            raw_pace = row.get('Avg_Pace', row.get('pace', 0.0))
            if isinstance(raw_pace, (int, float)) and raw_pace > 0:
                p_mins = int(raw_pace // 60)
                p_secs = int(round(raw_pace % 60))
                pace_val = f"{p_mins}:{p_secs:02d} /mi"
            else:
                pace_val = f"{raw_pace} /mi"
        except Exception:
            pace_val = "N/A"
            
        detail_string = f"⏱️ Duration: {duration_val} | 📐 Distance: {dist_val} | ⚡ Pace: {pace_val}"
        raw_rewards_list = row.get('earned_patches', row.get('earned_rewards', []))
        
        if isinstance(raw_rewards_list, str):
            cleaned_str = raw_rewards_list.strip()
            if cleaned_str:
                try:
                    raw_rewards_list = json.loads(cleaned_str)
                except json.JSONDecodeError:
                    try:
                        raw_rewards_list = ast.literal_eval(cleaned_str)
                    except Exception:
                        raw_rewards_list = []
            else:
                raw_rewards_list = []
        
        if isinstance(raw_rewards_list, list):
            for award_node in raw_rewards_list:
                if not isinstance(award_node, dict):
                    continue
                award_id = award_node.get('id', '')
                award_name = award_node.get('name', 'Core Milestone Element')
                award_icon = award_node.get('icon', '🛡️')
                award_type = award_node.get('type', 'patch')
                metric_lbl = award_node.get('metric_label', f"{award_icon} {award_name} Verified")
                if award_id:
                    lookup_code = f"{award_type}_{award_id}"
                    instances.append({
                        "award_code": lookup_code, 
                        "date": lbl,
                        "metric": metric_lbl,
                        "type": award_type,
                        "details": detail_string
                    })

    return pd.DataFrame(instances)


def calculate_athlete_rpg_level(df_instances):
    """Calculates total accumulated XP and maps the score into our rank matrix."""
    import metrics_config as cfg
    import personal_records_config as pr_cfg
    fallback_title = cfg.ATHLETIC_TIERS[0]["title"] if getattr(cfg, 'ATHLETIC_TIERS', None) else "Contender"
    if df_instances is None or df_instances.empty:
        return 1, 0, 0, fallback_title

    total_xp = 0
    for _, row in df_instances.iterrows():
        code = row.get("award_code", "")
        tier_key = "emerald"
        if "miles" in code:
            match = next((a for a in getattr(cfg, 'WEEKLY_MILEAGE_REWARDS', []) if f"weekly_miles_{a.get('miles')}" == code), None)
            if match: tier_key = match.get("tier", tier_key)
        elif "climb" in code:
            match = next((a for a in getattr(cfg, 'WEEKLY_ELEVATION_REWARDS', []) if f"weekly_climb_{a.get('climb_ft')}" == code), None)
            if match: tier_key = match.get("tier", tier_key)
        elif "patch" in code:
            match = next((p for p in getattr(pr_cfg, 'DISPLAY_REWARDS_REGISTRY', []) if p.get("code") == code), None)
            if match: tier_key = match.get("tier", tier_key)
            
        registry = getattr(cfg, 'GEM_TIER_REGISTRY', {})
        total_xp += registry.get(tier_key, {"xp": 10})["xp"]

    threshold = getattr(cfg, 'XP_PER_LEVEL_THRESHOLD', 100)
    computed_level = (total_xp // threshold) + 1
    xp_in_level = total_xp % threshold
    progress_pct = min(int((xp_in_level / threshold) * 100), 100)
    
    division_title = cfg.ATHLETIC_TIERS[-1]["title"] if getattr(cfg, 'ATHLETIC_TIERS', None) else "Elite"
    for tier in getattr(cfg, 'ATHLETIC_TIERS', []):
        if computed_level <= tier.get("max_lvl", 0):
            division_title = tier.get("title", division_title)
            break
            
    return computed_level, xp_in_level, progress_pct, division_title


def check_streak_defense_status(df_logs):
    """
    Checks chronological consistency. Calculates continuous day clusters 
    and outputs a risk status indicator based on last known activity dates.
    """
    if df_logs is None or df_logs.empty:
        return "Stable", 0
        
    try:
        df_copy = df_logs.copy()
        df_copy['Parsed_Date'] = pd.to_datetime(df_copy['Date'], errors='coerce').dt.date
        unique_dates = sorted(df_copy['Parsed_Date'].dropna().unique(), reverse=True)
        
        if not unique_dates:
            return "Stable", 0
            
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        
        # If the most recent active log drops below yesterday, streak vectors cool down to 0
        if unique_dates[0] != today and unique_dates[0] != yesterday:
            return "Vulnerable", 0
            
        streak_count = 1
        for i in range(len(unique_dates) - 1):
            diff = unique_dates[i] - unique_dates[i+1]
            if diff.days == 1:
                streak_count += 1
            elif diff.days > 1:
                break  # The continuous link sequence was broken
                
        status = "Fortified" if streak_count >= 5 else "Stable"
        return status, streak_count
    except Exception:
        return "Stable", 0

def calculate_current_week_metrics(df_logs):
    """
    Identifies metrics matching the current localized ISO calendar week 
    to drive progress bars and requirement lists.
    """
    if df_logs is None or df_logs.empty:
        return 0.0, 0.0
        
    try:
        df_copy = df_logs.copy()
        df_copy['Parsed_Date'] = pd.to_datetime(df_copy['Date'], errors='coerce')
        df_copy = df_copy.dropna(subset=['Parsed_Date'])
        
        now = datetime.datetime.now()
        current_iso_year = now.isocalendar()[0]
        current_iso_week = now.isocalendar()[1]
        
        # Squeeze dataframe records into the active week boundaries
        week_df = df_copy[
            (df_copy['Parsed_Date'].dt.isocalendar().year == current_iso_year) & 
            (df_copy['Parsed_Date'].dt.isocalendar().week == current_iso_week)
        ]
        
        miles_col = next((c for c in week_df.columns if any(x in c.lower() for x in ["dist", "mile"])), "Display_Distance")
        climb_col = next((c for c in week_df.columns if any(x in c.lower() for x in ["ascent", "elev", "climb"])), "Total_Ascent")
        
        total_miles = pd.to_numeric(week_df[miles_col], errors='coerce').sum() if miles_col in week_df.columns else 0.0
        total_climb = pd.to_numeric(week_df[climb_col], errors='coerce').sum() if climb_col in week_df.columns else 0.0
        
        return float(total_miles), float(total_climb)
    except Exception:
        return 0.0, 0.0


def evaluate_coveted_targets_status(df_logs, target_year=None):
    """Dynamically parses and checks goals across all registered items in configuration, with year filtering."""
    import metrics_config as cfg
    coveted_status = {}
    targets_registry = getattr(cfg, 'COVETED_TARGETS', {})
    for key in targets_registry.keys():
        coveted_status[key] = {"status": "Locked", "progress_label": "0%"}
    if df_logs is None or df_logs.empty or not targets_registry:
        return coveted_status

    clean_df = df_logs.copy()
    clean_df['Parsed_Date'] = pd.to_datetime(clean_df['Date'], errors='coerce')
    if target_year is not None:
        clean_df = clean_df[clean_df['Parsed_Date'].dt.year == int(target_year)]

    max_single_run = 0.0
    dist_col = "Display_Distance" if "Display_Distance" in clean_df.columns else ("Distance (Miles)" if "Distance (Miles)" in clean_df.columns else "distance")
    if dist_col in clean_df.columns:
        valid_dist = _clean_numeric_series(clean_df[dist_col]).dropna()
        if not valid_dist.empty:
            max_single_run = float(valid_dist.max())

    for key, target_node in targets_registry.items():
        target_dist = target_node.get("distance_required", float('inf'))
        if max_single_run >= target_dist:
            coveted_status[key] = {"status": "Unlocked", "progress_label": f"{max_single_run:.1f} Mi Logged"}
        else:
            pct = (max_single_run / target_dist) if target_dist > 0 else 0.0
            coveted_status[key] = {"status": "Locked", "progress_label": f"{pct:.0%} ({max_single_run:.1f}/{target_dist:.1f} Mi)"}
    return coveted_status


def evaluate_arena_tournament_medals(df_logs, target_year=None):
    """Scans and increments matches contested dynamically against the full configurations registry, with year filtering."""
    import arena_tournaments_config as arena_cfg
    arena_status = {}
    tournaments_registry = getattr(arena_cfg, 'ARENA_TOURNAMENTS_REGISTRY', {})
    for k in tournaments_registry.keys():
        arena_status[k] = {"count": 0, "status_label": "LOCKED MATCH"}
    if df_logs is None or df_logs.empty or not tournaments_registry:
        return arena_status
        
    clean_df = df_logs.copy()
    clean_df['Parsed_Date'] = pd.to_datetime(clean_df['Date'], errors='coerce')
    if target_year is not None:
        clean_df = clean_df[clean_df['Parsed_Date'].dt.year == int(target_year)]
        
    dist_col = "Display_Distance" if "Display_Distance" in clean_df.columns else ("Distance (Miles)" if "Distance (Miles)" in clean_df.columns else "distance")
    elev_col = "Total_Ascent" if "Total_Ascent" in clean_df.columns else ("Elevation (ft)" if "Elevation (ft)" in clean_df.columns else "elevation")

    clean_df['Resolved_Dist'] = _clean_numeric_series(clean_df[dist_col]).fillna(0.0) if dist_col in clean_df.columns else 0.0
    clean_df['Resolved_Ascent'] = _clean_numeric_series(clean_df[elev_col]).fillna(0.0) if elev_col in clean_df.columns else 0.0

    for key, config_node in tournaments_registry.items():
        matches = clean_df.copy()
        if "target_distance" in config_node:
            matches = matches[matches['Resolved_Dist'] >= float(config_node["target_distance"])]
        if "target_elevation_ft" in config_node:
            matches = matches[matches['Resolved_Ascent'] >= float(config_node["target_elevation_ft"])]
        count = len(matches)
        if count > 0:
            suffix = config_node.get("status_suffix", "Contested")
            status_str = f"x{count} {suffix}"
        else:
            status_str = "LOCKED MATCH"
        arena_status[key] = {"count": count, "status_label": status_str}
    return arena_status

