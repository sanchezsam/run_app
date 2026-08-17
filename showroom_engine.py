import pandas as pd
import numpy as np
import datetime
import re
import metrics_config as cfg
import personal_records_config as pr_cfg
import arena_tournaments_config as arena_cfg
from error_utils import get_logger

logger = get_logger(__name__)

# ==============================================================================
# ⚙️ TROPHY ENGINE: CORE MATHEMATICAL ENGINE PIPELINE (BLOCK 1)
# ==============================================================================

def sanitize_json_history_logs(raw_history_list):
    """Safely extracts dictionary payloads out of a mixed string/object list.
    Filters out string-only elements and converts metric strings into pure decimals.
    """
    if not raw_history_list or not isinstance(raw_history_list, list):
        return pd.DataFrame()
        
    sanitized_records = []
    
    for item in raw_history_list:
        # Ignore raw text combat or racing loss string logs to prevent dictionary crashes
        if not isinstance(item, dict):
            continue
            
        # Guarantee a baseline valid Date anchor coordinate exists
        date_val = item.get('Date', item.get('date', None))
        if not date_val:
            continue
            
        record = {
            'Date': str(date_val),
            'Display_Distance': 0.0,
            'Avg_Pace': 0.0,
            'Total_Ascent': 0.0,
            'Five_K_Time': item.get('Five_K_Time', item.get('5k_time', ''))
        }
        
        # 1. Extract Distance Field
        dist = item.get('Distance (Miles)', item.get('Display_Distance', item.get('distance', 0.0)))
        try:
            record['Display_Distance'] = float(dist)
        except (ValueError, TypeError):
            pass
            
        # 2. Extract Pace Field
        pace = item.get('pace', item.get('Avg_Pace', 0.0))
        try:
            record['Avg_Pace'] = float(pace)
        except (ValueError, TypeError):
            pass
            
        # 3. Extract Elevation Gain & Strip text strings like "+865.5 ft"
        elev = item.get('Elevation (ft)', item.get('Total_Ascent', item.get('elevation', 0.0)))
        if isinstance(elev, str):
            # Regex extracts decimal or integers out of the alphanumeric text payload
            cleaned_elev = "".join(re.findall(r"[-+]?\d*\.\d+|\d+", elev))
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


def calculate_personal_records(df_logs):
    """Calculates all career records dynamically by scanning personal_records_config maps."""
    calculated_prs = {}
    
    for record in pr_cfg.PERSONAL_RECORDS_REGISTRY:
        rec_id = record["id"]
        calculated_prs[rec_id] = {"val": record["fallback_value"], "date": record["fallback_date"]}
        
        if df_logs is None or df_logs.empty:
            continue
            
        col_target = record["data_column"]
        if col_target not in df_logs.columns:
            continue
            
        try:
            calc_mode = record["calculation_type"]
            valid_df = df_logs[df_logs[col_target].notna()]
            
            if calc_mode == "max" and not valid_df.empty:
                max_idx = valid_df[col_target].idxmax()
                calculated_prs[rec_id]["val"] = f"{float(valid_df.loc[max_idx, col_target]):.2f} {record['metric_suffix']}"
                calculated_prs[rec_id]["date"] = valid_df.loc[max_idx, 'Date']
                    
            elif calc_mode == "min" and not valid_df.empty:
                numeric_df = valid_df[pd.to_numeric(valid_df[col_target], errors='coerce') > 0]
                if not numeric_df.empty:
                    min_idx = numeric_df[col_target].idxmin()
                    calculated_prs[rec_id]["val"] = f"{numeric_df.loc[min_idx, col_target]} {record['metric_suffix']}".strip()
                    calculated_prs[rec_id]["date"] = numeric_df.loc[min_idx, 'Date']
                        
            elif calc_mode == "min_pace" and not valid_df.empty:
                numeric_df = valid_df[valid_df[col_target] > 0]
                if not numeric_df.empty:
                    min_idx = numeric_df[col_target].idxmin()
                    raw_pace = numeric_df.loc[min_idx, col_target]
                    mins = int(raw_pace)
                    secs = int((raw_pace - mins) * 60)
                    calculated_prs[rec_id]["val"] = f"{mins}:{secs:02d} {record['metric_suffix']}"
                    calculated_prs[rec_id]["date"] = numeric_df.loc[min_idx, 'Date']
                        
            elif calc_mode == "peak_year":
                valid_df['Temp_Year'] = pd.to_datetime(valid_df['Date'], errors='coerce').dt.year
                ann_sums = valid_df.groupby('Temp_Year')[col_target].sum()
                if not ann_sums.empty:
                    calculated_prs[rec_id]["val"] = f"{float(ann_sums.max()):.1f} {record['metric_suffix']}"
                    calculated_prs[rec_id]["date"] = f"Year: {int(ann_sums.idxmax())}"
        except Exception:
            logger.warning('Could not compute personal record %r from the activity table', rec_id, exc_info=True)
            
    return calculated_prs




