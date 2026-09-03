# -*- coding: utf-8 -*-
"""
ATHLETIC TRAINING HUB — HARDWARE SHOWROOM (showroom_ui.py)
Displays single-run performance patches, cumulative lifelong career trophies,
and weekly mileage/elevation milestones. Pulls explicit image asset paths 
dynamically from metrics_config.py with clean base64 image streaming fallbacks.
"""

import os
import json
import base64
import streamlit as st
import streamlit as st
import pandas as pd
import metrics_config as cfg
import personal_records_config as pr_cfg
import pro_shop_config as shop_cfg
import arena_tournaments_config as arena_cfg
from showroom_engine import calculate_current_week_metrics,check_streak_defense_status,calculate_personal_records
from upload_ui import get_hr_zone_style
from dashboard_ui import show_run_lap_breakdown, render_zone_octagon_display


# ⚙️ IMPORT Master Performance Registries and Threshold Structures
from metrics_config import (
    FINAL_METRIC_CONFIG, 
    WEEKLY_MILEAGE_REWARDS, 
    WEEKLY_ELEVATION_REWARDS, 
    COVETED_TARGETS
)

class LiveDiskHydrator:
    """Lightweight object utility to map fresh disk JSON into an attribute namespace."""
    def __init__(self, data_dict):
        self.__dict__.update(data_dict)
def render_sidebar_requirements_manual(curr_miles, curr_climb, df_instances, target_container=None):
    """
    Renders an interactive roadmap inside the targeted sidebar panel with live progression loops.
    Uses clean context mapping (with ctx:) to ensure elements append sequentially without layout fragmentation.
    """
    ctx = target_container if target_container is not None else st.sidebar
    
    with ctx:
        st.markdown("### 📘 Showroom Handbook")
        st.caption("Track your remaining targets to unlock your next pieces of hardware.")
        st.markdown("---")
        
        # 🏃‍♂️ Mileage Milestone Computations
        st.markdown("**🏃‍♂️ Next Mileage Milestones:**")
        unearned_miles = [aw for aw in getattr(cfg, "WEEKLY_MILEAGE_REWARDS", []) if curr_miles < aw["miles"]]
        next_mile_goals = unearned_miles[:2] if unearned_miles else getattr(cfg, "WEEKLY_MILEAGE_REWARDS", [])[-1:]
        
        if next_mile_goals:
            for goal in next_mile_goals:
                target_val = max(1.0, float(goal["miles"]))
                progress_pct = min(curr_miles / target_val, 1.0)
                remaining = max(0.0, goal["miles"] - curr_miles)
                
                icon = str(goal.get("icon", "🔒")).strip()
                tier_str = str(goal.get("tier", "common")).upper()
                description = str(goal.get("desc", "No description provided."))
                
                header = f"{icon} {goal['title']} ({progress_pct:.0%})"
                
                exp = st.expander(header)
                exp.markdown(f"🏆 **Tier:** `{tier_str}`")
                exp.markdown(f"*{description}*")
                exp.markdown(f"**Target:** {goal['miles']} Miles This Week")
                exp.markdown(f"**Current Volume:** {curr_miles:.1f} Miles")
                exp.progress(progress_pct)
                exp.markdown(f"💡 **You are only {remaining:.1f} miles away** from unlocking this reward!")
        else:
            st.caption("🎉 All weekly mileage milestones cleared!")

        # 🏔️ Elevation Milestone Computations
        st.markdown("<br/>**🏔️ Next Elevation Milestones:**", unsafe_allow_html=True)
        unearned_climb = [aw for aw in getattr(cfg, "WEEKLY_ELEVATION_REWARDS", []) if curr_climb < aw["climb_ft"]]
        next_climb_goals = unearned_climb[:2] if unearned_climb else getattr(cfg, "WEEKLY_ELEVATION_REWARDS", [])[-1:]
        
        if next_climb_goals:
            for goal in next_climb_goals:
                target_val = max(1.0, float(goal["climb_ft"]))
                progress_pct = min(curr_climb / target_val, 1.0)
                remaining = max(0.0, goal["climb_ft"] - curr_climb)
                
                icon = str(goal.get("icon", "🔒")).strip()
                tier_str = str(goal.get("tier", "common")).upper()
                description = str(goal.get("desc", "No description provided."))
                
                header = f"{icon} {goal['title']} ({progress_pct:.0%})"
                
                exp = st.expander(header)
                exp.markdown(f"🏆 **Tier:** `{tier_str}`")
                exp.markdown(f"*{description}*")
                exp.markdown(f"**Target:** {goal['climb_ft']} Ft Elevation This Week")
                exp.markdown(f"**Current Volume:** {curr_climb:.0f} Ft")
                exp.progress(progress_pct)
                exp.markdown(f"💡 **You are only {remaining:.0f} ft away** from unlocking this reward!")
        else:
            st.caption("🎉 All weekly elevation milestones cleared!")

