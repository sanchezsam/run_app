import json
import os

FILE_PATH = "save_file.json"

def inspect_database():
    if not os.path.exists(FILE_PATH):
        print(f"❌ Error: Could not find '{FILE_PATH}' in this directory.")
        return

    print(f"📖 Opening '{FILE_PATH}' for inspection...\n")
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Error: The JSON file formatting is broken and cannot be read at all.")
            print(f"Details: {e}")
            return

    if "history_logs" not in data:
        print("ℹ️ No 'history_logs' section found in the file.")
        return

    logs = data["history_logs"]
    bad_record_count = 0

    print("=== 📋 SCANNING HISTORY LOGS ===")
    for index, log in enumerate(logs):
        # The app expects a dictionary {}. If it is a string "", it causes the crash.
        if not isinstance(log, dict):
            bad_record_count += 1
            print(f"\n🚨 [CRITICAL BAD RECORD FOUND AT INDEX {index}]")
            print(f"   Data Type Found: {type(log).__name__}")
            print("   Content:")
            print(f"   --------------------------------------------------")
            print(f"   {repr(log)}")
            print(f"   --------------------------------------------------")

    print("\n=== 📊 INSPECTION SUMMARY ===")
    if bad_record_count > 0:
        print(f"❌ Found {bad_record_count} corrupted non-dictionary item(s) that will crash your app.")
        print("👉 Copy and paste the content above into our chat so we can review it!")
    else:
        print("✅ Clean! All entries in 'history_logs' are valid dictionary structures.")

if __name__ == "__main__":
    inspect_database()

