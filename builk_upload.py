# -*- coding: utf-8 -*-
"""
🛰️ RETRO GLADIATOR — CLI BULK DATA INGESTION ENGINE
Populates save_file.json directly from a target directory of Garmin .fit tracking files.
"""
import os
import sys
import re
from datetime import datetime
from run_utils import SAVE_FILE, load_save_data, save_player_profile

# Safely import your existing Garmin FIT parser binary service module
try:
    from services import parse_garmin_fit
except ImportError:
    print("❌ Error: Could not locate 'services.py' with 'parse_garmin_fit'.")
    print("Ensure this script is placed inside your root application directory.")
    sys.exit(1)

FILE_PATH = SAVE_FILE

def calculate_pace_float(total_secs, miles):
    if miles > 0 and total_secs > 0:
        return (total_secs / 60.0) / miles
    return 0.0

def load_save_file():
    if not os.path.exists(FILE_PATH):
        print(f"ℹ️ Base database file '{FILE_PATH}' not detected. Constructing a fresh profile...")
        return {"history_logs": [], "gold": 50, "total_xp": 0}
    return load_save_data(FILE_PATH, default={"history_logs": [], "gold": 50, "total_xp": 0})

def save_database(data):
    save_player_profile(data, FILE_PATH)

def main():
    # Enforce standard command line arguments setup execution
    if len(sys.argv) < 2:
        print("❌ Usage Error: Missing path to your .fit files directory.")
        print("📌 Run syntax: python bulk_populate_ledger.py /path/to/your/fit_directory")
        sys.exit(1)

    target_dir = sys.argv[1]
    if not os.path.isdir(target_dir):
        print(f"❌ Error: Path directory '{target_dir}' does not exist.")
        sys.exit(1)

    # 1. Gather all local .fit filenames inside the requested path folder target
    fit_files = [f for f in os.listdir(target_dir) if f.lower().endswith('.fit')]
    if not fit_files:
        print(f"⚠️ Ingestion Aborted: No '.fit' tracker logs detected inside '{target_dir}'.")
        sys.exit(0)

    print(f"🔍 Scanner found {len(fit_files)} tracking files to analyze inside '{target_dir}'.")
    
    # 2. Ingest your current persistent save profile array records into memory
    save_data = load_save_file()
    
    # Support both flat list configurations or nested objects structure variants
    is_nested_player = "player" in save_data and isinstance(save_data["player"], dict)
    historical_logs = save_data["player"].get("history_logs", []) if is_nested_player else save_data.get("history_logs", [])

    print(f"📊 Established reference links to {len(historical_logs)} current ledger records.")
    print("-" * 75)

    added_count = 0
    duplicate_count = 0
    failure_count = 0
    
    accumulated_gold = 0
    accumulated_xp = 0
    accumulated_miles = 0.0

    # 3. Process every individual file session chronologically or in order string sequence loop
    for idx, filename in enumerate(sorted(fit_files), 1):
        file_path = os.path.join(target_dir, filename)
        
        try:
            with open(file_path, 'rb') as f:
                file_bytes = f.read()
                
            # Execute your system fit metrics parser function block
            fit_m = parse_garmin_fit(file_bytes)
            
            # Formulate core alignment signatures
            parsed_date_str = fit_m.get("date", datetime.now().strftime('%Y-%m-%d'))
            calculated_distance_miles = fit_m.get("distance_km", 0.0) * 0.621371
            chk_dist = round(calculated_distance_miles, 2)
            
            t_secs = int(fit_m.get("duration_seconds", 0))
            chk_dur = f"{t_secs // 3600:02d}:{(t_secs % 3600) // 60:02d}:{t_secs % 60:02d}"
            calculated_pace = calculate_pace_float(t_secs, calculated_distance_miles)

            # --- EXACT TRIPLE SPECIFICATION DUPLICATION INJECTOR SHIELD ---
            is_duplicate = False
            for log_row in historical_logs:
                if isinstance(log_row, dict):
                    h_date = str(log_row.get("Date", log_row.get("Activity Date", "")))[:10]
                    h_dist = round(float(log_row.get("Distance (Miles)", log_row.get("dist", 0.0))), 2)
                    h_dur = str(log_row.get("Duration", log_row.get("duration", ""))).strip()
                    
                    if h_date == parsed_date_str and h_dist == chk_dist and h_dur == chk_dur:
                        is_duplicate = True
                        break
                elif isinstance(log_row, str):
                    log_str = str(log_row)
                    if f"[{parsed_date_str}]" in log_str:
                        d_m = re.search(r'(?:Run|run|ran|distance):?\s*([0-9.]+)', log_str, re.IGNORECASE)
                        if not d_m: d_m = re.search(r'([0-9.]+)\s*(?:miles|mi)', log_str, re.IGNORECASE)
                        dur_m = re.search(r'Duration:\s*([0-9:]+)', log_str, re.IGNORECASE)
                        
                        if d_m and dur_m:
                            h_dist = round(float(d_m.group(1)), 2)
                            h_dur = dur_m.group(1).strip()
                            if h_dist == chk_dist and h_dur == chk_dur:
                                is_file_duplicate = True
                                break

            if is_duplicate:
                print(f"  ⏭️  [{idx}/{len(fit_files)}] SKIPPED: '{filename}' is already registered (Date: {parsed_date_str} | {chk_dist} Mi).")
                duplicate_count += 1
                continue

            # 4. Allocate Gamified Telemetry Metrics parameters rewards
            gold_rewarded = int(chk_dist * 10)
            xp_gained = int(chk_dist * 50)
            
            accumulated_gold += gold_rewarded
            accumulated_xp += xp_gained
            accumulated_miles += chk_dist

            text_sentence = f"[{parsed_date_str}] Run: {chk_dist:.2f} miles | Duration: {chk_dur} | Pace: {calculated_pace:.2f} min/mi | Elevation Climbed: +{fit_m['elevation_gain_ft']} ft. [REWARD] Earned +{gold_rewarded}g and +{xp_gained} XP."
            
            # Format object schema structure matching your revised ledger framework exactly
            structured_log = {
                "Date": parsed_date_str,
                "Name": filename,
                "Distance (Miles)": chk_dist,
                "Duration": chk_dur,
                "pace": round(calculated_pace, 2),
                "Elevation (ft)": f"+{fit_m['elevation_gain_ft']} ft",
                "splits": fit_m.get('splits', []),
                "text_payload": text_sentence
            }
            
            historical_logs.append(structured_log)
            print(f"  ✅ [{idx}/{len(fit_files)}] PARSED: '{filename}' committed under [{parsed_date_str}] — Added {chk_dist:.2f} Mi | +{gold_rewarded}g.")
            added_count += 1

        except Exception as e:
            print(f"  ❌ [{idx}/{len(fit_files)}] FAILURE on track line item file '{filename}': {e}")
            failure_count += 1

    # 5. Compile global changes and write the file array payload back out safely to disk drive lines
    if added_count > 0:
        if is_nested_player:
            save_data["player"]["history_logs"] = historical_logs
            save_data["player"]["gold"] = int(save_data["player"].get("gold", 50)) + accumulated_gold
            save_data["player"]["total_xp"] = int(save_data["player"].get("total_xp", 0)) + accumulated_xp
        else:
            save_data["history_logs"] = historical_logs
            save_data["gold"] = int(save_data.get("gold", 50)) + accumulated_gold
            save_data["total_xp"] = int(save_data.get("total_xp", 0)) + accumulated_xp

        save_database(save_data)

    print("-" * 75)
    print("🛰️  CLI BULK DATA INGESTION ENGINE PROCESS CONCLUDED.")
    print(f"   ✨ Added Runs     : {added_count}")
    print(f"   ⏭️  Skipped Dupes  : {duplicate_count}")
    print(f"   ❌ Failed Parsing : {failure_count}")
    print(f"   💰 Total Gold Core: +{accumulated_gold}g | 👑 XP Yielded: +{accumulated_xp} XP | 🎛️ Odometer Delta: +{accumulated_miles:.2f} Mi")
    print(f"🚀 Your global file '{FILE_PATH}' database has been optimized and synchronized.")

if __name__ == '__main__':
    main()

