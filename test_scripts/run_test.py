# test_upload.py
import json
import os
from upload_ui import process_and_award_metrics

SAVE_FILE = "save_file.json"

def run_upload_test():
    print("🚀 Initializing Live Upload Simulation Test...")
    
    # 1. Create a mock run structure that mirrors your exact dictionary format
    mock_new_run = {
        "Date": "2026-08-14",
        "Name": "test_simulation_activity.fit",
        "Distance (Miles)": 6.50,          # Eligible for Pillar 4 (Stride Tracker)
        "Duration": "00:45:30",
        "pace": 7.00,                      # 7.00 decimal mins = 7:00 pace (Pillar 1 Deer Tier!)
        "Elevation (ft)": "+820.0 ft",     # Pillar 2 (Bighorn Torque Tier!)
        "splits": [
            {"split_num": 1, "distance_mi": 1.0, "time": "07:30", "pace": "07:30"},
            {"split_num": 2, "distance_mi": 1.0, "time": "07:10", "pace": "07:10"},
            {"split_num": 3, "distance_mi": 1.0, "time": "07:05", "pace": "07:05"},
            {"split_num": 4, "distance_mi": 1.0, "time": "07:00", "pace": "07:00"},
            {"split_num": 5, "distance_mi": 1.0, "time": "06:55", "pace": "06:55"},
            {"split_num": 6, "distance_mi": 1.0, "time": "06:40", "pace": "06:40"} # 6:40 close = Pillar 3 kick!
        ]
    }

    # 2. Take a snapshot of the database values before processing
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            before_data = json.load(f).get("final_metric_data", {})
        print(f"📊 Distance before test: {before_data.get('lifetime_odometer_miles', 0.0)} Miles")
    else:
        print("⚠️ Warning: save_file.json not found. Ensure it exists in this folder.")
        return

    print("\n📥 Injecting mock run into process_and_award_metrics()...")
    
    # 3. Fire the ingestion core
    try:
        process_and_award_metrics(mock_new_run)
    except Exception as e:
        print(f"❌ Core Parser Crash: {e}")
        return

    # 4. Read the database back immediately after processing to verify the delta updates
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        after_profile = json.load(f)
        after_data = after_profile.get("final_metric_data", {})

    print("\n==================================================")
    print("🧪 SIMULATION RESULTS VERIFICATION")
    print("==================================================")
    print(f"📈 Updated Distance Odometer : {after_data.get('lifetime_odometer_miles', 0.0)} Miles (+6.5)")
    print(f"🔥 Updated Lifelong Calories  : {after_data.get('lifetime_calories_burned', 0)} kcal (+650)")
    print(f"🏆 Mileage Shelf Unlocks      : {after_data.get('trophy_cabinet', {}).get('shelf_a_mileage', [])}")
    print(f"🍕 Food Burn Shelf Unlocks    : {after_data.get('trophy_cabinet', {}).get('shelf_c_calories', [])}")
    print(f"🎽 Profile Master Badge Inventory: {after_profile.get('unlocked_badges', [])}")
    print("==================================================")
    print("✅ Test execution complete!")

if __name__ == "__main__":
    run_upload_test()

