#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
# Fix: Imported timedelta alongside datetime to resolve the NameError crash
from datetime import datetime, timedelta
from fitparse import FitFile

def inspect_fit_file(file_path):
    """
    Reads a Garmin .fit binary file and prints a comprehensive telemetry report.
    Exposes fields slated for ingestion alongside unused embedded metrics.
    """
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found at '{file_path}'")
        return

    print("=" * 80)
    print(f"🛰️  GARMIN .FIT TELEMETRY FIELD INSPECTION FOR: {os.path.basename(file_path)}")
    print("=" * 80)

    try:
        fit_file = FitFile(file_path)
    except Exception as e:
        print(f"💥 Failed to parse binary file structure. Error: {str(e)}")
        return

    # =========================================================================
    # SECTION 1: CRITICAL FILE TRACKING HEADER METADATA (SLATED FOR INGESTION)
    # =========================================================================
    print("\n[🔒 CORE ID & ANTI-DUPLICATION HEADERS — TO BE DIGESTED]")
    print("-" * 80)
    
    file_id_messages = list(fit_file.get_messages('file_id'))
    if file_id_messages:
        for msg in file_id_messages:
            data_dict = {d.name: d.value for d in msg}
            
            # The critical watch birth certificate timestamp field we are adding
            time_created = data_dict.get('time_created')
            device_serial = data_dict.get('serial_number')
            manufacturer = data_dict.get('manufacturer')
            product_id = data_dict.get('product')
            
            print(f"  • time_created (Watch Record Start Time) : {time_created} (UTC)")
            print(f"  • serial_number (Garmin Hardware Serial) : {device_serial}")
            print(f"  • manufacturer (Hardware Device Vendor)  : {manufacturer}")
            print(f"  • product (Garmin Device Product ID)    : {product_id}")
    else:
        print("  ⚠️ Warning: No 'file_id' or 'time_created' header messages found in this file.")

    # =========================================================================
    # SECTION 2: WORKOUT SUMMARY METRICS (CURRENTLY DIGESTED BY ENGINE)
    # =========================================================================
    print("\n[📊 WORKOUT SUMMARY DATA PATHWAYS — CURRENTLY DIGESTED]")
    print("-" * 80)
    
    summary_metrics = {
        "distance": None,
        "calories": None,
        "heart_rate_samples": 0,
        "altitude_samples": 0,
        "first_timestamp": None,
        "last_timestamp": None
    }
    
    # Track metrics from record point samples to simulate what services.py performs
    for record in fit_file.get_messages('record'):
        data_dict = {data.name: data.value for data in record}
        
        if 'timestamp' in data_dict and data_dict['timestamp'] is not None:
            if summary_metrics["first_timestamp"] == None:
                summary_metrics["first_timestamp"] = data_dict['timestamp']
            summary_metrics["last_timestamp"] = data_dict['timestamp']
            
        if 'distance' in data_dict and data_dict['distance'] is not None:
            summary_metrics["distance"] = data_dict['distance']
            
        if 'calories' in data_dict and data_dict['calories'] is not None:
            summary_metrics["calories"] = data_dict['calories']
            
        if 'heart_rate' in data_dict and data_dict['heart_rate'] is not None:
            summary_metrics["heart_rate_samples"] += 1
            
        if ('enhanced_altitude' in data_dict and data_dict['enhanced_altitude'] is not None) or \
           ('altitude' in data_dict and data_dict['altitude'] is not None):
            summary_metrics["altitude_samples"] += 1

    if summary_metrics["distance"] is not None:
        miles = summary_metrics["distance"] * 0.000621371
        print(f"  • distance (Final Odometer Record)       : {summary_metrics['distance']:.2f} meters ({miles:.2f} Mi)")
    print(f"  • calories (Metabolic Burn Record)       : {summary_metrics['calories']} kcal")
    
    if summary_metrics["first_timestamp"] and summary_metrics["last_timestamp"]:
        duration = (summary_metrics["last_timestamp"] - summary_metrics["first_timestamp"]).total_seconds()
        print(f"  • timestamp bounds (Ingestion Timeline)  : Start: {summary_metrics['first_timestamp']} -> End: {summary_metrics['last_timestamp']}")
        print(f"  • calculated duration (Elapsed Clock)   : {duration:.0f} seconds ({timedelta(seconds=int(duration))})")
        
    print(f"  • heart_rate points (Cardio Stream Size) : {summary_metrics['heart_rate_samples']} records digested")
    print(f"  • altitude data points (Ascent Index Size): {summary_metrics['altitude_samples']} records digested")

    # =========================================================================
    # SECTION 3: UNUSED FIELDS DISCOVERY POOL
    # =========================================================================
    print("\n[💡 UNUSED TELEMETRY FIELDS FOUND — AVAILABLE FOR EXPANSION]")
    print("-" * 80)
    print("  The following embedded fields were detected inside this specific activity file\n"
          "  but are completely ignored by your current services.py parser engine:")
    
    discovered_record_fields = set()
    discovered_lap_fields = set()
    
    # Sample actual messages to extract layout names
    for record in fit_file.get_messages('record'):
        for data in record:
            if data.value is not None:
                discovered_record_fields.add((data.name, type(data.value).__name__, data.units))
                
    for lap in fit_file.get_messages('lap'):
        for data in lap:
            if data.value is not None:
                discovered_lap_fields.add((data.name, type(data.value).__name__, data.units))

    # Clean out fields you are already using from the discovery list
    already_used = {'distance', 'calories', 'heart_rate', 'altitude', 'enhanced_altitude', 'timestamp', 'total_distance', 'total_timer_time', 'total_elapsed_time'}
    
    print("\n  🔹 Inside Core Tracking Time-Series ('record' messages):")
    record_count = 0
    for name, dtype, units in sorted(discovered_record_fields):
        if name in already_used:
            continue
        unit_str = f" in {units}" if units else ""
        print(f"    - Field: {name:<28} | Type: {dtype:<8}{unit_str}")
        record_count += 1
    if record_count == 0:
        print("    (No unmapped fields found in time-series records)")

    print("\n  🔹 Inside Summary Lap Splits ('lap' messages):")
    lap_count = 0
    for name, dtype, units in sorted(discovered_lap_fields):
        if name in already_used:
            continue
        unit_str = f" in {units}" if units else ""
        print(f"    - Field: {name:<28} | Type: {dtype:<8}{unit_str}")
        lap_count += 1
    if lap_count == 0:
        print("    (No unmapped fields found in summary laps)")

    print("\n" + "=" * 80)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("💡 Usage Instructions:")
        print("  python inspect_fit.py <path_to_your_garmin_file.fit>")
        sys.exit(1)
        
    inspect_fit_file(sys.argv[1])

