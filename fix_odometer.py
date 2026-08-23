#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Odometer Recovery Utility Script
Scans structured JSON activity fields and recalculates cumulative miles.
"""
import json
import os
import shutil

FILE_PATH = "save_file.json"
BACKUP_PATH = "save_file.json.bak"

def repair_save_file():
    if not os.path.exists(FILE_PATH):
        print(f"❌ Error: Could not find '{FILE_PATH}' in this directory.")
        return

    # 1. Create a safe backup copy
    print(f"📦 Creating backup at {BACKUP_PATH}...")
    shutil.copy2(FILE_PATH, BACKUP_PATH)

    # 2. Read current save file state
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON file: {e}")
            return

    # 3. Scan history arrays and calculate total miles
    history = data.get("history_logs", [])
    print(f"🔍 Scanning {len(history)} historical activity logs...")

    total_accumulated_miles = 0.0
    logged_count = 0

    for item in history:
        # Match your exact JSON structure key
        if isinstance(item, dict) and "Distance (Miles)" in item:
            try:
                total_accumulated_miles += float(item["Distance (Miles)"])
                logged_count += 1
            except (ValueError, TypeError):
                pass

    total_accumulated_miles = round(total_accumulated_miles, 2)
    print(f"📊 Processed {logged_count} valid activities.")
    print(f"🏁 True Total Mileage Computed: {total_accumulated_miles} miles")

    # 4. Inject corrected values back into the save dictionary structure
    if "final_metric_data" not in data:
        data["final_metric_data"] = {}
    
    old_miles = data["final_metric_data"].get("lifetime_odometer_miles", 0.0)
    data["final_metric_data"]["lifetime_odometer_miles"] = total_accumulated_miles

    # 5. Overwrite the file with the corrected values
    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"✅ Success! Updated odometer from {old_miles} to {total_accumulated_miles} miles.")
    print("🚀 You can now safely relaunch the app to view your unlocked circuit tracks!")

if __name__ == "__main__":
    repair_save_file()

