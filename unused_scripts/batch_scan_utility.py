# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import json
import os
import datetime
from fitparse import FitFile

# 🎯 DYNAMIC SYSTEM PIPELINE HOOKS: Pull actual logic blocks straight from configurations
import metrics_config as cfg
try:
    import personal_records_config as pr_cfg
except ImportError:
    pr_cfg = None  # Safe alignment block if module names vary across branches

def parse_single_fit_file(file_path):
    """
    Parses a binary Garmin .fit file and extracts summary session logs.
    Translates raw metric data into normalized imperial parameters.
    """
    try:
        fitfile = FitFile(file_path)
        total_distance_meters = 0.0
        total_ascent_meters = 0.0
        start_time_utc = None
        duration_seconds = 0.0
        
        # Stream messages out of binary record structures to extract metrics data fields
        for record in fitfile.get_messages('session'):
            for data in record:
                if data.name == 'total_distance':
                    total_distance_meters = float(data.value or 0.0)
                elif data.name == 'total_ascent':
                    total_ascent_meters = float(data.value or 0.0)
                elif data.name == 'start_time':
                    start_time_utc = data.value
                elif data.name == 'total_timer_time':
                    duration_seconds = float(data.value or 0.0)

        # Reconcile raw metadata to imperial units matching user profiles
        distance_miles = total_distance_meters * 0.000621371
        elevation_feet = total_ascent_meters * 3.28084
        
        if start_time_utc:
            date_str = start_time_utc.strftime("%Y-%m-%d")
            time_str = start_time_utc.strftime("%H:%M:%S")
        else:
            basename = os.path.basename(file_path)
            date_str = "-".join(basename.split("-")[:3])
            time_str = "12:00:00"

        if distance_miles > 0.1 and duration_seconds > 0:
            total_minutes = duration_seconds / 60.0
            pace_decimal = total_minutes / distance_miles
            pace_str = f"{int(pace_decimal)}:{int((pace_decimal - int(pace_decimal)) * 60):02d}"
            duration_str = f"{int(total_minutes // 60)}:{int(total_minutes % 60):02d}:{int(duration_seconds % 60):02d}"
        else:
            pace_str, duration_str = "0:00", "00:00"

        return {
            "Date": date_str,
            "Display_Distance": round(distance_miles, 2),
            "Distance (Miles)": round(distance_miles, 2),
            "Miles": round(distance_miles, 2),
            "Elevation (Ft)": int(elevation_feet),
            "Activity Type": "Run",
            "Pace": pace_str,
            "Time": duration_str
        }
    except Exception as e:
        st.error(f"⚠️ Error reading binary layout file `{os.path.basename(file_path)}`: {str(e)}")
        return None
