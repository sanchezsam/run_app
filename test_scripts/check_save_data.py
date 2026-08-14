# check_save_data.py
import json
import os

SAVE_FILE = "save_file.json"

def diagnose_database():
    print("==================================================")
    print("🔬 RUNNER LEDGER DIAGNOSTIC TOOL")
    print("==================================================")
    
    if not os.path.exists(SAVE_FILE):
        print(f"❌ Error: '{SAVE_FILE}' does not exist in this directory.")
        print(f"Current Directory Contents: {os.listdir('.')}")
        return

    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Critical Error: '{SAVE_FILE}' contains corrupted JSON syntax: {e}")
            return

    # 1. Check Top-Level Metrics Container
    print("✅ File Found and Parsed Successfully!")
    if "final_metric_data" in data:
        m_data = data["final_metric_data"]
        print("\n📈 [METRIC LEDGER CONTENTS]")
        print(f"   • Odometer Miles : {m_data.get('lifetime_odometer_miles')} mi")
        print(f"   • Calorie Bank   : {m_data.get('lifetime_calories_burned')} kcal")
        print(f"   • Mileage Shelf  : {m_data.get('trophy_cabinet', {}).get('shelf_a_mileage')}")
        print(f"   • Calorie Shelf  : {m_data.get('trophy_cabinet', {}).get('shelf_c_calories')}")
    else:
        print("❌ Error: 'final_metric_data' container is missing from this file.")

    # 2. Check Historical Workout Array Length
    history = data.get("history_logs", [])
    print(f"\n🏃 [WORKOUT HISTORY CONTENTS]")
    print(f"   • Total runs saved in history_logs: {len(history)}")
    
    if len(history) > 0:
        print("\n📝 [SAMPLE RUN METRICS KEY CHECK]")
        sample = history[0]
        print(f"   • Available Keys: {list(sample.keys())}")
        print(f"   • Date Value    : {sample.get('Date')}")
        print(f"   • Distance Key  : {sample.get('Distance (Miles)')}")
        print(f"   • Patches Key   : {'earned_patches' in sample} (Should be True)")
    else:
        print("⚠️ Warning: 'history_logs' list is empty. No historical logs are saved inside the file.")
    print("==================================================")

if __name__ == "__main__":
    diagnose_database()

