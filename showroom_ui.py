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


def render_trophy_showroom_tab(player=None, *args, **kwargs):
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

