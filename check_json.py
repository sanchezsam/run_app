import json

try:
    with open("save_file.json", "r") as f:
        data = json.load(f)
    
    print("--- TOP LEVEL KEYS ---")
    print(list(data.keys()))
    
    # Let's peek at an example run if there is a history list
    for key in ["history", "runs", "workouts"]:
        if key in data and isinstance(data[key], list) and len(data[key]) > 0:
            print(f"\n--- EXAMPLE ENTRY IN '{key}' ---")
            print(json.dumps(data[key][0], indent=2))
            break
            
except Exception as e:
    print(f"Error reading save.json: {e}")

