# -*- coding: utf-8 -*-
import json
import os
import pandas as pd

def run_save_file_audit():
    save_path = "save_file.json"
    
    print("=" * 60)
    print("🔍 RUN TIME DATA VAULT AUDIT TERMINAL")
    print("=" * 60)
    
    if not os.path.exists(save_path):
        print(f"❌ Error: Could not locate '{save_path}' in the current working directory.")
        print(f"Current Path Context: {os.getcwd()}")
        return

    try:
        with open(save_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print("✅ Success: save_file.json successfully loaded into memory.")
    except Exception as e:
        print(f"❌ Error: JSON parsing failed. The file may have a formatting error: {str(e)}")
        return

    # 1. Profile Core Architecture
    print("\n👤 1. USER PROFILE PROFILE HIGHLIGHTS:")
    print(f"   * Name Key:   '{data.get('name', 'MISSING')}'")
    print(f"   * Level Key:  '{data.get('level', 'MISSING')}'")
    print(f"   * Total XP:   '{data.get('total_xp', 'MISSING')}'")

    # 2. Personal Records Dictionary Check
    print("\n🏃‍♂️ 2. PERSONAL RECORDS BANNER OBJECT CONTENTS:")
    pr = data.get("personal_records", {})
    if pr:
        for record_name, record_data in pr.items():
            print(f"   * {record_name.upper()}: {record_data}")
    else:
        print("   ⚠️ WARNING: 'personal_records' key is completely missing or empty.")

    # 3. Telemetry Log Array Analysis
    print("\n📊 3. HISTORY LOGS ARRAY ANALYSIS:")
    logs = data.get("history_logs", [])
    print(f"   * Total workout rows found in file: {len(logs)}")
    
    if logs:
        df = pd.DataFrame(logs)
        print(f"   * Extracted Columns Found: {list(df.columns)}")
        
        # Check specific column variations for case matching
        type_cols = [c for c in df.columns if c.lower() == 'type']
        date_cols = [c for c in df.columns if c.lower() == 'date']
        print(f"   * Exact 'Type' Column Variant: {type_cols}")
        print(f"   * Exact 'Date' Column Variant: {date_cols}")
        
        # Isolate the newest uploads
        print("\n🎨 4. LAST 2 INGESTED LOG ENTRIES (RECENT UPLOADS):")
        for idx, log in enumerate(logs[-2:]):
            print(f"   --- Entry [-{2 - idx}] ---")
            print(json.dumps(log, indent=4, ensure_ascii=False))
            
        # Check for 2026 logs specifically
        if 'Date' in df.columns or 'date' in df.columns:
            date_key = 'Date' if 'Date' in df.columns else 'date'
            df['parsed_year'] = pd.to_datetime(df[date_key], errors='coerce').dt.year
            count_2026 = len(df[df['parsed_year'] == 2026])
            print(f"\n📅 5. SEASONAL LENS CHECK: Total rows matching year 2026: {count_2026}")
    else:
        print("   ⚠️ WARNING: 'history_logs' list array is completely empty.")
        
    print("=" * 60)

if __name__ == "__main__":
    run_save_file_audit()

