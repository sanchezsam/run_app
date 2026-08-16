import json
import pandas as pd

def inspect_nested_data(file_path="save_file.json"):
    print("==============================================================================")
    print("🛰️ NESTED SUBSURFACE DATABASE LOOKUP ENGINE")
    print("==============================================================================")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    targets = ['history_logs', 'synced_garmin_activities', 'daily_miles']
    
    for target in targets:
        if target in data:
            print(f"\n🎯 Inspecting Key Node: '{target}'")
            node_content = data[target]
            print(f"   - Content Datatype Type: {type(node_content)}")
            
            if isinstance(node_content, list) and len(node_content) > 0:
                print(f"   - Total Listed Record Matrix Items: {len(node_content)}")
                # Convert the internal list items to a tabular data view
                df_nested = pd.DataFrame(node_content)
                print(f"   - Discovered Available Tracking Keys: {list(df_nested.columns)}")
                print(f"   - Head Raw Row Samples Preview:\n{df_nested.head(2).to_string(index=False)}")
            elif isinstance(node_content, dict):
                print(f"   - Total Dictionary Elements: {len(node_content)}")
                print(f"   - Discovered Subkeys: {list(node_content.keys())[:8]}")
            else:
                print(f"   - Element Content Status: Empty or Unstructured ({node_content})")
        else:
            print(f"❌ Key '{target}' not present in root map dictionary.")
            
    print("==============================================================================")

if __name__ == "__main__":
    inspect_nested_data()

