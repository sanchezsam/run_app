# -*- coding: utf-8 -*-
import json
import os
import pandas as pd

def run_preview_fix():
    file_path = "save_file.json"
    if not os.path.exists(file_path):
        print("❌ save_file.json not found.")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        master_data = json.load(f)

    logs = master_data.get("history_logs", [])
    print(f"📊 Processing {len(logs)} activities for Showroom display...")

    # 1. DYNAMICALLY GENERATE PERSONAL RECORDS FROM DATA ARRAY
    longest_run_miles = 0.0
    longest_run_date = "No Logs"
    
    for entry in logs:
        dist = float(entry.get("Distance (Miles)", 0.0))
        date_str = entry.get("Date", "Unknown")
        if dist > longest_run_miles:
            longest_run_miles = dist
            longest_run_date = date_str

    print("\n🏃‍♂️ --- FIXED PERSONAL RECORDS BANNER PREVIEW ---")
    print(f"   * LONGEST RUN: {longest_run_miles:.2f} Mi (Achieved: {longest_run_date})")
    print(f"   * PEAK VOLUME YEAR: 2026 (Active Ingestion Data Matrix)")

    # 2. DYNAMICALLY DERIVE SHOWROOM CODES ON THE FLY
    print("\n🏆 --- FIXED TROPHY CABINET SHELVING PREVIEW ---")
    
    trophies_count = 0
    medals_count = 0
    ribbons_count = 0
    patches_count = 0

    for idx, entry in enumerate(logs):
        # Only process activities within your active 2026 Seasonal Lens
        date_str = entry.get("Date", "")
        if not date_str.startswith("2026"):
            continue

        dist = float(entry.get("Distance (Miles)", 0.0))
        
        # Strip string indicators to convert clean integers safely
        raw_climb = entry.get("Elevation (ft)", "0")
        try:
            climb = float(str(raw_climb).replace("+", "").replace("ft", "").strip())
        except ValueError:
            climb = 0.0

        # Apply your logic rules to sort the entries into visual shelves
        if dist >= 20.0:
            patches_count += 1
            print(f"   [Entry #{idx+1}] {date_str} ({dist} Mi | {climb} Ft) -> 🫀 Cardio Cyborg Patch Unlocked!")
        elif dist >= 13.1:
            ribbons_count += 1
            print(f"   [Entry #{idx+1}] {date_str} ({dist} Mi) -> 🎗️ Endurance Ribbon Unlocked!")
        elif climb >= 1500:
            patches_count += 1
            print(f"   [Entry #{idx+1}] {date_str} ({climb} Ft) -> 🧗 Hill Climber Patch Unlocked!")

    print("\n🏁 --- PROPOSED SHELF MULTIPLIERS TOTALS ---")
    print(f"   * Trophies Shelved: {trophies_count}")
    print(f"   * Medals Shelved:   {medals_count}")
    print(f"   * Ribbons Shelved:  {ribbons_count}")
    print(f"   * Patches Shelved:  {patches_count}")

if __name__ == "__main__":
    run_preview_fix();

