# verify_patch.py
import json
import os

def test_database_injection():
    print("==================================================")
    print("🔍 RUNNING BATCH UTILITY PATCH INTEGRITY CHECK")
    print("==================================================")
    
    save_path = "save_file.json"
    
    if not os.path.exists(save_path):
        print(f"❌ Verification Failed: '{save_path}' could not be located.")
        print("💡 Suggestion: Go to the Streamlit UI and click 'Synchronize' first.")
        return

    try:
        with open(save_path, "r", encoding="utf-8") as f:
            db_data = json.load(f)
            
        logs = db_data.get("history_logs", [])
        
        if not logs:
            print("❌ Verification Failed: 'history_logs' array is empty inside your save file.")
            return
            
        # Target keys we injected via the patch
        target_keys = ["Duration Time", "Calculated Pace", "Climb Ascent"]
        latest_record = logs[-1]  # Inspect the most recent entry
        
        print(f"📦 Total Records Synced: {len(logs)}")
        print(f"📅 Inspecting Latest Entry Date: {latest_record.get('Date', 'N/A')}")
        print("--------------------------------------------------")
        
        missing_keys = []
        for key in target_keys:
            if key in latest_record:
                print(f"✅ Key Found!  ->  \"{key}\": \"{latest_record[key]}\"")
            else:
                missing_keys.append(key)
                print(f"❌ Key Missing ->  \"{key}\"")
                
        print("--------------------------------------------------")
        if not missing_keys:
            print("🎉 SUCCESS: All telemetry patch metrics are successfully saving to JSON!")
        else:
            print(f"⚠️ WARNING: Missing keys detected: {missing_keys}")
            
    except Exception as e:
        print(f"💥 Error reading storage layouts during validation: {e}")

if __name__ == "__main__":
    test_database_injection()

