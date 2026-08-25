import json
import os

FILE_PATH = "save_file.json"

def purge_zero_mileage_records():
    if not os.path.exists(FILE_PATH):
        print(f"❌ Error: Could not locate database file '{FILE_PATH}' in this folder.")
        return

    print(f"📖 Opening database file '{FILE_PATH}' for processing...")
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Error: JSON structural format is corrupted. Cannot read file.")
            print(f"Details: {e}")
            return

    if "history_logs" not in data:
        print("ℹ️ Missing 'history_logs' structure array section. No logs available to filter.")
        return

    original_logs_count = len(data["history_logs"])
    cleaned_logs_pool = []
    removed_records_count = 0

    print("⚡ Analyzing fitness logs for zero distance values...")
    
    for log_item in data["history_logs"]:
        # Standard dictionary checks
        if isinstance(log_item, dict):
            # Safe distance metrics locator lookup
            distance_value = float(log_item.get("Distance (Miles)", log_item.get("distance_mi", 0.0)))
            
            # 🟢 CRITERIA FILTER: Retain the item only if mileage is greater than zero
            if distance_value > 0.0:
                cleaned_logs_pool.append(log_item)
            else:
                removed_records_count += 1
                workout_date = log_item.get("Date", "Unknown Date")[:10]
                workout_name = log_item.get("Name", "Standard Activity")
                print(f"  🗑️ Removing: [{workout_date}] {workout_name} — {distance_value} mi")
        else:
            # Retain any mixed plain text log lines (like coliseum string sentences if present)
            cleaned_logs_pool.append(log_item)

    # Save and write data only if zero-mile entries were identified
    if removed_records_count > 0:
        data["history_logs"] = cleaned_logs_pool
        
        # 🛡️ SAFETY PRECAUTION: Generate a local backup clone copy first
        backup_name = FILE_PATH + ".bak"
        if os.path.exists(backup_name):
            os.remove(backup_name)
        os.rename(FILE_PATH, backup_name)
        print(f"📦 Safety precaution: Cloned old file state as '{backup_name}'.")

        # Write clean data payload
        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        print("\n" + "="*50)
        print(f"✅ SUCCESSFUL PURGE! Cleaned out {removed_records_count} empty records.")
        print(f"📊 Activity data rows optimized from {original_logs_count} down to {len(cleaned_logs_pool)} items.")
        print("="*50)
    else:
        print("\n✅ Clean! No tracking log sheets contain 0.0 miles inside the history database.")

if __name__ == "__main__":
    purge_zero_mileage_records()