def compile_all_award_instances(df_logs):
    """
    Completely data-driven milestone harvester. ZERO hardcoded logic.
    Directly extracts any pre-calculated award structures (Patches, Medals, 
    Ribbons, Trophies, and Milestones) embedded inside the save_file.
    """
    instances = []
    if df_logs is None or df_logs.empty:
        return pd.DataFrame(columns=["award_code", "date", "metric", "type", "details"])
        
    df = df_logs.copy()
    df['Date_Parsed'] = pd.to_datetime(df['Date'], errors='coerce')
    df = df[df['Date_Parsed'].notna()]

    # ==============================================================================
    # 🧬 METADATA HARVESTER LOOP: Extracts any asset type dynamically
    # ==============================================================================
    for idx, row in df.iterrows():
        lbl = row['Date_Parsed'].strftime("%Y-%m-%d")
        
        # Structure core verification parameters for the drilldown ledger
        dist_val = f"{row.get('Display_Distance', row.get('Distance (Miles)', 0.0)):.2f} Mi"
        duration_val = str(row.get('Duration', 'N/A'))
        pace_val = f"{row.get('Avg_Pace', row.get('pace', 0.0)):.2f} min/mi"
        detail_string = f"⏱️ Duration: {duration_val} | 📐 Distance: {dist_val} | ⚡ Pace: {pace_val}"
        
        # Scan your history log row for any nested list array matrices of achievements
        # This single look covers patches, trophies, ribbons, or milestone items
        raw_rewards_list = row.get('earned_patches', row.get('earned_rewards', []))
        
        if isinstance(raw_rewards_list, list):
            for award_node in raw_rewards_list:
                award_id = award_node.get('id', '')
                award_name = award_node.get('name', 'Core Milestone Element')
                award_icon = award_node.get('icon', '🛡️')
                award_type = award_node.get('type', 'patch') # patch, ribbon, medal, trophy
                metric_lbl = award_node.get('metric_label', f"{award_icon} {award_name} Verified")
                
                if award_id:
                    # Automatically structures the target reference lookup key
                    # Matches your standard formatting, e.g., patch_rabbit, trophy_century
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
    if df_instances is None or df_instances.empty:
        fallback_title = cfg.ATHLETIC_TIERS[0]["title"] if cfg.ATHLETIC_TIERS else "Contender"
        return 1, 0, 0, fallback_title

    total_xp = 0
    for _, row in df_instances.iterrows():
        code = row["award_code"]
        tier_key = "emerald"
        
        if "miles" in code:
            match = next((a for a in cfg.WEEKLY_MILEAGE_REWARDS if f"weekly_miles_{a['miles']}" == code), None)
            if match: tier_key = match["tier"]
        elif "climb" in code:
            match = next((a for a in cfg.WEEKLY_ELEVATION_REWARDS if f"weekly_climb_{a['climb_ft']}" == code), None)
            if match: tier_key = match["tier"]
        elif "patch" in code:
            match = next((p for p in pr_cfg.DISPLAY_REWARDS_REGISTRY if p["code"] == code), None)
            if match: tier_key = match["tier"]
            
        total_xp += cfg.GEM_TIER_REGISTRY.get(tier_key, {"xp": 10})["xp"]

    computed_level = (total_xp // cfg.XP_PER_LEVEL_THRESHOLD) + 1
    xp_in_level = total_xp % cfg.XP_PER_LEVEL_THRESHOLD
    progress_pct = min(int((xp_in_level / cfg.XP_PER_LEVEL_THRESHOLD) * 100), 100)
    
    division_title = cfg.ATHLETIC_TIERS[-1]["title"] if cfg.ATHLETIC_TIERS else "Elite"
    for tier in cfg.ATHLETIC_TIERS:
        if computed_level <= tier["max_lvl"]:
            division_title = tier["title"]
            break
            
    return computed_level, xp_in_level, progress_pct, division_title


def check_streak_defense_status(df_logs):
    if df_logs is None or df_logs.empty:
        return "stable", 0
    try:
        last_date = pd.to_datetime(df_logs['Date']).max()
        days_elapsed = (datetime.datetime.now() - last_date).days
        if days_elapsed > cfg.DEFENSE_WINDOW_DAYS:
            return "decaying", days_elapsed
    except Exception:
        logger.warning('Could not evaluate streak defense status, reporting it as stable', exc_info=True)
    return "stable", 0


def calculate_current_week_metrics(df_logs):
    if df_logs is None or df_logs.empty:
        return 0.0, 0.0
    try:
        df = df_logs.copy()
        df['Date_Parsed'] = pd.to_datetime(df['Date'], errors='coerce')
        today = datetime.datetime.now()
        curr_year, curr_week, _ = today.isocalendar()
        
        cw_rows = df[(df['Date_Parsed'].dt.isocalendar().year == curr_year) & (df['Date_Parsed'].dt.isocalendar().week == curr_week)]
        return float(cw_rows['Display_Distance'].sum()), float(cw_rows['Total_Ascent'].sum())
    except Exception:
        logger.warning('Could not compute current-week distance and ascent totals, reporting zeroes', exc_info=True)
        return 0.0, 0.0


def evaluate_coveted_targets_status(df_logs):
    coveted_status = {}
    for key in cfg.COVETED_TARGETS.keys():
        coveted_status[key] = {"status": "Locked", "progress_label": "0%"}
        
    if df_logs is None or df_logs.empty:
        return coveted_status

    max_single_run = df_logs['Display_Distance'].max() if 'Display_Distance' in df_logs.columns else 0.0
    target_dist = cfg.COVETED_TARGETS["coveted_century_mount"]["distance_required"]
    if max_single_run >= target_dist:
        coveted_status["coveted_century_mount"] = {"status": "Unlocked", "progress_label": f"{max_single_run:.1f} Mi Logged"}
    else:
        pct = (max_single_run / target_dist)
        coveted_status["coveted_century_mount"] = {"status": "Locked", "progress_label": f"{pct:.0%} ({max_single_run:.1f}/{target_dist:.1f} Mi)"}

    return coveted_status


def evaluate_arena_tournament_medals(df_logs):
    arena_status = {}
    for k in arena_cfg.ARENA_TOURNAMENTS_REGISTRY.keys():
        arena_status[k] = {"count": 0, "status_label": "LOCKED MATCH"}
        
    if df_logs is None or df_logs.empty:
        return arena_status
        
    clash_cfg = arena_cfg.ARENA_TOURNAMENTS_REGISTRY["coliseum_sprint_clash"]
    matches = df_logs[(df_logs['Display_Distance'] >= clash_cfg["target_distance"])]
    arena_status["coliseum_sprint_clash"] = {"count": len(matches), "status_label": f"x{len(matches)} Contested" if not matches.empty else "LOCKED MATCH"}
        
    vert_cfg = arena_cfg.ARENA_TOURNAMENTS_REGISTRY["alpine_vert_challenge"]
    high_climbs = df_logs[df_logs['Total_Ascent'] >= vert_cfg["target_elevation_ft"]]
    arena_status["alpine_vert_challenge"] = {"count": len(high_climbs), "status_label": f"x{len(high_climbs)} Climbed" if not high_climbs.empty else "LOCKED MATCH"}
        
    return arena_status

