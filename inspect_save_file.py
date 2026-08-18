# -*- coding: utf-8 -*-
"""
inspect_save_file.py
Diagnostic tool to inspect history_logs inside save_file.json, check for the
missing 0.68 Mi run, and flag date duplication or pace overwrites.
"""
import json
import os

FILE_PATH = "save_file.json"

if not os.path.exists(FILE_PATH):
    print(f"❌ Error: Cannot locate '{FILE_PATH}' in this folder directory.")
    exit(1)

print("📖 Reading 'save_file.json' content logs...")
with open(FILE_PATH, "r", encoding="utf-8") as f:
    try:
        data = json.load(f)
    except Exception as e:
        print(f"❌ JSON Parsing Error: Your save file structure is corrupted. {str(e)}")
        exit(1)

history_logs = data.get("history_logs", [])
print(f"📋 Found total of {len(history_logs)} run entries registered in history_logs.\n")

print("🔍 SCANNING ENTRIES INDIVIDUALLY:")
print("-" * 90)

date_counts = {}
found_short_run = False

for idx, log in enumerate(history_logs):
    # Support both structural types (native dictionary format or legacy flat text strings)
    if isinstance(log, dict):
        date = log.get("Date") or log.get("date") or "Unknown Date"
        dist = log.get("Distance (Miles)") or log.get("distance_miles") or log.get("dist", 0.0)
        pace = log.get("pace") or log.get("pace_min_mile") or 0.0
        ele = log.get("Elevation (ft)") or log.get("elevation_gain_ft") or 0
        patches = log.get("earned_patches") or []
        
        # Format patches for easy reading
        patch_str = ""
        if isinstance(patches, list):
            patch_str = ",".join([p.get("id", str(p)) if isinstance(p, dict) else str(p) for p in patches])
        else:
            patch_str = str(patches)
            
        print(f" Entry [{idx}]: Date: {date} | Dist: {dist} Mi | Pace: {pace} | Elev: {ele} | Patches: [{patch_str}]")
        
        date_counts[date] = date_counts.get(date, 0) + 1
        if float(dist) == 0.68:
            found_short_run = True
            
    elif isinstance(log, str):
        print(f" ⚠️ Entry [{idx}] is stored as a raw string line: {log}")
        if "0.68" in log:
            found_short_run = True

print("-" * 90)
print("\n📊 DIAGNOSTIC FINDINGS SUMMARY:")

if found_short_run:
    print("✅ SUCCESS: The 0.68 Mi run is present in save_file.json! The bug is down in the spreadsheet view engine.")
else:
    print("❌ CRITICAL: The 0.68 Mi run is NOT inside save_file.json. It was overwritten or dropped during the upload step.")

# Flag duplicate date keys causing overwrite bugs
duplicates = {d: c for d, c in date_counts.items() if c > 1}
if duplicates:
    print(f"⚠️ DATE DUPLICATION WARNING: The following dates have multiple entries: {duplicates}")
    print("   -> If your spreadsheet or upload engine maps data by date strings, they will overwrite each other!")
else:
    print("✅ Date indexing is clean. No duplicate day keys found in your database records.")

