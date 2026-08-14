# test_patch_display.py
import json
import os
from upload_ui import process_and_award_metrics

SAVE_FILE = "save_file.json"

def execute_patch_injection_test():
    print("==================================================")
    print("🧪 INITIALIZING CALENDAR PATCH DISPLAY TEST")
    print("==================================================")

    if not os.path.exists(SAVE_FILE):
        print(f"❌ Error: Database '{SAVE_FILE}' missing. Run run_full_system.py first.")
        return

    # 1. Read file state BEFORE the test injection
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        profile = json.load(f)
    
    initial_runs_count = len(profile.get("history_logs", []))
    print(f"📊 Current Calendar Workout Log Count: {initial_runs_count}")

    # 2. Design a mock workout payload that guarantees triggering multiple patches
    #    - 7.50 miles -> Pillar 4 Stride Tracker Badges (👣)
    #    - 6.80 pace (6:48 min/mi) -> Pillar 1 Deer Sprint Nodes (🦌)
    #    - +950 ft climb -> Pillar 2 Bighorn Torque Modules (🐏)
    mock_high_perf_run = {
        "Date": "2022-01-02",              # Overwrites the empty Jan 2nd run with data!
        "Name": "achievement_test_track.fit",
        "Distance (Miles)": 7.50,
        "Duration": "00:51:00",
        "pace": 6.80,                      
        "Elevation (ft)": "+950 ft",       
        "splits": [
            {"split_num": 1, "distance_mi": 1.0, "time": "07:15", "pace": "07:15"},
            {"split_num": 2, "distance_mi": 1.0, "time": "06:55", "pace": "06:55"},
            {"split_num": 3, "distance_mi": 1.0, "time": "06:50", "pace": "06:50"},
            {"split_num": 4, "distance_mi": 1.0, "time": "06:45", "pace": "06:45"},
            {"split_num": 5, "distance_mi": 1.0, "time": "06:40", "pace": "06:40"},
            {"split_num": 6, "distance_mi": 1.0, "time": "06:35", "pace": "06:35"},
            {"split_num": 7, "distance_mi": 1.0, "time": "06:10", "pace": "06:10"}  # Fast closing mile split
        ]
    }

    print("\n📥 Streaming test payload into process_and_award_metrics()...")
    
    # 3. Fire the pipeline directly
    try:
        process_and_award_metrics(mock_high_perf_run)
    except Exception as e:
        print(f"❌ Core Parser Error encountered: {e}")
        return

    # 4. Read back and verify the file payload data structure updates
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        updated_profile = json.load(f)
        
    updated_history = updated_profile.get("history_logs", [])
    
    print("\n==================================================")
    print("🏁 INJECTION VERIFICATION REPORT")
    print("==================================================")
    
    # Locate our injected activity entry
    test_entry = next((run for run in updated_history if run.get("Name") == "achievement_test_track.fit"), None)
    
    if test_entry:
        print("✅ Ingestion Check: Run successfully committed to history_logs array!")
        print(f"📅 Training Target Date : {test_entry.get('Date')}")
        print(f"⚡ Calculated Pace Value: {test_entry.get('pace')} decimal min/mi")
        
        # Check the newly attached single-run patch blocks
        patches = test_entry.get("earned_patches", [])
        extracted_emojis = [p.get("icon") for p in patches]
        print(f"🎽 Earned Badge List    : {extracted_emojis}")
        print(f"✨ Horizontal Row Check : {' '.join(extracted_emojis)}")
    else:
        print("❌ Error: Run processed but failed to append to history_logs container.")
        
    print("==================================================")
    print("Verification complete! Refresh your Streamlit app page layout to see badges live.")

if __name__ == "__main__":
    execute_patch_injection_test()

