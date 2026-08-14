# batch_cli_uploader.py
import os
import json
from upload_ui import process_and_award_metrics

# SURGICAL IMPORT: Borrow your native application service file parser
try:
    from services import parse_garmin_fit
    HAS_FIT_PARSER = True
except ImportError:
    HAS_FIT_PARSER = False

DATA_DIR = "data"
#YEARS = ["2022", "2023", "2024", "2025", "2026"]
YEARS = ["2022"]
SAVE_FILE = "save_file.json"

def run_batch_cli_upload():
    print("==================================================")
    print("🚀 GARKIN ENGINE: TOTAL HISTORICAL DIRECTORY SWEEP")
    print("==================================================")
    
    if not os.path.exists(SAVE_FILE):
        print(f"❌ Error: Database '{SAVE_FILE}' not found in the root directory.")
        return
        
    if not HAS_FIT_PARSER:
        print("❌ Critical Error: 'parse_garmin_fit' could not be imported from services.")
        print("Please ensure this script is run from the folder containing the 'services/' directory.")
        return
        
    collected_files = []

    # 1. Sweep across your 5 year folders
    for year in YEARS:
        year_path = os.path.join(DATA_DIR, year)
        if not os.path.exists(year_path):
            continue
            
        print(f"🔍 Scanning shelf folder: {year_path}...")
        for filename in os.listdir(year_path):
            if filename.endswith(".json") or filename.endswith(".fit"):
                full_file_path = os.path.join(year_path, filename)
                collected_files.append((filename, full_file_path))

    # Sort files chronologically so odometers build logically up across years
    collected_files.sort(key=lambda x: x[0])
    total_files = len(collected_files)
    print(f"\n📋 Discovery Phase Complete: Found {total_files} total logs ready for full streaming.")
    
    if total_files == 0:
        return

    print("\n📥 Commencing heavy streaming data processing...")
    success_count = 0
    
    for idx, (filename, file_path) in enumerate(collected_files):
        print(f"[{idx + 1}/{total_files}] Ingesting: {filename}...")
        
        try:
            # OPTION A: Handled clean JSON text payloads
            if filename.endswith(".json"):
                with open(file_path, "r", encoding="utf-8") as f:
                    run_payload = json.load(f)
                    
            # OPTION B: Handle Garmin Binary tracks with your active service decoder!
            elif filename.endswith(".fit"):
                # Call your native service file decoder directly
                run_payload = parse_garmin_fit(file_path)

            # Ensure data payload isn't empty or corrupted before parsing awards
            if not run_payload:
                print(f"   ⚠️ Warning: File {filename} returned an empty payload structure. Skipping.")
                continue

            # Pass the parsed text dictionary structure down to your metric evaluator core
            process_and_award_metrics(run_payload)
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ Failed to completely process file {filename}: {e}")
            continue

    # Final Summary Report extraction parameters
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        profile = json.load(f)
        m_data = profile.get("final_metric_data", {})

    print("\n==================================================")
    print("🏆 ALL HISTORICAL RECORDS COMMITTED AND PROCESSED")
    print("==================================================")
    print(f"✅ Successfully Processed: {success_count} / {total_files} Files")
    print(f"📊 Final Lifelong Mileage Odometer: {m_data.get('lifetime_odometer_miles', 0.0):,} Miles")
    print(f"🏔️ Final Lifelong Elevation Gain  : {profile.get('lifetime_elevation_gain', 0.0):,} Vert Feet")
    print(f"🍕 Final Lifelong Calorie Burn    : {m_data.get('lifetime_calories_burned', 0):,} kcal")
    print("==================================================")
    print("Done! Load up your Streamlit dashboard grid to view your fully populated character mantle.")

if __name__ == "__main__":
    run_batch_cli_upload()

