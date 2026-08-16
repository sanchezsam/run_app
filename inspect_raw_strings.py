import json

def read_raw_log_lines(file_path="save_file.json"):
    print("==============================================================================")
    print("📋 RAW NESTED STRING DATA SCANNER")
    print("==============================================================================")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    if 'history_logs' in data:
        logs = data['history_logs']
        total_items = len(logs)
        print(f"✅ Auto-located 'history_logs' containing: {total_items:,} total lines.\n")
        
        # Pull 5 sample rows safely regardless of their internal string structure
        print("🎯 First 5 Raw Data Samples:")
        for idx, item in enumerate(logs[:5]):
            print(f"   Line [{idx}]: type={type(item).__name__} | content = {repr(item)}")
            
        print("\n🎯 Last 2 Raw Data Samples:")
        for idx, item in enumerate(logs[-2:]):
            actual_idx = total_items - 2 + idx
            print(f"   Line [{actual_idx}]: type={type(item).__name__} | content = {repr(item)}")
            
    else:
        print("❌ Could not locate 'history_logs' in this storage file.")
    print("==============================================================================")

if __name__ == "__main__":
    read_raw_log_lines()

