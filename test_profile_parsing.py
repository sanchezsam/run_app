"""
test_profile_parsing.py

A standalone diagnostic script to inspect 'save_file.json', parse the history logs,
and output intermediate sports-science metrics and finalized tier ratings.
Run this script directly in your terminal using: python test_profile_parsing.py
"""

import json
import os
import re
from datetime import datetime, timedelta

def run_diagnostic():
    file_path = "save_file.json"
    print("=" * 70)
    print("🔍 RUNNING CHARACTER PROFILE METRIC DIAGNOSTIC ENGINE")
    print("=" * 70)

    # 1. Verify file existence and load contents
    if not os.path.exists(file_path):
        print(f"❌ ERROR: Content file '{file_path}' not found in the current directory.")
        print("Creating a sample mock 'save_file.json' for testing baseline structures...")
        
        mock_data = {
            "history_logs": [
                {
                    "Date": datetime.now().strftime("%Y-%m-%d"),
                    "Distance (Miles)": 5.5,
                    "pace": "08:15",
                    "Elevation (ft)": "+250ft"
                },
                {
                    "Date": (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d"),
                    "Distance (Miles)": 12.0,
                    "pace": "07:45",
                    "Elevation (ft)": "500"
                }
            ],
            "profile": {
                "running_level": 2,
                "final_metric_data": {
                    "fatigue": 5,
                    "lifetime_odometer_miles": 1250.5
                }
            }
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(mock_data, f, indent=4)
        print(f"✅ Generated mock '{file_path}'. Please replace or modify with real values.")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ CRITICAL ERROR reading JSON file: {e}")
        return

    # 2. Extract logs and structure layout
    history_logs = data.get("history_logs", [])
    print(f"ℹ️ Total historical entries found in file: {len(history_logs)}")
    
    if len(history_logs) > 0:
        print(f"ℹ️ Data type of first log entry: {type(history_logs[0])}")
        if isinstance(history_logs[0], dict):
            print(f"ℹ️ Available keys in log dictionary: {list(history_logs[0].keys())}")

    # 3. Setup time windows
    now_date = datetime.now()
    seven_days_ago = now_date - timedelta(days=7)
    twenty_eight_ago = now_date - timedelta(days=28)
    eighty_four_ago = now_date - timedelta(days=84)

    print("\n" + "-" * 50)
    print("⏱️ SPORTS SCIENCE LOOKBACK WINDOWS (RELATIVE TO TODAY)")
    print(f"  Current Date (Now): {now_date.strftime('%Y-%m-%d')}")
    print(f"  7-Day Threshold:    {seven_days_ago.strftime('%Y-%m-%d')}")
    print(f"  28-Day Threshold:   {twenty_eight_ago.strftime('%Y-%m-%d')}")
    print(f"  84-Day Threshold:   {eighty_four_ago.strftime('%Y-%m-%d')}")
    print("-" * 50)

    miles_7d = 0.0
    miles_28d = 0.0
    miles_84d = 0.0
    valid_sessions_count = 0
    fastest_pace_in_window = 999.0
    total_84d_elevation = 0.0
    ignored_logs_count = 0

    # 4. Process logs matching exact character_profile rules
    for idx, log in enumerate(history_logs):
        if isinstance(log, dict):
            dist_val = float(log.get("Distance (Miles)", 0.0))
            
            # Pace Parsing Strategy
            pace_raw = log.get("pace", 999.0)
            if isinstance(pace_raw, str) and ":" in pace_raw:
                try:
                    parts = pace_raw.strip().split(":")
                    if len(parts) == 2:
                        pace_val = float(parts[0]) + (float(parts[1]) / 60.0)
                    elif len(parts) == 3:
                        pace_val = (float(parts[0]) * 60.0) + float(parts[1]) + (float(parts[2]) / 60.0)
                    else:
                        pace_val = 999.0
                except ValueError:
                    pace_val = 999.0
            else:
                try:
                    pace_val = float(pace_raw) if pace_raw is not None else 999.0
                except ValueError:
                    pace_val = 999.0

            # Elevation Parsing Strategy
            ele_str = str(log.get("Elevation (ft)", "0")).replace('+', '').replace('ft', '').strip()
            try:
                ele_val = float(ele_str) if ele_str else 0.0
            except ValueError:
                ele_val = 0.0
            
            # Date Parsing Strategy
            date_raw = log.get("Date", "")
            try:
                log_dt = datetime.strptime(str(date_raw)[:10], '%Y-%m-%d')
            except Exception:
                ignored_logs_count += 1
                continue

            # Accumulations
            if dist_val > 0:
                if log_dt >= seven_days_ago:
                    miles_7d += dist_val
                if log_dt >= twenty_eight_ago:
                    miles_28d += dist_val
                    valid_sessions_count += 1
                if log_dt >= eighty_four_ago:
                    miles_84d += dist_val
                if ele_val > 0 and log_dt >= eighty_four_ago:
                    total_84d_elevation += ele_val
                if 2.0 < pace_val < 20.0 and log_dt >= twenty_eight_ago:
                    if pace_val < fastest_pace_in_window:
                        fastest_pace_in_window = pace_val
        else:
            ignored_logs_count += 1

    # 5. Output intermediate math summaries
    print("\n📊 INTERMEDIATE ACCUMULATED BIOMETRICS:")
    print(f"  • miles_7d:               {miles_7d:.2f} Mi")
    print(f"  • miles_28d:              {miles_28d:.2f} Mi")
    print(f"  • miles_84d:              {miles_84d:.2f} Mi")
    print(f"  • valid_sessions_count:   {valid_sessions_count}")
    print(f"  • total_84d_elevation:    {int(total_84d_elevation):,} ft")
    print(f"  • fastest_pace_in_window: {fastest_pace_in_window if fastest_pace_in_window < 900.0 else 'N/A'}")
    print(f"  • Ignored/Unparsed Logs:  {ignored_logs_count}")

    # 6. Apply Tier Math Equations
    avg_weekly_macro_volume = miles_84d / 12.0
    macro_base_cushion = min(9, int(avg_weekly_macro_volume / 8.5))
    active_stamina_level = max(1, min(9, int(miles_28d / 15.0)))

    print("\n📐 RATING COMPONENT FRACTIONS:")
    print(f"  • avg_weekly_macro_volume: {avg_weekly_macro_volume:.2f} mi/wk")
    print(f"  • macro_base_cushion:      {macro_base_cushion}")
    print(f"  • active_stamina_level:    {active_stamina_level}")

    # Calculate Endurance Tier
    if avg_weekly_macro_volume >= 35.0:
        endurance_rating = int(round((macro_base_cushion * 0.65) + (active_stamina_level * 0.35)))
        print(f"  • Endurance Calculation Path: Weighted Formula (Macro Volume >= 35)")
    else:
        endurance_rating = active_stamina_level
        print(f"  • Endurance Calculation Path: Direct Volume Path (Macro Volume < 35)")
    endurance_rating = max(1, min(9, endurance_rating))

    # Calculate Speed Tier
    if 2.0 < fastest_pace_in_window < 20.0:
        minutes = int(fastest_pace_in_window)
        seconds = min(59, int(round((fastest_pace_in_window % 1) * 100)))
        total_pace_seconds = (minutes * 60) + seconds
        speed_rating = 9 if total_pace_seconds <= 330 else max(1, min(9, int(9 - ((total_pace_seconds - 330) / 33.7))))
        if miles_7d >= 15.0 and speed_rating < 9:
            speed_rating += 1
    else:
        speed_rating = 1

    # Calculate Elevation Tier
    strength_rating = max(1, min(9, int((total_84d_elevation / 10000.0) * 9)))

    # 7. Final Verification Matrix Report
    print("\n" + "=" * 70)
    print("🏆 FINAL COMPUTED CHARACTER LEVELS RESULTS Matrix")
    print("=" * 70)
    print(f"  🔋 calculated_endurance_level (global_endurance): {endurance_rating} / 9")
    print(f"  ⚡ calculated_speed_level     (global_speed):     {speed_rating} / 9")
    print(f"  ⛰️ calculated_elevation_level (global_elevation): {strength_rating} / 9")
    print("=" * 70)
    
    if endurance_rating == 1 and speed_rating == 1 and strength_rating == 1:
        print("💡 INSIGHT: All stats evaluated to 1. This typically occurs if:")
        print("   1. The 'Date' parameters inside your save file are outdated (older than 28-84 days lookbacks).")
        print("   2. Key names like 'Distance (Miles)', 'pace', or 'Elevation (ft)' have case mismatches.")
        print("   3. Distances inside the logged arrays evaluate to exactly 0.0.")
    else:
        print("✅ SUCCESS: Dynamic tracking levels calculated accurately out of data points.")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    run_diagnostic()

