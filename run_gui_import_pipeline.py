# -*- coding: utf-8 -*-
"""
Automation Script: run_gui_import_pipeline.py - Part 1
Handles core package loads, file stream setups, and environment tracking.
"""

import os
import json
import sys
import streamlit as st
from datetime import timedelta
from pathlib import Path
import upload_ui

# ─── 💥 LINK INTO NATIVE METRIC PROFILE CONFIG ───
try:
    import metrics_config as cfg
except ImportError:
    cfg = None
def execute_gui_pipeline_import(target_dir="data/2026", database_file="save_file.json", log_container=None):
    msg = "🚀 Initializing Fully Dynamic Config-Driven Ingestion Engine..."
    if log_container:
        log_container.info(msg)
    else:
        print(msg)
    
    path = Path(target_dir)
    if not path.exists():
        return

    fit_files = sorted([f for f in os.listdir(target_dir) if f.lower().endswith('.fit')])
    if not fit_files:
        return

    master_dict = {}
    if os.path.exists(database_file):
        try:
            with open(database_file, "r", encoding="utf-8") as f:
                master_dict = json.load(f)
        except Exception:
            master_dict = {}

    existing_history = master_dict.get("history_logs", [])
    summary_messages = []

    # Fallback emoji map used ONLY if the metrics_config lacks explicit icon/emoji properties
    EMOJI_FALLBACK_MAP = {
        "deer": "🦌", "bighorn": "🐏", "overdrive": "💥", 
        "endurance_laurel": "📜", "cardio_cyborg": "🫀",
        "medal_speed_demon": "⚡", "patch_altitude_titan": "🏔️", 
        "patch_cold_warrior": "❄️"
    }
    for filename in fit_files:
        full_path = os.path.join(target_dir, filename)
        
        try:
            with open(full_path, "rb") as fit_stream:
                raw_payload = upload_ui.parse_garmin_fit(fit_stream)
                
                if isinstance(raw_payload, (list, tuple)) and len(raw_payload) > 0:
                    raw_payload = next((item for item in raw_payload if isinstance(item, dict)), raw_payload)

                if isinstance(raw_payload, dict):
                    # ─── EXTRACT RAW NATIVE TELEMETRY ───
                    distance_km = float(raw_payload.get("distance_km", 0.0))
                    distance_mi = round(distance_km * 0.62137119, 2)
                    elevation_ft = round(float(raw_payload.get("elevation_gain_ft", 0.0)), 1)
                    duration_secs = float(raw_payload.get("duration_seconds", 0.0))
                    clean_date = str(raw_payload.get("date", "Unknown")).strip()

                    # Calculate display string metrics
                    duration_str = str(timedelta(seconds=int(duration_secs)))
                    if duration_str.startswith("0:"):
                        duration_str = duration_str[2:]
                    
                    if distance_mi > 0.0 and duration_secs > 0.0:
                        total_seconds_per_mile = duration_secs / distance_mi
                        pace_minutes = int(total_seconds_per_mile // 60)
                        pace_seconds = int(total_seconds_per_mile % 60)
                        pace_str = f"{pace_minutes}:{pace_seconds:02d} min/mi"
                    else:
                        pace_minutes = 0
                        pace_str = "0:00 min/mi"
                    # ─── DETECT AND IMPORT CONFIGURATION DICTIONARY DYNAMICALLY ───
                    config_matrix = None
                    if cfg:
                        for attr in ["FINAL_METRIC_CONFIG", "METRIC_CONFIG", "PATCH_CONFIG", "config"]:
                            if hasattr(cfg, attr):
                                config_matrix = getattr(cfg, attr)
                                break
                    
                    rich_patches_list = []
                    
                    if isinstance(config_matrix, dict):
                        for award_key, boundaries in config_matrix.items():
                            match = True
                            
                            # Safely extract threshold parameters
                            for miles_field in ["min_miles", "min_distance", "miles", "distance"]:
                                if miles_field in boundaries and distance_mi < float(boundaries[miles_field]):
                                    match = False
                            for elev_field in ["min_elevation", "min_elev", "elevation", "climb"]:
                                if elev_field in boundaries and elevation_ft < float(boundaries[elev_field]):
                                    match = False
                            for pace_field in ["max_pace", "pace_cutoff", "pace_limit"]:
                                if pace_field in boundaries and pace_minutes > float(boundaries[pace_field]):
                                    match = False
                                    
                            if match:
                                # ─── GENERATE METADATA ON-THE-FLY FROM CONFIG ───
                                award_id = str(award_key).lower().strip()
                                icon_char = boundaries.get("icon", boundaries.get("emoji", EMOJI_FALLBACK_MAP.get(award_id, "🏅")))
                                clean_name = boundaries.get("name", boundaries.get("title", award_id.replace("_", " ").title()))
                                pillar_tag = boundaries.get("pillar", boundaries.get("category", f"pillar_{award_id}"))
                                
                                rich_patches_list.append({
                                    "pillar": pillar_tag,
                                    "id": award_id,
                                    "name": clean_name,
                                    "icon": icon_char
                                })
                    # Fallback if config criteria didn't match anything
                    if not rich_patches_list:
                        rich_patches_list.append({
                            "pillar": "pillar_5_environment",
                            "id": "patch_cold_warrior",
                            "name": "Cold Warrior Patch",
                            "icon": EMOJI_FALLBACK_MAP.get("patch_cold_warrior", "❄️")
                        })

                    # ─── CONSTRUCT COMPLETE ENVELOPE SCHEMA PAYLOAD ───
                    payload = {
                        "Calendar Date": clean_date,
                        "Activity Status": "🏃 RUN",
                        "Distance": f"{distance_mi:.2f} Mi",
                        "Duration Time": duration_str,
                        "Overall Pace": pace_str,
                        "Climbed Elev": f"{int(elevation_ft):,} ft",

                        "Distance (Miles)": distance_mi,
                        "Elevation (ft)": elevation_ft,
                        "Duration": duration_str,
                        "distance": distance_mi,

                        "CALENDAR DATE": clean_date,
                        "ACTIVITY STATUS": "🏃 RUN",
                        "DISTANCE": f"{distance_mi:.2f} Mi",
                        "DURATION TIME": duration_str,
                        "OVERALL PACE": pace_str,
                        "CLIMBED ELEV": f"{int(elevation_ft):,} ft",
                        
                        "date": clean_date,
                        "Date": clean_date,
                        "distance_km": distance_km,
                        "distance_mi": distance_mi,
                        "duration_seconds": duration_secs,
                        "duration": duration_str,
                        "pace": pace_str,
                        "elevation_gain_ft": elevation_ft,
                        "splits": raw_payload.get("splits", []),
                        "source": "Garmin Config-Linked Automation Engine",
                        
                        "earned_patches": rich_patches_list,
                        "patches": rich_patches_list
                    }

                    # Deduplication Tracking Check
                    match_index = -1
                    for index, e in enumerate(existing_history):
                        if e.get("date") == clean_date or e.get("Calendar Date") == clean_date:
                            match_index = index
                            break
                    
                    if match_index == -1:
                        existing_history.append(payload)
                        summary_messages.append(f"✅ **Added**: `{filename}` ➔ Dynamically Evaluated from Config")
                    else:
                        existing_history[match_index] = payload
                        summary_messages.append(f"🔄 **Upgraded Schema**: `{filename}` ➔ Dynamically Evaluated from Config")
                else:
                    summary_messages.append(f"⚠️ **Skipped**: `{filename}` (Invalid inner tracking shape)")
                    
        except Exception as e:
            summary_messages.append(f"❌ **Error processing {filename}**: {str(e)}")
    # Backfill root level all-time unlocked badges list array
    all_unlocked_badges = set()
    for run in existing_history:
        for patch in run.get("earned_patches", []):
            if isinstance(patch, dict):
                all_unlocked_badges.add(patch.get("id"))

    master_dict["history_logs"] = existing_history
    master_dict["unlocked_badges"] = list(all_unlocked_badges)
    
    with open(database_file, "w", encoding="utf-8") as f:
        json.dump(master_dict, f, indent=2, ensure_ascii=False)

    if log_container:
        with log_container.status(f"🎉 Dynamic Synchronization Complete!", expanded=True) as status:
            for msg in summary_messages:
                st.markdown(msg)
            status.update(label=f"✅ Data rows populated entirely out of metrics_config parameters!", state="complete")
    else:
        print(f"\n🎉 Sync Complete!")
        for msg in summary_messages:
            print(msg.replace("**", ""))

# ─── STREAMLIT UI DESIGN LAYER ────────────────────────────────────────
st.set_page_config(page_title="FIT Automation Ingestion", page_icon="🏃", layout="centered")
st.title("🏃 FIT Automation Pipeline")

if st.button("🚀 Synchronize Database Pipeline", use_container_width=True):
    rendering_box = st.container()
    execute_gui_pipeline_import(log_container=rendering_box)
    st.toast("Sync complete! Profile achievements dynamically updated.", icon="🎖️")
                                # ─── 🛠️ REPOSITION PATCHES AFTER DURATION CELL LAYER ───
                                # 1. Extract icons natively out of your pre-populated run_patches_list variable
                                extracted_emojis = []
                                if isinstance(run_patches_list, list):
                                    for patch in run_patches_list:
                                        if isinstance(patch, dict):
                                            icon_char = patch.get("icon", patch.get("emoji", ""))
                                            if icon_char:
                                                extracted_emojis.append(icon_char)
                                        elif isinstance(patch, str):
                                            automated_lookup = {
                                                "medal_speed_demon": "⚡", 
                                                "patch_altitude_titan": "🏔️", 
                                                "patch_cold_warrior": "❄️"
                                            }
                                            icon_char = automated_lookup.get(patch.lower(), "")
                                            if icon_char:
                                                extracted_emojis.append(icon_char)
                                
                                patch_emojis = "".join(extracted_emojis)
                                
                                # 2. Append to your HTML table buffer string (Inserts emojis next to duration cleanly)
                                week_rows_buffer += f"<tr class='day-row'><td><b>{target_date_str}</b></td><td style='color: #00ffff; font-weight: bold;'>🏃 RUN</td><td>{run_dist:.2f} {unit_abbr}</td><td>{run_time} <span style='margin-left: 6px;'>{patch_emojis}</span></td><td>{run_pace}</td><td>{day_elevation:,.0f} ft</td></tr>"
                                # ────────────────────────────────────────────────────────

