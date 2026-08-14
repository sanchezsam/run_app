# run_full_system.py
import os
import json
from upload_ui import process_and_award_metrics

try:
    from services import parse_garmin_fit
    HAS_FIT_PARSER = True
except ImportError:
    HAS_FIT_PARSER = False

SAVE_FILE = "save_file.json" 
DATA_DIR = "data"
#YEARS = ["2022", "2023", "2024", "2025", "2026"]
YEARS = ["2022"]

def initialize_and_run_upload():
    print("==================================================")
    print("🛠️ RUNNER DATABASE AUTO-GENERATION & BATCH SYSTEM")
    print("==================================================")

    # 1. AUTO-MANUFACTURING: If missing, create a fresh template player profile
    if not os.path.exists(SAVE_FILE):
        print(f"📝 {SAVE_FILE} not found. Manufacturing a fresh character template layout...")
        profile = {
            "name": "Athlete",
            "bodyweight": 180,
            "level": 1,
            "total_xp": 0,
            "running_level": 1,
            "vo2_max": 40.0,
            "avg_heart_rate": 150,
            "resting_heart_rate": 65,
            "lifetime_elevation_gain": 0.0,
            "cadence_history": [],
            "elevation_milestone_history": [],
            "deep_rem_streak": 0,
            "stat_points": 0,
            "gold": 0,
            "inventory": [],
            "equipped_gear": {},
            "registered_races": [],
            "boss_wins": 0,
            "fatigue": 0,
            "days_tracked": 0,
            "synced_garmin_activities": [],
            "history_logs": [],
            "unlocked_badges": [],
            "daily_miles": {},
            "base_xp": 100,
            "exponent": 1.5,
            "last_distance": 0.0,
            "last_pace": "00:00",
            "boss_clears": 0,
            "boss_levels": {},
            "coliseum_history": [],
            "stamina_xp": 0,
            "agility_xp": 0,
            "power_xp": 0
        }
    else:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            profile = json.load(f)

    # Inject the metric tracking object container safely
    if "final_metric_data" not in profile:
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
        
    # Write the base profile down so the file path officially exists to write data records into
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=4, ensure_ascii=False)
    print(f"✅ Save File Link Secured at: '{SAVE_FILE}'")

    # 2. Gather history files
    collected_files = []
    for year in YEARS:
        year_path = os.path.join(DATA_DIR, year)
        if not os.path.exists(year_path):
            continue
        for filename in os.listdir(year_path):
            if filename.endswith(".json") or filename.endswith(".fit"):
                collected_files.append((filename, os.path.join(year_path, filename)))

    collected_files.sort(key=lambda x: x)
    total_files = len(collected_files)
    print(f"📋 Found {total_files} runs ready for complete ingestion.\n")

    # 3. Stream data file loops
    success_count = 0
    for idx, (filename, file_path) in enumerate(collected_files):
        print(f"[{idx + 1}/{total_files}] Ingesting: {filename}...")
        try:
            if filename.endswith(".json"):
                with open(file_path, "r", encoding="utf-8") as f:
                    run_payload = json.load(f)
            elif filename.endswith(".fit"):
                if HAS_FIT_PARSER:
                    run_payload = parse_garmin_fit(file_path)
                else:
                    continue

            if not run_payload:
                continue

            process_and_award_metrics(run_payload)
            success_count += 1
        except Exception as e:
            print(f"   ❌ Error on {filename}: {e}")
            continue

    # 4. Summary Readback report block
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        final_profile = json.load(f)
        m_data = final_profile.get("final_metric_data", {})

    print("\n==================================================")
    print("🏁 INGESTION COMPLETE: DATABASE TOTALS REGENERATED")
    print("==================================================")
    print(f"✅ Successfully Processed: {success_count} / {total_files} Files")
    print(f"📊 Final Lifelong Mileage Odometer: {m_data.get('lifetime_odometer_miles', 0.0):,} Miles")
    print(f"🏔 Montaineer Total Elevation Climb: {final_profile.get('lifetime_elevation_gain', 0.0):,} Vert Feet")
    print(f"🍕 Metabolic Total Energy Scorched: {m_data.get('lifetime_calories_burned', 0):,} kcal")
    print("==================================================")

if __name__ == "__main__":
    initialize_and_run_upload()

