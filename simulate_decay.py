#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import shutil
from datetime import datetime, timedelta

FILE_PATH = "save_file.json"
BACKUP_PATH = "save_file.json.bak"

def apply_global_decay():
    if not os.path.exists(FILE_PATH):
        print("❌ Error: Missing file.")
        return

    # Always create a backup profile state
    if not os.path.exists(BACKUP_PATH):
        shutil.copy2(FILE_PATH, BACKUP_PATH)

    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    history = data.get("history_logs", [])
    print(f"🔍 Auditing {len(history)} files for testing...")

    shifted_count = 0
    now_dt = datetime.now()
    cutoff_dt = now_dt - timedelta(days=90)

    # Shift ALL recent workouts back into the past to fake an extended vacation
    for item in history:
        if isinstance(item, dict) and "Date" in item:
            try:
                date_str = item["Date"][:10]
                log_dt = datetime.strptime(date_str, '%Y-%m-%d')
                
                # If the run happened in the last 90 days, push it back by 120 days
                if log_dt >= cutoff_dt:
                    new_dt = log_dt - timedelta(days=120)
                    item["Date"] = new_dt.strftime("%Y-%m-%d") + item["Date"][10:]
                    if "text_payload" in item:
                        item["text_payload"] = item["text_payload"].replace(date_str, new_dt.strftime("%Y-%m-%d"))
                    shifted_count += 1
            except:
                pass

    with open(FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"🚀 Success! Shifted {shifted_count} recent workouts out of your active window.")
    print("⏳ All recent training records are hidden. Refresh your app to see your decay alerts active!")

if __name__ == "__main__":
    apply_global_decay()

