# -*- coding: utf-8 -*-
import json

SAVE_FILE = "save_file.json"

try:
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        profile = json.load(f)
    
    print("=== 🎖️ TOP-LEVEL PROFILE BADGES ===")
    badges = profile.get("unlocked_badges", [])
    print(f"Total Unique Badges: {len(badges)}")
    print(f"IDs found: {badges}\n")
    
    print("=== 📜 RECENT WORKOUT HISTORY PATCH LOG ===")
    history = profile.get("history_logs", [])
    if history:
        last_run = history[-1]
        print(f"Date: {last_run.get('Date')}")
        print(f"Distance: {last_run.get('Distance (Miles)')} Mi")
        print(f"Earned Patches In Log: {last_run.get('earned_patches', '⚠️ NO PATCHES KEY FOUND')}")
    else:
        print("❌ No history logs found in file.")

except FileNotFoundError:
    print(f"❌ Error: Could not find {SAVE_FILE} in this directory.")
except Exception as e:
    print(f"❌ Error reading file: {str(e)}")

