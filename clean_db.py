import json
import os

FILE_PATH = "save_file.json"

def clean_database():
    if not os.path.exists(FILE_PATH):
        print(f"❌ Error: Could not find '{FILE_PATH}' in this directory.")
        return

    # 1. Read the corrupted file
    print(f"📖 Reading {FILE_PATH}...")
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print("❌ Error: The JSON file is too corrupted to read. Please open it manually.")
            return

    if "history_logs" not in data:
        print("ℹ️ No 'history_logs' key found. Your database might already be clean.")
        return

    original_count = len(data["history_logs"])
    
    # 2. Filter out raw text strings and keep only dictionaries
    cleaned_logs = []
    removed_count = 0
    
    for log in data["history_logs"]:
        if isinstance(log, dict):
            cleaned_logs.append(log)
        else:
            removed_count += 1
            print(f"🗑️ Found and removed bad text entry: '{str(log)[:60]}...'")

    # 3. Save if changes were made
    if removed_count > 0:
        data["history_logs"] = cleaned_logs
        
        # Create a backup just in case
        os.rename(FILE_PATH, FILE_PATH + ".bak")
        
        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        print("\n==================================================")
        print(f"✅ SUCCESS! Cleaned {removed_count} raw text string(s).")
        print(f"📊 Activity logs went from {original_count} down to {len(cleaned_logs)} valid items.")
        print(f"📦 A backup of your old file was saved as '{FILE_PATH}.bak'.")
        print("==================================================")
    else:
        print("ℹ️ No broken text strings found in 'history_logs'.")

if __name__ == "__main__":
    clean_database()

