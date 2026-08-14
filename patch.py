import json
import os

FILENAME = "save_file.json"

def safely_inject_final_metric():
    if not os.path.exists(FILENAME):
        print(f"Error: Could not locate '{FILENAME}' in this directory.")
        return

    # 1. Read existing data safely
    try:
        with open(FILENAME, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Critical Error: '{FILENAME}' has broken formatting or was cut off: {e}")
        print("Fix the trailing brackets in your editor before running this script.")
        return

    # 2. Check for existence to prevent overwriting your progress
    if "final_metric_data" in data:
        print("Database Verification: 'final_metric_data' container is already safely installed.")
        return

    print("Target Found. Initializing surgical integration of 'final_metric_data'...")

    # 3. Create the clean container right alongside your levels and gear
    data["final_metric_data"] = {
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

    # 4. Safe write back, preserving all your original game variables
    try:
        with open(FILENAME, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print("Success! 'final_metric_data' has been seamlessly added without touching other stats.")
    except Exception as e:
        print(f"Error writing to file: {e}")

if __name__ == "__main__":
    safely_inject_final_metric()

