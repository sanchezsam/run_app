import os
import json
import pandas as pd

def run_json_diagnostics(file_path="save_file.json"):
    print("==============================================================================")
    print("🔍 DIAGNOSTICS COMMAND ENGINE: CORRUPTIONS & SCHEMA MATRIX SCANNER")
    print("==============================================================================")
    
    # 1. Physical Location Check
    if not os.path.exists(file_path):
        print(f"❌ ERROR: Could not locate '{file_path}' in your current working directory.")
        print(f"   Current Directory Path: {os.getcwd()}")
        return

    # 2. JSON Integrity Parsing
    print(f"📂 Found '{file_path}'. Parsing file structure...")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        print("✅ JSON Syntax Matrix Integrity: VALID")
    except json.JSONDecodeError as je:
        print(f"❌ JSON SYNTAX ERROR: Your file is corrupted or contains syntax errors.")
        print(f"   Details: {str(je)}")
        return
    except Exception as e:
        print(f"❌ FILE READING ERROR: {str(e)}")
        return

    # 3. Structural Object Identification
    print("\n📦 Object Node Layout Scan:")
    if isinstance(raw_data, dict):
        print(f"   - Root Structure: Dictionary Map")
        print(f"   - Top-Level Keys Found: {list(raw_data.keys())}")
    elif isinstance(raw_data, list):
        print(f"   - Root Structure: Flat Array List")
        print(f"   - Total Array Elements: {len(raw_data)}")
    else:
        print(f"   - Unknown Root Datatype Format: {type(raw_data)}")

    # 4. Data Extraction & Dataframe Normalization
    print("\n🔄 Simulating DataFrame Normalization Pipeline...")
    try:
        # Check if logs are wrapped inside a specific sub-key map block
        if isinstance(raw_data, dict):
            # Attempt to automatically locate an embedded array list container
            possible_keys = ['workout_logs', 'logs', 'history', 'activities', 'runs', 'data']
            array_key = next((k for k in possible_keys if k in raw_data and isinstance(raw_data[k], list)), None)
            
            if array_key:
                print(f"   🎯 Auto-located record stream array wrapped inside key: '{array_key}'")
                df = pd.DataFrame(raw_data[array_key])
            else:
                print("   ⚠️ No standard list wrapper found. Normalizing from root map...")
                df = pd.DataFrame([raw_data])
        else:
            df = pd.DataFrame(raw_data)
            
        print(f"   ✅ Extraction Complete. Created active grid containing: [{df.shape[0]} rows x {df.shape[1]} columns]")
    except Exception as normalize_err:
        print(f"❌ DATAFRAME PARSING CRASH: Could not convert data structure to tabular grid.")
        print(f"   Details: {str(normalize_err)}")
        return

    # 5. Core Column Profile Mapping Validation
    print("\n📊 Column Key Mappings Profile:")
    print(f"   Columns Available: {list(df.columns)}")
    
    # Track down time coordinates validation
    date_col = next((c for c in ['Date', 'Calendar Date', 'timestamp', 'date'] if c in df.columns), None)
    if date_col:
        print(f"   📅 Target Date Coordinate Anchor: MATCHED ('{date_col}')")
        try:
            sample_dates = df[date_col].dropna().head(3).tolist()
            print(f"   📝 Sample Raw Value Formats: {sample_dates}")
            
            # Extract distinct years calculation test loop
            parsed_years = pd.to_datetime(df[date_col], errors='coerce').dt.year.dropna().unique()
            print(f"   ⏳ Compiled Year Indices Detected: {sorted([int(y) for y in parsed_years])}")
            
            if len(parsed_years) <= 1:
                print("\n💡 INTERACTIVE TIMELINE ALERT:")
                print("   Your JSON dataset only registers a single calendar year structure.")
                print("   The selector widget needs data items from different calendar years to change rows.")
        except Exception as date_err:
            print(f"   ❌ DATE CONVERSION FLUSH ERROR: {str(date_err)}")
    else:
        print("   ❌ CRITICAL TARGET MISSED: No valid 'Date' columns discovered.")
        print("      Ensure your storage properties use capitalization matching 'Date' or 'Calendar Date'.")

    print("==============================================================================")

if __name__ == "__main__":
    # If your file name is customized (e.g. data.json), update this parameter
    run_json_diagnostics("save_file.json")

