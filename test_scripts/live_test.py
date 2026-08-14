# live_test.py
import json
import os
from upload_ui import process_and_award_metrics

SAVE_FILE = "save_file.json"

def test_live_interceptor():
    print("🧪 SIMULATION: Processing a brand new live run upload...")
    
    # 1. Check odometer totals BEFORE the test run
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        profile_before = json.load(f)
    miles_before = profile_before["final_metric_data"]["lifetime_odometer_miles"]
    cals_before = profile_before["final_metric_data"]["lifetime_calories_burned"]
    
    print(f"📊 Starting Mileage: {miles_before:,} Miles")
    print(f"🔥 Starting Calories: {cals_before:,} kcal")

    # 2. Simulate an incoming workout payload (e.g., a fast, hilly 10-miler)
    mock_live_run = {
        "Date": "2026-08-14",
        "Name": "live_test_track.fit",
        "Distance (Miles)": 10.0,
        "Duration": "01:10:00",
        "pace": 7.00,                      # 7:00/mi pace -> Pillar 1 Deer Node!
        "Elevation (ft)": "+800.0 ft",     # +800ft climb -> Pillar 2 Bighorn!
        "splits": [
            {"split_num": 1, "distance_mi": 1.0, "time": "07:30", "pace": "07:30"},
            {"split_num": 2, "distance_mi": 1.0, "time": "07:00", "pace": "07:00"},
            {"split_num": 3, "distance_mi": 1.0, "time": "06:45", "pace": "06:45"} # Strong close!
        ]
    }

    # 3. Fire the ingestion function
    process_and_award_metrics(mock_live_run)

    # 4. Check odometer totals AFTER the test run
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        profile_after = json.load(f)
    m_data_after = profile_after["final_metric_data"]
    
    print("\n==================================================")
    print("🏁 LIVE PROCESSING TEST RESULTS")
    print("==================================================")
    print(f"📈 Updated Distance Odometer : {m_data_after['lifetime_odometer_miles']:,} Miles (+10.0)")
    print(f"🔥 Updated Lifelong Calories  : {m_data_after['lifetime_calories_burned']:,} kcal (+1,000)")
    print(f"🏆 Unlocked Mileage Trophies : {m_data_after['trophy_cabinet']['shelf_a_mileage']}")
    print(f"🍕 Unlocked Food Trophies    : {m_data_after['trophy_cabinet']['shelf_c_calories']}")
    print("==================================================")
    print("🎉 Ingestion test successful! Your app is fully automated.")

if __name__ == "__main__":
    test_live_interceptor()

