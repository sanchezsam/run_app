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

def render_trophy_showroom_tab(df_instances=None, defense_state="stable", popout_container=None):
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

        selected_season_year = st.selectbox(
            "📅 Select Seasonal Lens Timeline:",
            options=timeline_options,
            index=0
        )
        
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
    with patch_tab:
        st.markdown("### 🛡️ Single-Run Performance Patches")
        st.caption("Earned by triggering specialized athletic criteria configurations during an individual training log session.")
        
        patch_categories = FINAL_METRIC_CONFIG.get("single_run_patches", {})
        badges_list = getattr(player, "unlocked_badges", [])
        history_logs = getattr(player, "history_logs", [])
        
        for cat_id, cat_meta in patch_categories.items():
            st.markdown(f"#### {cat_meta['name']}")
            tiers = cat_meta.get("tiers", [])
            
            # Formulate 3-column rows dynamically to display individual metrics
            for i in range(0, len(tiers), 3):
                row_slice = tiers[i:i+3]
                cols = st.columns(3)
                
                for idx, tier in enumerate(row_slice):
                    with cols[idx]:
                        with st.container(border=True):
                            unlocked_count = 0
                            
                            # Pass A: Scan explicitly tracked item entries inside the standard badges array
                            for b in badges_list:
                                b_str = str(b).lower()
                                if (tier["id"].lower() in b_str or 
                                    tier["name"].lower() in b_str or 
                                    (tier.get("icon") and tier.get("icon") in str(b))):
                                    unlocked_count += 1
                                    
                            # Pass B: Unconditional substring matching over the entire history log ledger lines
                            for log in history_logs:
                                log_str = str(log)
                                # Check for name, config ID, or native emoji icon anywhere in the entry row text
                                if (tier.get("icon") and tier.get("icon") in log_str) or \
                                   (tier["id"].lower() in log_str.lower()) or \
                                   (tier["name"].lower() in log_str.lower()):
                                    unlocked_count += 1
                                        
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
                                    st.markdown(
                                        f"**{tier['name']}** "
                                        f'<span style="color:#2ecc71;font-weight:bold;margin-left:4px;">'
                                        f"x{unlocked_count}</span>", 
                                        unsafe_allow_html=True
                                    )

                                    st.caption(f"{tier['icon']} Verified Clear Profile")
                                    st.markdown(f'<p style="font-size:11px;color:#808495;margin:0;">{tier["desc"]}</p>', unsafe_allow_html=True)
                                else:
                                    st.markdown(f'<span style="opacity:0.4;font-weight:bold;">{tier["name"]}</span>', unsafe_allow_html=True)
                                    st.caption("🔒 Locked Objective")
                                    st.markdown(f'<p style="font-size:11px;color:gray;margin:0;">{tier["desc"]}</p>', unsafe_allow_html=True)

    # =========================================================================
    # 🏆 VIEW PANEL: CUMULATIVE LIFELONG CAREER TROPHY CABINET
    # =========================================================================
    with trophy_tab:
        st.markdown("### 🏆 Cumulative Career Trophy Cabinet")
        st.caption("Long-term milestone containers reflecting accumulated totals logged over your active training career.")
        
        metric_totals = getattr(player, "final_metric_data", {})
        lifetime_miles = float(metric_totals.get("lifetime_odometer_miles", 0.0))
        lifetime_elevation = float(metric_totals.get("lifetime_elevation_gain_ft", 0.0))
        lifetime_calories = float(metric_totals.get("lifetime_calories_burned", 0.0))
        
        cabinet_shelves = FINAL_METRIC_CONFIG.get("trophy_cabinet", {})
        
        for shelf_id, shelf_meta in cabinet_shelves.items():
            st.markdown(f"#### {shelf_meta['name']}")
            
            # Determine contextual unit parameters based on active shelf targets
            if "mileage" in shelf_id:
                current_total = lifetime_miles
                unit_label = "miles"
            elif "elevation" in shelf_id:
                current_total = lifetime_elevation
                unit_label = "ft"
            else:
                current_total = lifetime_calories
                unit_label = "kcal"
                
            st.markdown(f"`Accumulated Lifetime Volume: {current_total:,.1f} {unit_label}`")
            st.write("")
            
            trophies = shelf_meta.get("trophies", [])
            for i in range(0, len(trophies), 4):
                row_slice = trophies[i:i+4]
                cols = st.columns(4)
                
                for idx, trophy in enumerate(row_slice):
                    with cols[idx]:
                        with st.container(border=True):
                            is_earned = current_total >= trophy["threshold"]
                            
                            t_col1, t_col2 = st.columns([1, 2.5])
                            with t_col1:
                                render_showroom_asset(
                                    img_path=trophy.get("img_path"), 
                                    fallback_emoji=trophy.get("icon", "🏆"), 
                                    size_px=60
                                )
                            with t_col2:
                                if is_earned:
                                    st.markdown(f"**{trophy['name']}**")
                                    st.success("✅ Unlocked")
                                else:
                                    st.markdown(f'<span style="opacity:0.4;font-weight:bold;">{trophy["name"]}</span>', unsafe_allow_html=True)
                                    st.caption(f"🔒 Requires {trophy['threshold']:,} {unit_label}")

    # =========================================================================
    # 🎗️ VIEW PANEL: WEEKLY REWARDS & COVETED ELITE PERFORMANCE TARGETS
    # =========================================================================
    with milestone_tab:
        st.markdown("### 🎗️ Weekly Progress Thresholds & Elite Milestones")
        st.caption("Short-term high-volume week blocks and historic elite running achievements.")
        
        split_col_1, split_col_2 = st.columns(2)
        
        with split_col_1:
            st.markdown("#### 📅 Weekly Mileage Ribbons & Buckles")
            with st.expander("Review Mileage Milestone Requirements", expanded=True):
                for reward in WEEKLY_MILEAGE_REWARDS:
                    r_col1, r_col2 = st.columns([1, 5.2])
                    with r_col1:
                        render_showroom_asset(
                            img_path=reward.get("img_path"), 
                            fallback_emoji=reward.get("icon", "🎗️"), 
                            size_px=45
                        )
                    with r_col2:
                        st.markdown(f"**{reward['title']}** (`{reward['miles']} miles`)")
                        st.markdown(f'<p style="font-size:11px;color:#808495;margin:0;">{reward["desc"]}</p>', unsafe_allow_html=True)
                        st.markdown('<div style="margin-bottom:8px;border-bottom:1px solid #1f232a;opacity:0.15;"></div>', unsafe_allow_html=True)

        with split_col_2:
            st.markdown("#### 🏔️ Weekly Elevation Climb Milestones")
            with st.expander("Review Vertical Milestone Requirements", expanded=True):
                for reward in WEEKLY_ELEVATION_REWARDS:
                    r_col1, r_col2 = st.columns([1, 5.2])
                    with r_col1:
                        render_showroom_asset(
                            img_path=reward.get("img_path"), 
                            fallback_emoji=reward.get("icon", "🔰"), 
                            size_px=45
                        )
                    with r_col2:
                        st.markdown(f"**{reward['title']}** (`{reward['climb_ft']:,} ft`)")
                        st.markdown(f'<p style="font-size:11px;color:#808495;margin:0;">{reward["desc"]}</p>', unsafe_allow_html=True)
                        st.markdown('<div style="margin-bottom:8px;border-bottom:1px solid #1f232a;opacity:0.15;"></div>', unsafe_allow_html=True)

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

