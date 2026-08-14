# backfill_history.py
import json
import os

# Import the parsing functions we built inside upload_ui.py
from upload_ui import (
    process_and_award_metrics, 
    decimal_pace_to_seconds, 
    clean_elevation_string,
    check_single_run_patches
)

SAVE_FILE = "save_file.json"

def run_historical_backfill():
    if not os.path.exists(SAVE_FILE):
        print(f"Error: Could not locate '{SAVE_FILE}' in this directory.")
        return

    # 1. Open up your database safely
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        profile = json.load(f)

    if "history_logs" not in profile or not profile["history_logs"]:
        print("Verification: No historical runs found inside 'history_logs' to backfill.")
        return

    print(f"Found {len(profile['history_logs'])} historical workouts. Initializing Ledger Backfill...")

    # 2. Reset our counters to zero so we don't accidentally double-count anything
    profile["final_metric_data"] = {
        "lifetime_odometer_miles": 0.0,
        "lifetime_calories_burned": 0,
        "current_streak_tracker": {
            "current_week_runs_count": 0,
            "last_tracked_week_start": "",
            "consecutive_4_run_weeks": 0,
            "consecutive_52_run_weeks": 0
        },
        "trophy_cabinet": {
            "shelf_a_mileage": [],
            "shelf_b_elevation": [],
            "shelf_c_calories": [],
            "prestige_loops": {
                "mileage_loops_count": 0,
                "elevation_loops_count": 0,
                "calorie_loops_count": 0
            }
        },
        "all_time_personal_records": {
            "fastest_1_mile_seconds": 99999,
            "fastest_5k_seconds": 99999,
            "fastest_10k_seconds": 99999,
            "longest_single_run_miles": 0.0
        }
    }
    profile["unlocked_badges"] = []
    profile["lifetime_elevation_gain"] = 0.0

    # 3. Sweep through every single workout in your history array list
    for idx, run_log in enumerate(profile["history_logs"]):
        print(f"Processing run {idx + 1}/{len(profile['history_logs'])}: {run_log.get('Date', 'Unknown Date')}...")
        
        # This function updates odometers, loops shelves, and appends trophies to profile dict
        process_and_award_metrics(run_log)
        
        # Re-read the file state inside our loops to keep our master profile dictionary variable accurate
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            profile = json.load(f)

    print("\n==================================================")
    print("🎉 SUCCESS: HISTORICAL LEDGER BACKFILL COMPLETE! 🎉")
    print("==================================================")
    
    m_data = profile["final_metric_data"]
    print(f"📊 New Lifelong Odometer: {m_data['lifetime_odometer_miles']:,} Miles")
    print(f"🏔️ New Lifelong Vert Climb: {profile['lifetime_elevation_gain']:,} Feet")
    print(f"🍕 New Lifelong Energy Burned: {m_data['lifetime_calories_burned']:,} Calories")
    print(f"🏆 Mileage Trophies Unlocked: {m_data['trophy_cabinet']['shelf_a_mileage']}")
    print(f"🏔️ Elevation Trophies Unlocked: {m_data['trophy_cabinet']['shelf_b_elevation']}")
    print(f"🌮 Calorie Trophies Unlocked: {m_data['trophy_cabinet']['shelf_c_calories']}")
    print("==================================================")
    print("Launch your app now to view your newly populated trophy cabinets!")

if __name__ == "__main__":
    run_historical_backfill()