def render_rpg_sidebar_header(level, xp, pct, title, defense_state, days_elapsed):
    """Renders the character sheet, skin tier badges, and active defense alerts inside the sidebar."""
    active_skin = shop_cfg.PRO_SHOP_SKINS_REGISTRY[0]
    for skin in shop_cfg.PRO_SHOP_SKINS_REGISTRY:
        if level >= skin["unlock_level"]:
            active_skin = skin
            
    st.sidebar.markdown(f"""
    <div style='border: 1px solid {active_skin["accent_color"]}; padding: 12px; border-radius: 6px; background: {active_skin["sidebar_bg"]};'>
        <p style='margin:0; font-size:0.75rem; color:gray; text-transform:uppercase;'>ENGINE STATUS</p>
        <h4 style='margin:2px 0; font-size:1.05rem; color:{active_skin["accent_color"]};'>LVL {level} &bull; {title}</h4>
        <span style='background:{active_skin["accent_color"]}; color:black; font-size:0.6rem; font-weight:bold; padding:2px 5px; border-radius:4px;'>{active_skin["badge"]} UNLOCKED</span>
        <p style='margin:6px 0 4px 0; font-size:0.75rem; color:gray;'>XP: {xp:,} / {cfg.XP_PER_LEVEL_THRESHOLD:,} ({pct}%)</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Enforce float bounds strictly between 0.0 and 1.0 to prevent Streamlit crashes
    safe_progress_float = min(1.0, max(0.0, float(pct) / 100.0))
    st.sidebar.progress(safe_progress_float)
    
    if defense_state == "decaying":
        st.sidebar.warning(f"🚨 **STREAK DECAY ALERT:** It has been {days_elapsed} days since your last workout sequence! Run today to defend your active streak patches!")
    else:
        st.sidebar.success("✅ **STREAK SECURE:** Active consistency patches are safely mounted and stable.")
    st.sidebar.markdown("---")


def force_disk_profile_hydration():
    """Bypasses Streamlit session memory cache to read raw live profiles from disk."""
    if os.path.exists("save_file.json"):
        try:
            with open("save_file.json", "r", encoding="utf-8") as f:
                return LiveDiskHydrator(json.load(f))
        except Exception:
            pass
    return None

def generate_dashboard_motivation_alerts(player=None, *args, **kwargs):
    """
    Generates dynamic athletic motivation alerts for the dashboard viewports.
    Prioritizes active session state entities to guarantee fresh profile loading.
    """
    disk_player = force_disk_profile_hydration()
    if disk_player is not None:
        player = disk_player
    else:
        resolved_player = None
        for key in ["player", "active_player", "athlete", "current_player"]:
            if key in st.session_state and st.session_state[key] is not None:
                resolved_player = st.session_state[key]
                break
        if resolved_player is not None:
            player = resolved_player
        elif player is None and args:
            player = args[0]
        
    if player is None:
        st.sidebar.info("🏃‍♂️ **Training Hub Matrix:** Securely tracking your athletic milestones. Keep pushing!")
        return
        
    badges_list = getattr(player, "unlocked_badges", [])
    history_list = getattr(player, "history_logs", [])
    metric_totals = getattr(player, "final_metric_data", {})
    lifetime_miles = float(metric_totals.get("lifetime_odometer_miles", 0.0))
    
    has_any_achievements = len(badges_list) > 0 or any("Rewards:" in str(log) for log in history_list)
    
    if not has_any_achievements:
        st.sidebar.info("🏃‍♂️ **Aero-Baseline Status:** Log your initial file telemetry split to unlock your primary performance patches!")
    else:
        st.sidebar.success(f"⚡ **Training Hub Matrix:** Career tracking active. Core odometer metrics and historical training logs synchronized. Stride on!")


def render_showroom_asset(img_path: str, fallback_emoji: str, size_px: int = 65) -> bool:
    """
    Renders an athletic trophy or milestone badge graphic using safe inline 
    base64 streaming data. Falls back to a clean, square dashed box enclosing 
    the native high-fidelity emoji if an asset is missing from disk.
    """
    if img_path and os.path.exists(img_path):
        try:
            with open(img_path, "rb") as f:
                encoded_bytes = base64.b64encode(f.read()).decode("utf-8")
            file_extension = os.path.splitext(img_path)[1].replace(".", "").lower()
            mime_type = f"image/{file_extension}" if file_extension in ["png", "jpg", "jpeg"] else "image/png"
            
            html_stream = (
                f'<div style="display:flex;justify-content:center;align-items:center;'
                f'width:{size_px}px;height:{size_px}px;background:#1a1c23;'
                f'border-radius:8px;border:1px solid #2d313f;">'
                f'<img src="data:{mime_type};base64,{encoded_bytes}" '
                f'style="max-width:100%;max-height:100%;object-fit:contain;border-radius:4px;"/>'
                f'</div>'
            )
            st.markdown(html_stream, unsafe_allow_html=True)
            return True
        except Exception:
            pass

    # High-contrast square dashboard container fallback rule
    html_fallback = (
        f'<div style="display:flex;justify-content:center;align-items:center;'
        f'width:{size_px}px;height:{size_px}px;background:#14161d;'
        f'border:1px dashed #3a3f50;border-radius:8px;font-size:{int(size_px * 0.48)}px;'
        f'line-height:{size_px}px;text-align:center;">'
        f'{fallback_emoji}'
        f'</div>'
    )
    st.markdown(html_fallback, unsafe_allow_html=True)
    return False



import streamlit as st
import pandas as pd
import datetime
import metrics_config as cfg



def parse_pace_to_float(pace_str):
    """Safely converts a string pace format like '7:11/mi' into a float value."""
    if not pace_str or ":" not in str(pace_str):
        return 999.0
    try:
        clean_p = str(pace_str).split("/")[0].strip()
        parts = clean_p.split(":")
        return float(parts[0]) + (float(parts[1]) / 60.0)
    except:
        return 999.0

def render_mile_splits_table(distance, avg_pace_str):
    """Generates a clean, pipes-free monospace layout table of individual mile intervals."""
    try:
        total_miles = max(1, int(float(distance)))
        st.markdown("<p style='font-family: monospace; font-size: 11px; color: #00ffcc; margin: 4px 0;'>📋 MILE-BY-MILE SPLITS MAP</p>", unsafe_allow_html=True)
        
        split_header = f"{'MILE':<8}{'SPLIT PACE':<12}{'CADENCE':<10}"
        st.text(split_header)
        st.markdown("<div style='border-bottom: 1px dashed #2D3748; margin-bottom: 4px;'></div>", unsafe_allow_html=True)
        
        for mile in range(1, total_miles + 1):
            st.text(f"{f'Mile {mile}':<8}{avg_pace_str:<12}{'178 spm':<10}")
    except:
        st.caption("Splits details not available for this record.")











#def render_trophy_showroom_tab(df_instances=None, defense_state="stable", popout_container=None):
def render_trophy_showroom_tab(df_instances=None, defense_state="stable", popout_container=None, widget_id="default"):

    """
    Primary module coordinator rendering the hardware catalog across horizontal tabs.
    Forces deep disk hydration on every render pass to eliminate Streamlit web layout
    caching desynchronizations automatically.
    """
    # Force live file sync from disk database state
    disk_player = force_disk_profile_hydration()
    if disk_player is not None:
        player = disk_player
    else:
        resolved_player = None
        for key in ["player", "active_player", "athlete", "current_player", "df_instances"]:
            if key in st.session_state and st.session_state[key] is not None:
                resolved_player = st.session_state[key]
                break
        if resolved_player is not None:
            player = resolved_player
        elif player is None and args:
            player = args[0]
                
    if player is None:
        st.error("Athlete player profile record could not be hydrated safely. Please verify that your profile database is active.")
        return


    if df_instances is None or (isinstance(df_instances, pd.DataFrame) and df_instances.empty):
        df_instances = st.session_state.get("filtered_df", pd.DataFrame())
                
    if df_instances is None or "award_code" not in df_instances.columns:
        df_instances = pd.DataFrame(columns=["award_code", "date", "metric", "type", "details"])

    # 1. Grab your master activity rows safely from session state
    df_master = st.session_state.get("filtered_df", pd.DataFrame()) 
    
    # 2. Process weekly calculations 
    curr_miles, curr_climb = calculate_current_week_metrics(df_master)
    defense_status, days_elapsed = check_streak_defense_status(df_master)
            
    # 3. Safe profile dictionary lookups with fallback defaults
    profile_dict = st.session_state.get("profile", {})
    p_level = int(profile_dict.get("level") or 1)
    p_xp = int(profile_dict.get("total_xp") or 0)
    p_title = str(profile_dict.get("name") or "Recruit")

    threshold = getattr(cfg, "XP_PER_LEVEL_THRESHOLD", 1000)
    if threshold <= 0:
        threshold = 1000
    p_pct = min(100, max(0, int((p_xp / threshold) * 100)))











    df_instances = df_instances.copy()
    if "Date" in df_instances.columns and "date" not in df_instances.columns:
        df_instances["date"] = df_instances["Date"]

    current_calendar_year = datetime.datetime.now().year
    
    if not df_instances.empty and "date" in df_instances.columns:
        try:
            df_instances['Parsed_Date'] = pd.to_datetime(df_instances['date'], errors='coerce')
            available_years = sorted(df_instances['Parsed_Date'].dt.year.dropna().unique())
            available_years = [int(y) for y in available_years]
        except Exception:
            available_years = []
    else:
        available_years = []
        
    if not available_years:
        available_years = [current_calendar_year]
        
    timeline_options = ["All Time"] + [int(y) for y in reversed(available_years)]

    # =====================================================================
    # STEP 4: TARGETED POPOUT SUB-MENU INJECTION
    # =====================================================================
    sidebar_target = popout_container if popout_container is not None else st.sidebar
    
    with sidebar_target:
        st.markdown("### ENGINE STATUS")
        st.markdown(f"**LVL {p_level}** • {p_title}")
        st.markdown("👑 **ELITE_OLYMPIAN UNLOCKED**")
        
        st.progress(p_pct / 100.0)
        st.caption(f"XP: {p_xp:,} / {threshold:,} ({p_pct}%)")
        
        if defense_status == "Fortified" or defense_status == "Stable" or defense_status is True:
            st.success("✅ **STREAK SECURE:** Active consistency patches are safely mounted and stable.")
        else:
            st.warning("⚠️ **STREAK VULNERABLE:** Consistency metrics are dropping context thresholds.")
            
        st.markdown("---")
        
        # Call requirements renderer streaming your custom parameters
        render_sidebar_requirements_manual(curr_miles, curr_climb, df_instances, target_container=sidebar_target)
        
        st.markdown("---")

       



        # 1. Initialize a single, shared cross-viewport data pipeline slot
        if "active_lens_year" not in st.session_state:
            st.session_state["active_lens_year"] = "All Time"
        
        # 2. Callback function to ensure both selectboxes always match when clicked
        def sync_seasonal_lens_filters():
            # Detect which widget was interacted with and copy its state over globally
            current_key = f"showroom_lens_widget_instance_{widget_id}"
            if current_key in st.session_state:
                st.session_state["active_lens_year"] = st.session_state[current_key]
        
        # 3. Find the current universal selection index
        try:
            default_index = timeline_options.index(st.session_state["active_lens_year"])
        except ValueError:
            default_index = 0
        
        # 4. Render the selectbox cleanly without ID collision or state fragmentation
        st.selectbox(
            "📅 Select Seasonal Lens Timeline:",
            options=timeline_options,
            index=default_index,
            key=f"showroom_lens_widget_instance_{widget_id}",  # Avoids duplicate key crash
            on_change=sync_seasonal_lens_filters              # Syncs both drop-downs immediately
        )
        
        # 5. Point the rest of your script to the shared universal selection value
        selected_season_year = st.session_state["active_lens_year"]










        ###SELECT DISPLAY HARDWARE TYPE
        ######hardware_filter_choices = ["Trophies", "Medals", "Ribbons", "Patches"]
        ######selected_hardware_types = st.multiselect(
        ######    "🛡️ Filter Showcase Assets:",
        ######    options=hardware_filter_choices,
        ######    default=hardware_filter_choices
        ######)
        
        year_val = None if selected_season_year == "All Time" else int(selected_season_year)
        pr_data = calculate_personal_records(df_master, target_year=year_val)
        
        if not df_instances.empty and 'Parsed_Date' in df_instances.columns:
            if selected_season_year == "All Time":
                df_filtered_display = df_instances.copy()
            else:
                df_filtered_display = df_instances[df_instances['Parsed_Date'].dt.year == int(selected_season_year)]
        else:
            df_filtered_display = df_instances.copy()

        type_conversion_mapping = {"Trophies": "trophy", "Medals": "medal", "Ribbons": "ribbon", "Patches": "patch"}
        ####active_type_strings = [type_conversion_mapping[lbl] for lbl in selected_hardware_types]

        ####if not df_filtered_display.empty and "type" in df_filtered_display.columns:
        ####    df_filtered_display = df_filtered_display[df_filtered_display["type"].str.lower().isin(active_type_strings)]
        
        st.markdown("---")
        st.info(f"""
        📊 **Active Season Metrics ({selected_season_year}):**
        * Total Hardware Unlocked: `{len(df_filtered_display)}`
        * Condition Profile Vector: `{str(defense_state).upper()}`
        """)



    st.markdown("## 🏅 Hardware Showroom & Achievements Matrix")
    st.markdown("Track your unlocked single-run performance patches, cumulative milestone shelves, and coveted elite targets.")
    st.markdown("---")





























    # Instantiate horizontal subview selector tabs
    patch_tab, trophy_tab, milestone_tab = st.tabs([
        "🛡️ Performance Patches", 
        "🏆 Career Trophy Cabinet", 
        "🎗️ Weekly & Elite Milestones"
    ])

    # =========================================================================
    # 🛡️ VIEW PANEL: SINGLE-RUN PERFORMANCE PATCHES
    # =========================================================================
    # =============================================================================
    # CODE BLOCK 1: STATE INITIALIZATION & SETUP
    # =============================================================================
    if "selected_patch_id" not in st.session_state:
        st.session_state.selected_patch_id = None
    if "selected_patch_name" not in st.session_state:
        st.session_state.selected_patch_name = None

    # Track distinct UI rendering contexts across function execution loops
    current_w_id = locals().get("widget_id", "default_showroom")
    # =============================================================================
    # CODE BLOCK 2: DATA EXTRACTION & TIMELINE FILTERING
    # =============================================================================
    patch_categories = FINAL_METRIC_CONFIG.get("single_run_patches", {})
    raw_history = getattr(player, "history_logs", [])
    raw_badges = getattr(player, "unlocked_badges", [])
    
    # Safe fallback unit indicator mapping
    unit_abbr = locals().get("unit_abbr", "mi")

    # Filter arrays cleanly based on your calendar filter settings
    if selected_season_year == "All Time":
        history_logs = raw_history
        badges_list = raw_badges
    else:
        year_str = str(selected_season_year)
        history_logs = [log for log in raw_history if year_str in str(log)]
        badges_list = [badge for badge in raw_badges if year_str in str(badge)]
    # =============================================================================
    # CODE BLOCK 3: SQUARE RESPONSIVE GRID LAYOUT & DUAL-CHUNK PANELS
    # =============================================================================
    with patch_tab:
        # Split layout view panel generation rules
        if st.session_state.selected_patch_id:
            left_layout, right_layout = st.columns([2, 1.2])
        else:
            left_layout = st.container()
            right_layout = None

        # --- LEFT SIDE: Patches Visual Matrix Card Grid ---
        with left_layout:
            st.markdown("### 🛡 Single-Run Performance Patches")
            st.caption("Earned by triggering specialized athletic criteria configurations.")
            
            for cat_id, cat_meta in patch_categories.items():
                st.markdown(f"#### {cat_meta['name']}")
                tiers = cat_meta.get("tiers", [])
                
                for i in range(0, len(tiers), 3):
                    row_slice = tiers[i:i+3]
                    cols = st.columns(3)
                    
                    for idx, tier in enumerate(row_slice):
                        with cols[idx]:
                            # Container structural border holds the items into square groupings
                            with st.container(border=True):
                                earning_activities = []
                                for log in history_logs:
                                    log_str = str(log).lower()
                                    if (tier["id"].lower() in log_str) or (tier["name"].lower() in log_str):
                                        earning_activities.append(log)
                                        
                                unlocked_count = len(earning_activities)
                                is_unlocked = unlocked_count > 0
                                
                                grid_col1, grid_col2 = st.columns([1, 3.2])
                                with grid_col1:
                                    render_showroom_asset(
                                        img_path=tier.get("img_path"), 
                                        fallback_emoji=tier.get("icon", "🛡️"), 
                                        size_px=65
                                    )
                                with grid_col2:
                                    if is_unlocked:
                                        st.markdown(f"**{tier['name']}** <span style='color:#2ecc71;font-weight:bold;'>x{unlocked_count}</span>", unsafe_allow_html=True)
                                        st.caption(f"{tier['icon']} Verified Clear Profile")
                                        st.markdown(f'<p style="font-size:11px;color:#808495;margin-bottom:8px;">{tier["desc"]}</p>', unsafe_allow_html=True)
                                        
                                        # FIXED: Removed use_container_width=True to lock width boundaries to static dimensions
                                        btn_grid_key = f"btn_{tier['id']}_{selected_season_year}_{current_w_id}_{cat_id}_{i}_{idx}"
                                        if st.button(f"👁️ View Runs", key=btn_grid_key):
                                            st.session_state.selected_patch_id = tier['id']
                                            st.session_state.selected_patch_name = tier['name']
                                            st.rerun()
                                    else:
                                        st.markdown(f'<span style="opacity:0.4;font-weight:bold;">{tier["name"]}</span>', unsafe_allow_html=True)
                                        st.caption("🔒 Locked Objective")
                                        st.markdown(f'<p style="font-size:11px;color:gray;margin:0;">{tier["desc"]}</p>', unsafe_allow_html=True)

        # --- RIGHT SIDE: Detailed Breakdown Summary Deck ---
        if right_layout and st.session_state.selected_patch_id:
            with right_layout:
                with st.container(border=True):
                    st.markdown(f"### 🛡️ Patch Details")
                    st.caption(f"Selected: **{st.session_state.selected_patch_name}**")
                    
                    if st.button("Close Panel X", key=f"close_panel_key_{current_w_id}", use_container_width=True):
                        st.session_state.selected_patch_id = None
                        st.session_state.selected_patch_name = None
                        st.rerun()
                        
                    st.divider()
                    
                    active_id = st.session_state.selected_patch_id.lower()
                    panel_runs = [log for log in history_logs if active_id in str(log).lower()]
                            
                    if not panel_runs:
                        st.info("No matching individual activities found for this filter.")
                    else:
                        for run_idx, run in enumerate(panel_runs):
                            r_date = run.get("Date", run.get("date", "N/A"))
                            r_title = run.get("Name", run.get("Activity Type", run.get("title", f"Run #{run_idx + 1}")))
                            r_dist = run.get("Distance (Miles)", run.get("Display_Distance", run.get("distance", 0.0)))
                            r_time = run.get("Duration", run.get("duration", "--:--"))
                            r_pace = run.get("Pace", run.get("pace", "—"))
                            
                            r_date_str = str(r_date).split(" ") if " " in str(r_date) else str(r_date)
                            
                            # CHUNK 1: OVERVIEW METRIC SUMMARY
                            st.markdown(f"📅 **Date:** `{r_date_str}` | **Workout:** **{r_title}**")
                            st.markdown(f"🏃 **Distance:** `{r_dist} {unit_abbr}` | ⏱️ **Duration:** `{r_time}` | ⏱️ **Pace:** `{r_pace}`")
                            
                            # CHUNK 2: NATIVE BREAKDOWN DROPDOWN
                            with st.expander(f"📋 Activity Log Summary:"):
                                #if run:
                                #    show_run_lap_breakdown(run, unit_abbr=unit_abbr)
                                #    render_zone_octagon_display(run)
                                # 🏁 Loop opens cleanly
                                matched_run = run
                
                                # Create a distinct visual header for multi-activity days
                                #if len(matched_run) > 1:
                                #    st.markdown(f"#### 🏃<200d>♂️ Workout Activity #{run_idx + 1}")
                
                                # Single Run Elevation parsing (Moved inside loop)
                                #run_elevation = 0.0
                                #if elev_columns:
                                #    raw_elev_val = matched_run.get(elev_columns[0], "0")
                                #    cleaned_run_elev = ''.join(c for c in str(raw_elev_val) if c.isdigit() or c == '.')
                                #    parsed_elev = pd.to_numeric(cleaned_run_elev, errors='coerce')
                                #    if pd.notna(parsed_elev):
                                #        run_elevation = parsed_elev
                
                                if "splits" in matched_run and isinstance(matched_run["splits"], list) and len(matched_run["splits"]) > 0:
                                    try:
                                        splits_df = pd.DataFrame(matched_run["splits"])
                                        splits_df['Split Mile'] = "M" + splits_df['split_num'].astype(str)
                
                                        # 🚨 THE DIRECT COLUMN CLEANUP: Extract heart rate directly by string name safely
                                        # If 'avg_heart_rate' isn't found, check for 'average_heart_rate' or default to 120
                                        if 'avg_heart_rate' in splits_df.columns:
                                            raw_hr_series = splits_df['avg_heart_rate']
                                        elif 'average_heart_rate' in splits_df.columns:
                                            raw_hr_series = splits_df['average_heart_rate']
                                        else:
                                            raw_hr_series = pd.Series([120] * len(splits_df))
                                        
                                        # Ensure 'max_heart_rate' exists per split for line graph rendering
                                        if 'max_heart_rate' not in splits_df.columns:
                                            splits_df['max_heart_rate'] = raw_hr_series

                                        # Clean Heart Rate Color Assigner with explicit numeric coercion
                                        def assign_bar_color_by_hr(avg_hr):
                                            try:
                                                hr = int(float(avg_hr))
                                                # Call your centralized theme function!
                                                bg_color, _, _ = get_hr_zone_style(hr)
                                                return bg_color
                                            except:
                                                return "#A0AEC0" # Distinct grey fallback so you know if data fails!
                
                                        # Map colors directly over your cleaned series
                                        splits_df['Zone_Color'] = raw_hr_series.apply(assign_bar_color_by_hr)
                
                                        # Safe pace formatting to numeric minutes for the Y-axis heights
                                        def safe_pace_to_mins(p_val):
                                            try:
                                                parts = str(p_val).strip().split(':')
                                                if len(parts) == 3:   # HH:MM:SS
                                                    return int(parts[0])*60 + int(parts[1]) + int(parts[2])/60.0
                                                elif len(parts) == 2: # MM:SS
                                                    return int(parts[0]) + int(parts[1])/60.0
                                                return float(p_val)
                                            except:
                                                return 8.0
                
                                        splits_df['Pace (Minutes)'] = splits_df['pace'].apply(safe_pace_to_mins)
                
                                        st.caption(f"⏱️      Lap Split Profiles - Activity #{run_idx + 1} (Bars = Pace, Line = Max HR)")
                
                                        import altair as alt
                                        
                                        # Base shared X-axis definition
                                        base_chart = alt.Chart(splits_df).encode(
                                            x=alt.X('Split Mile:N', sort=None, title="Workout Segment")
                                        )

                                        # Synchronized tooltips
                                        shared_tooltips = [
                                            alt.Tooltip('Split Mile', title='Split'),
                                            alt.Tooltip('pace', title='Pace'),
                                            alt.Tooltip('avg_heart_rate:Q', title='Avg Heart Rate (bpm)') if 'avg_heart_rate' in splits_df.columns else alt.Tooltip('average_heart_rate:Q', title='Avg Heart Rate (bpm)'),
                                            alt.Tooltip('max_heart_rate:Q', title='Max Peak HR (bpm)')
                                        ]

                                        # Left axis: Pace Bars
                                        bar_layer = base_chart.mark_bar(opacity=0.85).encode(
                                            y=alt.Y('Pace (Minutes):Q', title="Pace Minutes"),
                                            color=alt.Color('Zone_Color:N').scale(None),
                                            tooltip=shared_tooltips
                                        )

                                        # Right axis: Max HR Trendline
                                        line_layer = base_chart.mark_line(color="#2B6CB0", strokeWidth=3.5, interpolate="monotone").encode(
                                            y=alt.Y('max_heart_rate:Q', title="Max Heart Rate (bpm)", scale=alt.Scale(zero=False)),
                                            tooltip=shared_tooltips
                                        )

                                        # Visual target nodes on line points
                                        point_layer = base_chart.mark_point(color="#2B6CB0", size=60, filled=True).encode(
                                            y=alt.Y('max_heart_rate:Q'),
                                            tooltip=shared_tooltips
                                        )

                                        # Combine chart layers and resolve independent axes
                                        altair_combo_chart = alt.layer(
                                            bar_layer, line_layer, point_layer
                                        ).resolve_scale(
                                            y='independent'
                                        ).properties(height=320)
                
                                        # Render fresh by avoiding Streamlit's old layout memory
                                        st.altair_chart(altair_combo_chart, theme=None, key=f"split_chart_refresh_id_{run_idx}_v3")
                
                                    except Exception as e:
                                        st.error(f"❌ Chart Processing Error: {str(e)}")
                
                                # Metric visualization metrics blocks (Moved inside loop)
                                #st.metric(f"Activity #{run_idx + 1} Distance", f"{matched_run['Display_Distance']:.2f} {unit_abbr}")
                                #st.metric(f"Activity #{run_idx + 1} Duration", matched_run.get('Duration', 'N/A'))
                                #if run_elevation > 0:
                                #    st.metric(f"Activity #{run_idx + 1} Elevation Gain", f"{run_elevation:,.0f} ft")
                
                                # ------------------------------------------------------------------
                                # 💓 NEW ADDITION: DYNAMIC MAX HEART RATE INDICATOR
                                # ------------------------------------------------------------------
                                max_hr_val = matched_run.get("max_heart_rate")
                                splits_list = matched_run.get("splits", [])
                
                                # If top-level max HR isn't populated, scan nested split lap metadata dynamically
                                if not max_hr_val and isinstance(splits_list, list) and splits_list:
                                    valid_lap_maxes = [
                                        int(item["max_heart_rate"])
                                        for item in splits_list
                                        if isinstance(item, dict) and item.get("max_heart_rate")
                                    ]
                                    if valid_lap_maxes:
                                        max_hr_val = max(valid_lap_maxes)
                
                                if max_hr_val:
                                    try:
                                        # Reuses the exact function definition from upload_ui.py
                                        bg_color, zone_lbl, text_color = get_hr_zone_style(int(max_hr_val))
                
                                        hr_html = (
                                            f'<div style="background-color:{bg_color}; color:{text_color}; '
                                            f'padding:6px 12px; border-radius:8px; font-weight:bold; '
                                            f'font-size:14px; display:inline-block; margin-top:8px; margin-bottom:12px; '
                                            f'border: 1px solid rgba(0,0,0,0.1);">'
                                            f'💓 Peak Max HR: {max_hr_val} bpm — {zone_lbl}'
                                            f'</div>'
                                        )
                                        st.markdown(hr_html, unsafe_allow_html=True)
                                    except Exception:
                                        # Safe local fallback if an import path bottleneck arises
                                        st.caption(f"💓 Peak Max HR: {max_hr_val} bpm")
                
                                try:
                                    if matched_run:
                                        show_run_lap_breakdown(matched_run, unit_abbr=unit_abbr)
                                        render_zone_octagon_display(matched_run)
                
                                except Exception:
                                    pass

                               # if 'pace' in matched_run:
                               #     flat_pace = pace_str_to_minutes(matched_run['pace'])
                               #     st.metric("Flat Overall Pace", f"{matched_run['pace']} min/{unit_abbr.lower()}")
                
                               # # Grade Adjusted Pace (GAP) calculation output
                               # gap_pace = calculate_grade_adjusted_pace(flat_pace, run_elevation, matched_run['Display_Distance'])
                               # st.metric("🔋 Grade-Adjusted Pace (GAP)", f"{minutes_to_pace_str(gap_pace)} min/{unit_abbr.lower()}", delta=f"{run_elevation:,.0f} ft climbing effort penalty" if run_elevation > 0 else None, delta_color="inverse")
                
                               # if run_elevation > 0:
                               #     st.metric("Elevation Gain", f"{run_elevation:,.0f} ft")
                               #                         
                               # st.markdown('<div style="margin-bottom:24px; border-bottom:2px solid #2c313c; padding-top:12px;"></div>', unsafe_allow_html=True)




















    # =========================================================================
    # 🏆 VIEW PANEL: CUMULATIVE LIFELONG CAREER TROPHY CABINET
    # =========================================================================
    with trophy_tab:
        st.markdown("### 🏆 Cumulative Career Trophy Cabinet")
        st.caption("Long-term milestone containers reflecting accumulated totals logged over your active training career.")
        
            

        metric_totals = getattr(player, "final_metric_data", {})
        
        # Try reading from final_metric_data first; fallback to dynamic calculation if missing
        lifetime_miles = float(metric_totals.get("lifetime_odometer_miles", 0.0))
        lifetime_elevation = float(metric_totals.get("lifetime_elevation_gain_ft", metric_totals.get("lifetime_elevation_gain", 0.0)))
        lifetime_calories = float(metric_totals.get("lifetime_calories_burned", 0.0))
        
        # 🟢 FIXEDFALLBACK CALCULATOR: If database metrics are zeroed out, dynamically sum history records
        if lifetime_miles == 0.0 or lifetime_calories == 0.0:
            # Reset values to ensure an accurate fresh calculation loop
            calc_miles = 0.0
            calc_ele = 0.0
            calc_kcal = 0.0
            
            for log_item in getattr(player, "history_logs", []):
                if isinstance(log_item, dict):
                    # 1. Pull distance
                    m_val = float(log_item.get("Distance (Miles)", log_item.get("distance_mi", 0.0)))
                    calc_miles += m_val
                    
                    # 2. Pull calories safely (Fallback to estimating 100 kcal per mile if empty or 0)
                    c_val = float(log_item.get("calories", log_item.get("Calories", 0.0)))
                    if c_val <= 0.0 and m_val > 0.0:
                        c_val = m_val * 100.0
                    calc_kcal += c_val
                    
                    # 3. Pull elevation climbing feet safely
                    raw_ele = log_item.get("Elevation (ft)", log_item.get("ele", 0.0))
                    if isinstance(raw_ele, str):
                        try:
                            calc_ele += float(raw_ele.replace("+","").replace("ft","").replace(",","").strip())
                        except ValueError: pass
                    else:
                        calc_ele += float(raw_ele)
                        
            # Apply our freshly calculated historical totals if the file logs held data
            if lifetime_miles == 0.0:
                lifetime_miles = calc_miles
            if lifetime_elevation == 0.0:
                lifetime_elevation = calc_ele
            if lifetime_calories == 0.0:
                lifetime_calories = calc_kcal
        


        # =========================================================================
        # 🟢 FIXED UNIVERSAL INNER LOOP TERMINAL FOR SHOWROOM SHELVES
        # =========================================================================
        raw_cabinet = FINAL_METRIC_CONFIG.get("trophy_cabinet", {})
        
        # Normalize the data structure: Convert cabinet_shelves safely whether it is a dict or a list
        cabinet_shelves_dict = {}
        if isinstance(raw_cabinet, dict):
            cabinet_shelves_dict = raw_cabinet
        elif isinstance(raw_cabinet, list):
            # If your config stores them as a list of dictionaries, map them out cleanly by ID
            for idx, item in enumerate(raw_cabinet):
                s_id = item.get("id", f"shelf_{idx}")
                cabinet_shelves_dict[s_id] = item
        else:
            # Hard-coded ultimate safety backup fallback if your config file is completely unreadable
            cabinet_shelves_dict = {
                "shelf_a_mileage": {"name": "Cumulative Mileage Shelf", "tiers": FINAL_METRIC_CONFIG.get("mileage_tiers", [])},
                "shelf_b_elevation": {"name": "Cumulative Elevation Shelf", "tiers": FINAL_METRIC_CONFIG.get("elevation_tiers", [])},
                "shelf_c_calories": {"name": "The Burn Menu Shelf", "trophies": FINAL_METRIC_CONFIG.get("calorie_trophies", [])}
            }
        
        # Loop through every resolved shelf structural container explicitly
        for shelf_id, shelf_meta in cabinet_shelves_dict.items():
            st.markdown(f"#### {shelf_meta.get('name', shelf_id.replace('_',' ').title())}")
            
            # 1. Determine contextual unit parameters based on active shelf attributes
            if "mileage" in shelf_id.lower() or "mile" in shelf_meta.get('name', '').lower():
                current_total = lifetime_miles
                unit_label = "miles"
            elif "elevation" in shelf_id.lower() or "elev" in shelf_meta.get('name', '').lower():
                current_total = lifetime_elevation
                unit_label = "ft"
            else:
                current_total = lifetime_calories
                unit_label = "kcal"
        
            st.markdown(f"`Accumulated Lifetime Volume: {current_total:,.1f} {unit_label}`")
        
            # 2. Extract milestones across all possible schema configurations
            trophies = shelf_meta.get("tiers", shelf_meta.get("trophies", shelf_meta.get("milestones", [])))
            
            # Safety fallback check: if the shelf object itself is a list of trophies directly
            if isinstance(shelf_meta, list):
                trophies = shelf_meta
        
            # Safe extraction helper to clean up mixed data types inside config fields
            def get_trophy_value(t_obj):
                val = t_obj.get("threshold", t_obj.get("min_val", t_obj.get("value", t_obj.get("milestone", 0))))
                try:
                    return float(str(val).replace(",", "").strip())
                except (ValueError, TypeError):
                    return 0.0
        
            # 3. Extract values dynamically matching current performance totals
            unlocked_trophies = []
            for t in trophies:
                if current_total >= get_trophy_value(t):
                    unlocked_trophies.append(t)
                    
            # Calculate your absolute peak rank trophy safely
            highest_earned_trophy = max(
                unlocked_trophies, 
                key=get_trophy_value, 
                default=None
            )
        
            # 4. Streamlit Grid Interaction Renderer
            if len(trophies) == 0:
                st.caption("ℹ️ No milestone records found inside this shelf configuration profile.")
            else:
                for i in range(0, len(trophies), 4):
                    row_slice = trophies[i:i+4]
                    cols = st.columns(4)
                    for idx, trophy in enumerate(row_slice):
                        with cols[idx]:
                            with st.container(border=True):
                                t_bound = get_trophy_value(trophy)
                                
                                is_highest_peak = False
                                is_past_stepping_stone = False
                                
                                if highest_earned_trophy:
                                    h_bound = get_trophy_value(highest_earned_trophy)
                                    if t_bound == h_bound:
                                        is_highest_peak = True
                                    elif t_bound < h_bound:
                                        is_past_stepping_stone = True
                                
                                t_col1, t_col2 = st.columns([1, 2.5])
                                with t_col1:
                                    resolved_img_path = trophy.get("img_path", trophy.get("pic", trophy.get("img")))
                                    render_showroom_asset(
                                        img_path=resolved_img_path,
                                        fallback_emoji=trophy.get("icon", trophy.get("emoji", "🏆")),
                                        size_px=60
                                    )
                                with t_col2:
                                    if is_highest_peak:
                                        st.markdown(f"👑 **{trophy.get('name', 'Peak')}**")
                                        st.success("🎯 Peak Rank")
                                    elif is_past_stepping_stone:
                                        st.markdown(f"**{trophy.get('name', 'Unlocked')}**")
                                        st.caption("🛡️ Milestone Met")
                                    else:
                                        st.markdown(f'<span style="opacity:0.4;font-weight:bold;">{trophy.get("name", "Locked")}</span>', unsafe_allow_html=True)
                                        st.caption(f"🔒 Requires {int(t_bound):,} {unit_label}")
            st.write("")
            st.markdown("---")


#############
    # =========================================================================
    # 🎗️ VIEW PANEL: WEEKLY REWARDS & COVETED ELITE PERFORMANCE TARGETS
    # =========================================================================
    with milestone_tab:
        st.markdown("### 🎗️ Weekly Progress Thresholds & Elite Milestones")
        st.caption("Short-term high-volume week blocks and historic elite running achievements.")

        # 📥 BACKEND CALCULATION STEP: Group all history logs by calendar week buckets
        import datetime as dt
        weekly_mileage_tracker = {}    # Key: (year, week_num) -> Value: float miles
        weekly_elevation_tracker = {}  # Key: (year, week_num) -> Value: float feet
        weekly_runs_registry = {}      # Key: (year, week_num) -> Value: list of run logs
        available_years_set = set()    # Track distinct calendar years found in history

        for log_item in getattr(player, 'history_logs', []):
            log_date_str = None
            log_miles = 0.0
            log_ele = 0.0
            
            if isinstance(log_item, dict):
                log_date_str = log_item.get("Date", "")
                log_miles = float(log_item.get("Distance (Miles)", log_item.get("distance_mi", 0.0)))
                
                raw_ele = log_item.get("Elevation (ft)", log_item.get("ele", 0.0))
                if isinstance(raw_ele, str):
                    try:
                        log_ele = float(raw_ele.replace("+","").replace("ft","").replace(",","").strip())
                    except ValueError: pass
                else:
                    log_ele = float(raw_ele)
            elif isinstance(log_item, str):
                import re
                date_match = re.search(r'\[([0-9-]+)\]', log_item)
                if date_match:
                    log_date_str = date_match.group(1)
                
                d_match = re.search(r'(?:Run|run|ran|distance):?\s*([0-9.]+)', log_item, re.IGNORECASE)
                if not d_match:
                    d_match = re.search(r'([0-9.]+)\s*(?:miles|mi)', log_item, re.IGNORECASE)
                if d_match:
                    log_miles = float(d_match.group(1))

            # Add the metrics to their respective ISO Calendar Week bucket
            if log_date_str:
                try:
                    clean_date = dt.datetime.strptime(str(log_date_str)[:10], '%Y-%m-%d')
                    iso_year, iso_week, _ = clean_date.isocalendar()
                    bucket_key = (iso_year, iso_week)
                    
                    available_years_set.add(iso_year)
                    
                    if log_miles > 0.0:
                        weekly_mileage_tracker[bucket_key] = weekly_mileage_tracker.get(bucket_key, 0.0) + log_miles
                    if log_ele > 0.0:
                        weekly_elevation_tracker[bucket_key] = weekly_elevation_tracker.get(bucket_key, 0.0) + log_ele
                    
                    if bucket_key not in weekly_runs_registry:
                        weekly_runs_registry[bucket_key] = []
                    weekly_runs_registry[bucket_key].append(log_item)
                except Exception:
                    pass

        # 📅 MASTER OVERVIEW TIMELINE FILTER: High-level selection outside the individual cards
        sorted_years = sorted(list(available_years_set), reverse=True)
        year_options = ["📅 All Years Overview"] + [str(yr) for yr in sorted_years]
        
        selected_overview_year = st.selectbox(
            "🔍 Select Seasonal Timeline Filter (Overview):",
            year_options,
            key="master_showroom_milestone_overview_year"
        )
        st.write("")

        # ─── SPLIT DETECTOR: Create Side-by-Side View Ports ───
        is_inspecting = "inline_active_week" in st.session_state and st.session_state["inline_active_week"] is not None
        
        if is_inspecting:
            main_left_col, main_right_col = st.columns([1.2, 1.0])
        else:
            main_left_col = st.container()

        # ─── LEFT SIDE CONTENT PANEL: REWARDS CONFIGURATORS ───
        with main_left_col:
            split_col_1, split_col_2 = st.columns(2)
        # 🟢 CALLBACK FUNCTIONS: Extract week/year and protect background memory allocations
        def on_select_mil_week(key_id):
            chosen = st.session_state[key_id]
            if chosen != "-- Select a Week to Inspect --":
                clean_text = str(chosen).replace("Week ", "")
                picked_part = clean_text.split(" (")
                p_wk, p_yr = map(int, picked_part[0].split(", "))
                st.session_state["inline_active_week"] = (p_yr, p_wk)

        # COLUMN 1: WEEKLY MILEAGE STRINGS INDEX
        with split_col_1:
            st.markdown("#### 📅 Weekly Mileage Ribbons")
            with st.expander("Review Mileage Milestones", expanded=True):
                sorted_mileage_rewards = sorted(WEEKLY_MILEAGE_REWARDS, key=lambda x: float(x.get("miles", 0.0)))
                
                for idx, reward in enumerate(sorted_mileage_rewards):
                    try:
                        target_miles = float(reward.get("miles", 0.0))
                    except (ValueError, TypeError):
                        target_miles = 0.0
                    
                    # 🟢 BRACKET FILTER: Strict limits block lower milestones from bleeding upward
                    upper_miles_cap = float('inf')
                    if idx + 1 < len(sorted_mileage_rewards):
                        upper_miles_cap = float(sorted_mileage_rewards[idx+1].get("miles", float('inf')))
                    
                    # Gather keys matching the metric range bounds
                    base_weeks = [k for k, total in weekly_mileage_tracker.items() if target_miles <= total < upper_miles_cap]
                    
                    # 🟢 TIMELINE OVERVIEW COUPLING: Filter matching elements by the master year selectbox
                    if selected_overview_year != "📅 All Years Overview":
                        base_weeks = [k for k in base_weeks if k[0] == int(selected_overview_year)]
                        
                    mileage_weeks_met = sorted(base_weeks, key=lambda x: (x[0], x[1]), reverse=True)
                    mileage_frequency = len(mileage_weeks_met)
                    mileage_unlocked = mileage_frequency > 0
                    
                    r_col1, r_col2 = st.columns([1, 4.5])
                    with r_col1:
                        render_showroom_asset(
                            img_path=reward.get("img_path"),
                            fallback_emoji=reward.get("icon", "🎗️"),
                            size_px=45
                        )
                    with r_col2:
                        if mileage_unlocked:
                            st.markdown(f"**{reward['title']}** (`{reward['miles']}+ mi`) — **{mileage_frequency}x**")
                            
                            # 🟢 DROPDOWN IS SPECIFIC WEEKS: Populates choices for the active year space
                            options = ["-- Select a Week to Inspect --"] + [f"Week {wk}, {yr} ({weekly_mileage_tracker[(yr, wk)]:.1f} mi)" for yr, wk in mileage_weeks_met]
                            st.selectbox(
                                "📅 View Achieved Weeks:", 
                                options, 
                                key=f"sel_mil_{reward['title']}", 
                                on_change=on_select_mil_week, 
                                args=(f"sel_mil_{reward['title']}",)
                            )
                        else:
                            st.markdown(f'<span style="opacity:0.4;font-weight:bold;">🔒 {reward["title"]}</span>', unsafe_allow_html=True)
                            st.markdown(f'<p style="font-size:11px;color:#808495;margin:0;opacity:0.4;">Requires {reward["miles"]} miles</p>', unsafe_allow_html=True)
                            
                    st.markdown('<div style="margin-bottom:8px;border-bottom:1px solid #1f232a;opacity:0.15;"></div>', unsafe_allow_html=True)

        # COLUMN 2: WEEKLY VERTICAL STRINGS INDEX
        with split_col_2:
            st.markdown("#### 🏔️ Weekly Elevation Milestones")
            with st.expander("Review Vertical Milestones", expanded=True):
                def get_climb_val(r):
                    return float(str(r.get("climb_ft", "0")).replace(",", "").strip())
                sorted_elevation_rewards = sorted(WEEKLY_ELEVATION_REWARDS, key=get_climb_val)
                
                for idx, reward in enumerate(sorted_elevation_rewards):
                    try:
                        target_climb = get_climb_val(reward)
                    except (ValueError, TypeError):
                        target_climb = 0.0
                    
                    # 🟢 BRACKET FILTER: Strict limits block lower milestones from bleeding upward
                    upper_climb_cap = float('inf')
                    if idx + 1 < len(sorted_elevation_rewards):
                        upper_climb_cap = get_climb_val(sorted_elevation_rewards[idx+1])
                    
                    # Gather keys matching the metric range bounds
                    base_weeks = [k for k, total in weekly_elevation_tracker.items() if target_climb <= total < upper_climb_cap]
                    
                    # 🟢 TIMELINE OVERVIEW COUPLING: Filter matching elements by the master year selectbox
                    if selected_overview_year != "📅 All Years Overview":
                        base_weeks = [k for k in base_weeks if k[0] == int(selected_overview_year)]
                        
                    elevation_weeks_met = sorted(base_weeks, key=lambda x: (x[0], x[1]), reverse=True)
                    elevation_frequency = len(elevation_weeks_met)
                    elevation_unlocked = elevation_frequency > 0
                    
                    r_col1, r_col2 = st.columns([1, 4.5])
                    with r_col1:
                        render_showroom_asset(
                            img_path=reward.get("img_path"),
                            fallback_emoji=reward.get("icon", "🔰"),
                            size_px=45
                        )
                    with r_col2:
                        if elevation_unlocked:
                            st.markdown(f"**{reward['title']}** (`{reward['climb_ft']}+ ft`) — **{elevation_frequency}x**")
                            
                            # 🟢 DROPDOWN IS SPECIFIC WEEKS: Populates choices for the active year space
                            options = ["-- Select a Week to Inspect --"] + [f"Week {wk}, {yr} ({weekly_elevation_tracker[(yr, wk)]:,} ft)" for yr, wk in elevation_weeks_met]
                            st.selectbox(
                                "📅 View Achieved Weeks:", 
                                options, 
                                key=f"sel_elv_{reward['title']}", 
                                on_change=on_select_mil_week, 
                                args=(f"sel_elv_{reward['title']}",)
                            )
                        else:
                            st.markdown(f'<span style="opacity:0.4;font-weight:bold;">🔒 {reward["title"]}</span>', unsafe_allow_html=True)
                            st.markdown(f'<p style="font-size:11px;color:#808495;margin:0;opacity:0.4;">Requires {reward["climb_ft"]} ft</p>', unsafe_allow_html=True)
                            
                    st.markdown('<div style="margin-bottom:8px;border-bottom:1px solid #1f232a;opacity:0.15;"></div>', unsafe_allow_html=True)
        # ─── RIGHT SIDE: Detailed Breakdown Summary Deck (Dropdown Container Rows Style) ───
        if is_inspecting:
            with main_right_col:
                with st.container(border=True):
                    tgt_year, tgt_week = st.session_state["inline_active_week"]
                    panel_runs = weekly_runs_registry.get((tgt_year, tgt_week), [])
                    
                    st.markdown(f"### 🛡️ Weekly Milestone Details")
                    st.caption(f"Selected Time Block: **Week {tgt_week}, {tgt_year}**")
                    
                    if st.button("Close Panel X", key=f"close_panel_key_week_{tgt_week}_{tgt_year}", use_container_width=True):
                        st.session_state["inline_active_week"] = None
                        st.rerun()
                        
                    st.divider()
                    
                    if not panel_runs:
                        st.info("No individual activities found for this time block.")
                    else:
                        def get_run_date_sorting(r_obj):
                            if isinstance(r_obj, dict): return r_obj.get("Date", "9999")
                            return "9999"
                        sorted_runs = sorted(panel_runs, key=get_run_date_sorting)
                        
                        for run_idx, run in enumerate(sorted_runs):
                            if isinstance(run, dict):
                                r_date = run.get("Date", "N/A")
                                r_title = run.get("Name", "Standard Run")
                                r_dist = run.get("Distance (Miles)", run.get("distance_mi", 0.0))
                                r_time = run.get("Duration", "--:--")
                                r_pace = run.get("pace", "—")
                                r_elev = run.get("Elevation (ft)", "0 ft")
                                r_date_str = str(r_date).split(" ") if " " in str(r_date) else str(r_date)
                                
                                # CHUNK 1: OVERVIEW FLAT METRIC SUMMARY BAR
                                st.markdown(f"📅 **Date:** `{r_date_str}` | **Workout:** **{r_title}**")
                                st.markdown(f"🏃 **Distance:** `{r_dist} mi` | ⏱️ **Duration:** `{r_time}` | ⚡ **Pace:** `{r_pace} /mi` | ⛰️ `{r_elev}`")
                                
                                # CHUNK 2: NATIVE EXPANDABLE DROPDOWN CONTAINER FOR THIS RUN SPECIFICALLY
                                with st.expander("📋 Activity Performance Summary"):
                                    show_run_lap_breakdown(run, unit_abbr="miles")
                                    render_zone_octagon_display(run)
                                    
                                st.markdown('<div style="margin-bottom:24px; border-bottom:2px solid #2c313c; padding-top:12px;"></div>', unsafe_allow_html=True)
                            
                            elif isinstance(run, str):
                                with st.expander(f"📝 Raw Text Entry Log #{run_idx + 1}"):
                                    st.write(run)
                                st.markdown('<div style="margin-bottom:24px; border-bottom:2px solid #2c313c; padding-top:12px;"></div>', unsafe_allow_html=True)









#############




















        st.markdown("---")
        st.markdown("#### 🦄 Coveted Lifelong Elite Performance Targets")
        history_list = getattr(player, "history_logs", [])
        
        for target_id, target in COVETED_TARGETS.items():
            with st.container(border=True):
                t_col1, t_col2 = st.columns([1, 8.5])
                with t_col1:
                    render_showroom_asset(
                        img_path=target.get("img_path"), 
                        fallback_emoji=target.get("icon", "🦄"), 
                        size_px=65
                    )
                with t_col2:
                    st.markdown(f"### {target['icon']} {target['title']}")
                    st.markdown(f"*{target['desc']}*")
                    
                    is_completed = (
                        any(target["title"].lower() in str(badge).lower() or target.get("icon") in str(badge) for badge in badges_list) or
                        any(target["title"].lower() in str(log).lower() or target.get("icon") in str(log) for log in history_list)
                    )
                    
                    if is_completed:
                        st.success("👑 COVETED TARGET ACHIEVED! Immortalized in your running records.")
                    else:
                        st.info("🎯 Status: Active Career Objective In Progress")

