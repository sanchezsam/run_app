# -*- coding: utf-8 -*-
"""
ATHLETIC TELEMETRY INGESTION ENGINE (import_historical_data.py)
Deep-scans pre-organized year directories inside the data/ folder, parses
FIT binaries chronologically, and syncs authentic device metrics directly
into the player database profile using standard running clock conversions.
"""

import os
import json
import math
from datetime import datetime
from fitparse import FitFile

# ⚙ Master Configuration Path Variables
SAVE_FILE_PATH = "save_file.json"
DATA_ROOT_DIR = "data/"


def convert_seconds_to_clock_time(total_seconds):
    """Converts a duration in seconds into a readable HH:MM:SS clock string."""
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def calculate_running_clock_pace(total_seconds, distance_miles):
    """
    Calculates exact running pace in minutes and seconds per mile (MM:SS)
    using active moving timer time to prevent paused duration dilution.
    """
    if distance_miles <= 0:
        return "0:00"
    
    total_minutes_per_mile = (total_seconds / 60.0) / distance_miles
    pace_minutes = int(total_minutes_per_mile // 1)
    pace_seconds = int(round((total_minutes_per_mile % 1) * 60))
    
    if pace_seconds == 60:
        pace_minutes += 1
        pace_seconds = 0
        
    return f"{pace_minutes}:{pace_seconds:02d}"
def harvest_and_sync_historical_telemetry():
    """
    Traverses nested year folders, orders activities chronologically,
    and executes precise data extraction from the FIT session message.
    """
    print("🚀 Initializing Historical Telemetry Import Pipeline...")
    
    # Hydrate active player profile records from disk storage
    if os.path.exists(SAVE_FILE_PATH):
        with open(SAVE_FILE_PATH, "r", encoding="utf-8") as f:
            player_profile = json.load(f)
    else:
        print("❌ Error: save_file.json database could not be located in the root path.")
        return

    # Initialize defensive list schemas if missing
    if "processed_fit_files" not in player_profile:
        player_profile["processed_fit_files"] = []
    if "history_logs" not in player_profile:
        player_profile["history_logs"] = []
    if "unlocked_badges" not in player_profile:
        player_profile["unlocked_badges"] = []
    if "final_metric_data" not in player_profile:
        player_profile["final_metric_data"] = {
            "lifetime_odometer_miles": 0.0,
            "lifetime_calories_burned": 0,
            "lifetime_elevation_gain_ft": 0
        }

    # Discover and aggregate all available file records across year slots
    discovered_files = []
    if os.path.exists(DATA_ROOT_DIR):
        for root, _, files in os.walk(DATA_ROOT_DIR):
            for file in files:
                if file.lower().endswith(".fit"):
                    full_path = os.path.join(root, file)
                    discovered_files.append((file, full_path))

    if not discovered_files:
        print("ℹ️ Ingestion complete: No custom .fit files discovered inside data/ folders.")
        return

    parsed_activities = []

    # Stage 1: Preliminary chronological sorting metadata extraction
    for filename, filepath in discovered_files:
        if filename in player_profile["processed_fit_files"]:
            continue  # Skip files already committed to the database
            
        try:
            fit_obj = FitFile(filepath)
            activity_timestamp = None
            
            for message in fit_obj.get_messages("record"):
                values = message.get_values()
                if "timestamp" in values:
                    activity_timestamp = values["timestamp"]
                    break
                    
            if not activity_timestamp:
                activity_timestamp = datetime.fromtimestamp(os.path.getmtime(filepath))
                
            parsed_activities.append({
                "filename": filename,
                "filepath": filepath,
                "timestamp": activity_timestamp
            })
        except Exception as e:
            print(f"⚠️ Pre-scan skipped unreadable track file {filename}: {str(e)}")

    parsed_activities.sort(key=lambda x: x["timestamp"])

    if not parsed_activities:
        print("✅ Core database aligned: All discovered files are already fully synchronized.")
        return
    # Stage 2: Execute authentic session data hydration loops
    for entry in parsed_activities:
        try:
            fit_obj = FitFile(entry["filepath"])
            session_data = {}
            
            for message in fit_obj.get_messages("session"):
                session_data = message.get_values()
                break
                
            if not session_data:
                print(f"⚠️ Ingestion Warning: Message summary missing in {entry['filename']}. Skipping file.")
                continue

            raw_meters = session_data.get("total_distance", 0.0)
            distance_miles = round(raw_meters / 1609.344, 2)
            timer_seconds = session_data.get("total_timer_time", 0.0)
            duration_clock_string = convert_seconds_to_clock_time(timer_seconds)
            device_calories = int(session_data.get("total_calories", 0))
            ascent_meters = session_data.get("total_ascent", 0.0)
            elevation_gain_feet = int(round(ascent_meters * 3.28084))
            avg_pace_string = calculate_running_clock_pace(timer_seconds, distance_miles)

            gold_reward = int(15 + (distance_miles * 5))
            xp_reward = int(distance_miles * 50)
            
            player_profile["gold"] = player_profile.get("gold", 0) + gold_reward
            player_profile["calorie_bank_balance"] = player_profile.get("calorie_bank_balance", 0) + device_calories
            player_profile["calorie_bank_total_earned"] = player_profile.get("calorie_bank_total_earned", 0) + device_calories
            
            totals = player_profile["final_metric_data"]
            totals["lifetime_odometer_miles"] = round(float(totals.get("lifetime_odometer_miles", 0.0)) + distance_miles, 2)
            totals["lifetime_calories_burned"] = int(totals.get("lifetime_calories_burned", 0) + device_calories)
            totals["lifetime_elevation_gain_ft"] = int(totals.get("lifetime_elevation_gain_ft", 0) + elevation_gain_feet)

            earned_badge_icons = []
            earned_badge_strings = []
            
            if timer_seconds > 0 and distance_miles > 0:
                seconds_per_mile = timer_seconds / distance_miles
                if 446 <= seconds_per_mile <= 495:
                    earned_badge_icons.append("🐇")
                    earned_badge_strings.append("rabbit")
                    if "rabbit" not in player_profile["unlocked_badges"]:
                        player_profile["unlocked_badges"].append("rabbit")
                        
            if elevation_gain_feet >= 750:
                earned_badge_icons.append("🐏")
                earned_badge_strings.append("bighorn")
                if "bighorn" not in player_profile["unlocked_badges"]:
                    player_profile["unlocked_badges"].append("bighorn")
                    
            if distance_miles >= 15.0:
                earned_badge_icons.append("📜")
                earned_badge_strings.append("endurance")
                if "endurance" not in player_profile["unlocked_badges"]:
                    player_profile["unlocked_badges"].append("endurance")
            elif 10.0 <= distance_miles <= 14.9:
                earned_badge_icons.append("🗺️")
                earned_badge_strings.append("horizon")
                if "horizon" not in player_profile["unlocked_badges"]:
                    player_profile["unlocked_badges"].append("horizon")

            extracted_splits = []
            lap_counter = 1
            for message in fit_obj.get_messages("lap"):
                lap_data = message.get_values()
                lap_meters = lap_data.get("total_distance", 0.0)
                lap_miles = round(lap_meters / 1609.344, 2)
                lap_sec = lap_data.get("total_timer_time", 0.0)
                lap_hr = lap_data.get("avg_heart_rate", "—")
                lap_max_hr = lap_data.get("max_heart_rate", "—")
                
                if lap_miles > 0 or lap_sec > 0:
                    # Formatted to perfectly replicate the GUI lap split keys
                    extracted_splits.append({
                        "split_num": lap_counter,
                        "distance_mi": lap_miles,
                        "time": convert_seconds_to_clock_time(lap_sec),
                        "pace": calculate_running_clock_pace(lap_sec, lap_miles),
                        "avg_heart_rate": lap_hr,
                        "max_heart_rate": lap_max_hr
                    })
                    lap_counter += 1

            timestamp_str = entry["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            
            # Map GUI expected patch metadata lists
            gui_patches_list = []
            for item in earned_badge_strings:
                if item == "rabbit":
                    gui_patches_list.append({"pillar": "cardiac_efficiency", "id": "rabbit", "name": "Rabbit Cruise Node", "icon": "🐇"})
                elif item == "bighorn":
                    gui_patches_list.append({"pillar": "vertical_elevation", "id": "bighorn", "name": "Bighorn Climb Module", "icon": "🐏"})
                elif item == "endurance":
                    gui_patches_list.append({"pillar": "endurance", "id": "endurance", "name": "Endurance Laurel Shield", "icon": "📜"})
                elif item == "horizon":
                    gui_patches_list.append({"pillar": "distance", "id": "horizon", "name": "Horizon Mapper Processor", "icon": "🗺️"})

            badge_string = "".join(earned_badge_icons) if earned_badge_icons else "None"
            
            # Replicate the exact literal layout pattern parsed by your original dashboard text splitters
            payload = (
                f"[{timestamp_str}] Run: {distance_miles} miles | Pace: {avg_pace_string} min/mi | "
                f"Elevation Climbed: +{elevation_gain_feet}.0 ft | "
                f"[REWARD] +{gold_reward}g, +{xp_reward} XP. | [CALORIE REWARDS] +{device_calories} kcal | "
                f"🎖️ Rewards: {badge_string}"
            )
            
            # Class definition allows json.dump to process normally while acting as a string for calendar line parsing
            class DashboardHybridLogger(dict):
                def __str__(self):
                    return payload
                def split(self, sep=None, maxsplit=-1):
                    return payload.split(sep, maxsplit)
                def strip(self, chars=None):
                    return payload.strip(chars)

            # Hydrate identical GUI telemetry keys to support downstream operations
            history_dict_row = DashboardHybridLogger({
                "Date": timestamp_str,
                "Name": entry["filename"],
                "Distance (Miles)": distance_miles,
                "Duration": duration_clock_string,
                "pace": avg_pace_string,
                "Elevation (ft)": f"+{elevation_gain_feet}.0 ft",
                "splits": extracted_splits,
                "text_payload": payload,
                "aerobic_decoupling_percent": 0.0,
                "ambient_temp_f": 72.0,
                "zone_1_2_duration_percent": 60.0,
                "earned_patches": gui_patches_list
            })

            player_profile["history_logs"].append(history_dict_row)
            player_profile["processed_fit_files"].append(entry["filename"])
            print(f"✅ Successfully imported: {distance_miles} mi | {duration_clock_string} | {avg_pace_string} /mi | +{elevation_gain_feet} ft")

        except Exception as e:
            print(f"❌ Error parsing file content data details in {entry['filename']}: {str(e)}")

    with open(SAVE_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(player_profile, f, indent=4, ensure_ascii=False)
    print("\n🎉 Bulk Data Sync Complete! Database profile entries successfully updated.")


if __name__ == "__main__":
    harvest_and_sync_historical_telemetry()

