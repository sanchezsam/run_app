# metrics_processor.py
import json
import os
from metrics_config import FINAL_METRIC_CONFIG

SAVE_FILE = "save_file.json"

def clean_elevation_string(elev_str: str) -> int:
    """Strips formatting symbols '+', 'ft', and whitespace to return a clean integer."""
    try:
        cleaned = elev_str.replace("+", "").replace("ft", "").strip()
        return int(float(cleaned))
    except (ValueError, AttributeError):
        return 0

def decimal_pace_to_seconds(decimal_pace: float) -> int:
    """Converts a decimal pace float (like 8.82) into raw total seconds."""
    try:
        minutes = int(decimal_pace)
        seconds = int(round((decimal_pace - minutes) * 60))
        return (minutes * 60) + seconds
    except (ValueError, TypeError):
        return 0

def process_and_award_metrics(new_run_log: dict):
    """
    Main evaluation pipeline. Processes incoming run payloads, updates 
    profile statistics counters, and appends earned trophies.
    """
    if not os.path.exists(SAVE_FILE):
        return
        
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        profile = json.load(f)
        
    # Safeguard initialization if user hasn't run the migration snippet yet
    if "final_metric_data" not in profile:
        return
        
    m_data = profile["final_metric_data"]
    
    # --- A. DATA CONVERSION EXTRACTORS ---
    run_distance = float(new_run_log.get("Distance (Miles)", 0.0))
    run_pace_seconds = decimal_pace_to_seconds(new_run_log.get("pace", 0.0))
    run_elevation = clean_elevation_string(new_run_log.get("Elevation (ft)", "0"))
    
    # Extract string values from the nested splits dictionary array objects
    raw_splits_array = new_run_log.get("splits", [])
    pace_splits_list = [item.get("pace", "") for item in raw_splits_array if "pace" in item]
    
    final_mile_str = pace_splits_list[-1] if pace_splits_list else ""
    
    # --- B. EXECUTE MATH HELPERS ---
    # Convert overall decimal minutes pace to standard 'MM:SS' for our kick calculator
    avg_min = int(new_run_log.get("pace", 0))
    avg_sec = int(round((new_run_log.get("pace", 0) - avg_min) * 60))
    avg_pace_str = f"{avg_min:02d}:{avg_sec:02d}"
    
    final_kick_percent = calculate_final_kick(avg_pace_str, final_mile_str)
    split_variance = calculate_split_variance(pace_splits_list, run_distance)
    
    # Create temporary payload object to evaluate against metrics_config setup mappings
    compiled_run_metrics = {
        "average_pace_seconds": run_pace_seconds,
        "total_elevation_gain_ft": run_elevation,
        "final_mile_kick_percent": final_kick_percent,
        "total_distance_miles": run_distance,
        "split_variance_seconds": split_variance
        # Note: Pillars 6, 7, 8 will safely bypass for now since they are missing from payload strings
    }
    
    # --- C. TICK UP LIFETIME ODOMETERS & COUNTERS ---
    m_data["lifetime_odometer_miles"] = round(m_data["lifetime_odometer_miles"] + run_distance, 2)
    # Estimate standard average metabolic running burn of 100 kcal per mile for your logs
    run_calories = int(run_distance * 100) 
    m_data["lifetime_calories_burned"] += run_calories
    
    # Update master profile baseline values to sync everything perfectly
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
    # Checking Mileage Loops (Every 500 miles past the 2,000 baseline)
    if m_data["lifetime_odometer_miles"] > 2000:
        extra_miles = m_data["lifetime_odometer_miles"] - 2000
        m_data["trophy_cabinet"]["prestige_loops"]["mileage_loops_count"] = int(extra_miles // mileage_config["loop_increment"])
        
    # Checking Elevation Loops (Every 25k feet past the 100k baseline)
    if profile["lifetime_elevation_gain"] > 100000:
        extra_vert = profile["lifetime_elevation_gain"] - 100000
        m_data["trophy_cabinet"]["prestige_loops"]["elevation_loops_count"] = int(extra_vert // elev_config["loop_increment"])

    # Checking Calorie Loops (Every 25k calories past the 100k baseline)
    if m_data["lifetime_calories_burned"] > 100000:
        extra_cal = m_data["lifetime_calories_burned"] - 100000
        m_data["trophy_cabinet"]["prestige_loops"]["calorie_loops_count"] = int(extra_cal // cal_config["loop_increment"])

    # --- F. WRITE REWARDS SAFELY BACK TO DATABASE ---
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=4, ensure_ascii=False)
    print("Ledger Complete: Lifelong odometers and award cases refreshed successfully.")