def process_2026_fit_directory_with_all_configs():
    """
    Scans data/2026 for the top 20 files.
    Cross-references metrics_config and personal_records_config for awards.
    """
    st.markdown("### 🎛️ Double Config Award Verification Matrix (20 File Limit)")
    
    target_dir = os.path.join("data", "2026")
    if not os.path.exists(target_dir):
        st.error(f"🔴 Target directory path not found: `{target_dir}`.")
        return None

    all_fit_files = sorted([f for f in os.listdir(target_dir) if f.lower().endswith('.fit')])
    if not all_fit_files:
        st.warning(f"ℹ️ Directory `{target_dir}` contains zero `.fit` tracking paths.")
        return None

    # Performance slice cap limits loop execution time
    capped_files = all_fit_files[:20]
    st.info(f"📂 Evaluating up to `{len(capped_files)}` files against standard metrics and all-time records:")
    
    processed_records = []
    
    for filename in capped_files:
        full_path = os.path.join(target_dir, filename)
        payload = parse_single_fit_file(full_path)
        
        if payload:
            dist = payload["Miles"]
            climb = payload["Elevation (Ft)"]
            
            awards_met_list = []
            primary_award_code = "patch_cold_warrior"
            primary_type = "patch"
            primary_metric_desc = "❄️ Baseline Run Verified"

            # 🛠️ CHECK MODULE 1: Process against targets inside metrics_config
            weekly_rewards = getattr(cfg, "WEEKLY_MILEAGE_REWARDS", [])
            if weekly_rewards:
                for rw in sorted(weekly_rewards, key=lambda x: x.get("miles", 0), reverse=True):
                    if dist >= rw.get("miles", 99999.0):
                        awards_met_list.append(f"{rw.get('title', 'Milestone')} [{rw.get('code', 'award')}]")
                        if primary_award_code == "patch_cold_warrior":
                            primary_award_code = rw.get("code", "weekly_miles")
                            primary_type = rw.get("type", "trophy")
                            primary_metric_desc = rw.get("metric", "🏆 Distance Milestone Achieved")
                            break
            else:
                # Local baseline fallbacks
                if dist >= 50.0:
                    awards_met_list.append("🏆 50-Mile Ultra Trophy [weekly_miles_50]")
                    primary_award_code, primary_type, primary_metric_desc = "weekly_miles_50", "trophy", "🏆 50 Mile Weekly Club"
                elif dist >= 26.2:
                    awards_met_list.append("🏅 Full Marathon Ribbon [ribbon_marathon]")
                    primary_award_code, primary_type, primary_metric_desc = "ribbon_marathon", "ribbon", "🏅 Full Marathon Ribbon"
                elif dist >= 13.1:
                    awards_met_list.append("🎗️ Endurance Half-Marathon Ribbon [ribbon_endurance_elite]")
                    primary_award_code, primary_type, primary_metric_desc = "ribbon_endurance_elite", "ribbon", "🎗️ Endurance Elite Half-Marathon"
                elif dist >= 5.0:
                    awards_met_list.append("🔥 5-Mile Run Patch [patch_streak_master]")

            # 🛠️ CHECK MODULE 2: Process against ceilings inside personal_records_config
            if pr_cfg:
                # Dynamic matching loops check for elite tier targets (e.g. 20+ miles or extreme climbing)
                record_thresholds = getattr(pr_cfg, "RECORD_CEILING_THRESHOLDS", {})
                if not record_thresholds:
                    # Fallback checks if attributes are mapped in dictionary array layers
                    record_thresholds = {
                        "legendary_distance": getattr(pr_cfg, "LEGENDARY_DISTANCE_LIMIT", 20.0),
                        "apex_climb": getattr(pr_cfg, "APEX_CLIMB_LIMIT", 1000)
                    }

                if dist >= record_thresholds.get("legendary_distance", 20.0):
                    awards_met_list.append("🥇 All-Time Performance Benchmark [medal_speed_demon]")
                    primary_award_code, primary_type, primary_metric_desc = "medal_speed_demon", "medal", "🥇 Elite Personal Record Cross-Over"
                
                if climb >= record_thresholds.get("apex_climb", 1000):
                    awards_met_list.append("🧗 Peak Elevation Milestone [patch_altitude_titan]")
                    if primary_award_code == "patch_cold_warrior":
                        primary_award_code, primary_type, primary_metric_desc = "patch_altitude_titan", "patch", "🏔️ Summit Climb Milestone"

            # Final fallbacks if zero arrays match
            # Final fallbacks if zero arrays match
            if not awards_met_list:
                awards_met_list.append("Standard Run Logged [patch_cold_warrior]")
            
            # ─── 🛠️ FIXED: DYNAMIC SCHEMA CONFIGURATION HOOK ───
            payload["award_code"] = primary_award_code.lower()
            payload["type"] = primary_type.lower()
            payload["metric"] = primary_metric_desc
            payload["details"] = f"FIT activity stream verified via multi-config validation layers."
            
            # Extract individual codes out of the compiled milestones list to construct the 'patches' array
            extracted_patch_ids = []
            for am in awards_met_list:
                if '[' in am and ']' in am:
                    # FIX: Access the item from the list split BEFORE stripping whitespace strings
                    clean_tag = am.split('[')[-1].split(']')[0].strip()
                    extracted_patch_ids.append(clean_tag)
                else:
                    extracted_patch_ids.append(primary_award_code.lower())
    
            # Pull any extra award codes dynamically from your weekly mileage configurations
            weekly_rewards = getattr(cfg, "WEEKLY_MILEAGE_REWARDS", [])
            if weekly_rewards:
                for rw in weekly_rewards:
                    rw_code = rw.get("code")
                    rw_miles = rw.get("miles", 99999.0)
                    if dist >= rw_miles and rw_code and rw_code.lower() not in extracted_patch_ids:
                        extracted_patch_ids.append(rw_code.lower())
    
            # Inject the clean array payload key your verify_patches.py script scans for!
            payload["patches"] = extracted_patch_ids
            # ────────────────────────────────────────────────────────────────────────────

            # ────────────────────────────────────────────────────────────────────────────
    
            processed_records.append({
                "Filename": filename,
                "Activity Date": payload["Date"],
                "Distance Volume": f"{dist:.2f} Mi",
                "Climb Ascent": f"{climb:,.0f} Ft",
                "Qualifications Triggered": " | ".join(awards_met_list),
                "raw_payload": payload
            })

    return pd.DataFrame(processed_records)
def render_dual_config_scanner_view():
    """Combines parsing engines and renders the user interaction workspace panel."""
    df_ledger = process_2026_fit_directory_with_all_configs()

    if df_ledger is None or df_ledger.empty:
        return

    st.markdown("##### 🏁 Cross-Evaluated FIT Ingestion Summary Sheet")
    st.dataframe(
        df_ledger.drop(columns=["raw_payload"]),
        use_container_width=True,
        column_config={
            "Qualifications Triggered": st.column_config.TextColumn(
                "🎖️ Configuration Milestones Satisfied",
                help="Every individual rule category checklist target unlocked by checking system data properties."
            )
        }
    )

    # Save and merge records directly into the master database file
    if st.button("💾 Synchronize Double Config Awards to master save_file.json", use_container_width=True):
        save_path = "save_file.json"
        master_dict = {}
        
        if os.path.exists(save_path):
            try:
                with open(save_path, "r", encoding="utf-8") as f:
                    master_dict = json.load(f)
            except Exception:
                master_dict = {}

        existing_history = master_dict.get("history_logs", [])
        new_additions_count = 0
        
        for idx, row in df_ledger.iterrows():
            payload = row["raw_payload"]
            # FIXED: Check date AND distance volume to ensure multiple runs on the same day don't block each other
            is_duplicate = any(
                e.get('Date') == payload['Date'] and 
                abs(e.get('Miles', 0.0) - payload['Miles']) < 0.05 
                for e in existing_history
            )
            if not is_duplicate:
                existing_history.append(payload)
                new_additions_count += 1
        master_dict["history_logs"] = existing_history

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(master_dict, f, indent=2, ensure_ascii=False)

        st.success(f"🎉 Successfully imported and synchronized `{new_additions_count}` unified config runs into storage structures!")
        st.session_state["filtered_df"] = pd.DataFrame(existing_history)
        st.rerun()

if __name__ == "__main__":
    st.set_page_config(layout="wide")
    render_dual_config_scanner_view()
