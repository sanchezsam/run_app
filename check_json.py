import json
import os

# Updated to your exact file name
FILE_PATH = "save_file.json" 

if not os.path.exists(FILE_PATH):
    print(f"❌ Error: Could not locate the file '{FILE_PATH}' in the current directory.")
    print("Available files here:", [f for f in os.listdir('.') if f.endswith('.json')])
else:
    try:
        with open(FILE_PATH, 'r') as file:
            data = json.load(file)
            
        # Streamlit character states usually nest things inside a player object or root dictionary
        # Let's dynamically check common keys or fall back to the root if it's a list/flat dict
        history_logs = []
        if isinstance(data, dict):
            if 'history_logs' in data:
                history_logs = data['history_logs']
            elif 'player' in data and isinstance(data['player'], dict):
                history_logs = data['player'].get('history_logs', [])
            else:
                # If it's a generic dict, check if any value contains a list of workouts
                for key, val in data.items():
                    if isinstance(val, list):
                        history_logs = val
                        break
        elif isinstance(data, list):
            history_logs = data

        if not history_logs:
            print(f"⚠️ '{FILE_PATH}' opened, but no historic logs/workout lists could be detected.")
            print("Root keys found in JSON:", list(data.keys()) if isinstance(data, dict) else "List format")
        else:
            print(f"📊 Found {len(history_logs)} saved workouts inside '{FILE_PATH}'. Scanning for splits...")
            fit_count = 0
            
            for idx, log in enumerate(history_logs):
                if not isinstance(log, dict):
                    continue
                name = log.get('name', log.get('Activity Name', 'Unknown Run'))
                date = log.get('date', log.get('Activity Date', 'Unknown Date'))
                
                # Check for our critical splits key
                if "splits" in log:
                    splits = log["splits"]
                    if isinstance(splits, list) and len(splits) > 0:
                        print(f"✅ SUCCESS: Run on [{date}] has {len(splits)} mile splits saved.")
                        fit_count += 1
                    else:
                        print(f"⚠️ EMPTY SPLITS: Run on [{date}] has the 'splits' key, but the list is empty.")
                else:
                    print(f"❌ MISSING KEY: Run on [{date}] has no 'splits' key at all.")
            
            print(f"\n➡️ Scan complete. {fit_count} out of {len(history_logs)} records have active split arrays.")

    except json.JSONDecodeError:
        print(f"❌ Error: '{FILE_PATH}' is corrupted or not a valid JSON structure.")
    except Exception as e:
        print(f"❌ Unexpected tracking exception: {e}")

