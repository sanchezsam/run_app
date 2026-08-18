import json

FILE_PATH = "save_file.json"

try:
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract the history logs array from your player object structure
    logs = data.get('history_logs', []) if isinstance(data, dict) else []
    
    print(f"📊 Total logs found in file: {len(logs)}")
    print("-" * 60)
    
    found_structured_data = False
    for idx, log in enumerate(logs):
        # Check if the log is a structured dictionary or a raw string
        if isinstance(log, dict):
            found_structured_data = True
            date = log.get("Activity Date", "Unknown Date")
            name = log.get("Activity Name", "Unknown Run")
            splits = log.get("splits", [])
            
            print(f"✅ FOUND STRUCTURED RECORD: Index [{idx}]")
            print(f"   📅 Date: {date} | 📑 Name: {name}")
            print(f"   ⏱️ Splits Array Content: {splits}")
            print(f"   🔢 Total Splits Found: {len(splits) if isinstance(splits, list) else 'Not a list'}")
            
        elif isinstance(log, str) and "2026-07-11" in log:
            print(f"⚠️ FOUND STRING RECORD ON JUL 11: Index [{idx}]")
            print(f"   Text payload: {log}")
            print("   ❌ Error: This run was written out as a plain string line, discarding splits!")

    if not found_structured_data:
        print("\n❌ CRITICAL: 0 out of 57 records are saved as dictionaries.")
        print("   Your app is still saving everything as raw text sentences inside the JSON file.")

except Exception as e:
    print(f"❌ Error opening or parsing file: {e}")

