# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import metrics_config as cfg
import personal_records_config as pr_cfg
import pro_shop_config as shop_cfg
import arena_tournaments_config as arena_cfg
import showroom_engine as eng

# ==============================================================================
# 🎨 PART 1: INTERACTIVE COCKPIT SIDEBAR PANELS & PROGRESS METERS
# ==============================================================================

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
def render_sidebar_requirements_manual(curr_miles, curr_climb, df_instances):
    """Renders an interactive roadmap inside the left sidebar panel with live progression loops."""
    st.sidebar.markdown("### 📘 Showroom Handbook")
    st.sidebar.markdown("Track your remaining targets to unlock your next pieces of hardware.")
    
    st.sidebar.markdown("**🏃‍♂️ Next Mileage Milestones:**")
    unearned_miles = [aw for aw in cfg.WEEKLY_MILEAGE_REWARDS if curr_miles < aw["miles"]]
    next_mile_goals = unearned_miles[:2] if unearned_miles else cfg.WEEKLY_MILEAGE_REWARDS[-1:]
    
    for goal in next_mile_goals:
        progress_pct = min(curr_miles / goal["miles"], 1.0)
        remaining = goal["miles"] - curr_miles
        header = f"🔒 {goal['title']} ({progress_pct:.0%})"
        with st.sidebar.expander(header):
            st.markdown(f"**Target:** {goal['miles']} Miles This Week")
            st.markdown(f"**Current Volume:** {curr_miles:.1f} Miles")
            st.progress(progress_pct)
            st.markdown(f"💡 **You are only {remaining:.1f} miles away** from unlocking this reward!")

    st.sidebar.markdown("<br/>**🏔️ Next Elevation Milestones:**", unsafe_allow_html=True)
    unearned_climb = [aw for aw in cfg.WEEKLY_ELEVATION_REWARDS if curr_climb < aw["climb_ft"]]
    next_climb_goals = unearned_climb[:2] if unearned_climb else cfg.WEEKLY_ELEVATION_REWARDS[-1:]
    
    for goal in next_climb_goals:
        progress_pct = min(curr_climb / goal["climb_ft"], 1.0)
        remaining = goal["climb_ft"] - curr_climb
        header = f"🔒 {goal['title']} ({progress_pct:.0%})"
        with st.sidebar.expander(header):
            st.markdown(f"**Target:** {goal['climb_ft']:,} Vertical Feet")
            st.markdown(f"**Current Ascent:** {curr_climb:,.0f} Feet")
            st.progress(progress_pct)
            st.markdown(f"💡 **You are only {remaining:,.0f} feet away** from unlocking this reward!")
    st.sidebar.markdown("---")
# ==============================================================================
# 🎨 PART 2: SCOREBOARDS, VALUATIONS, BANNER SLOTS & MOTIVATION BOARDS
# ==============================================================================

def render_personal_records_banner(pr_data):
    """Renders layout scoreboard cards dynamically by processing personal_records_config registry definitions."""
    st.markdown("### 🏆 All-Time Personal Records")
    base_css = "border: 1px solid rgba(128,128,128,0.18); border-radius: 6px; padding: 12px; text-align: center; background-color: rgba(255,255,255,0.02);"
    
    registry_len = len(pr_cfg.PERSONAL_RECORDS_REGISTRY)
    if registry_len > 0:
        grid_cols = st.columns(registry_len)
        for idx, record in enumerate(pr_cfg.PERSONAL_RECORDS_REGISTRY):
            rec_id = record["id"]
            metric_info = pr_data.get(rec_id, {"val": record["fallback_value"], "date": record["fallback_date"]})
            
            with grid_cols[idx]:
                st.markdown(f"""
                <div style='{base_css} border-top: 3px solid {record['border_color']};'>
                    <p style='font-size:0.75rem; color:gray; margin:0;'>{record['title']}</p>
                    <h2 style='margin:4px 0; font-size:1.45rem;'>{metric_info['val']}</h2>
                    <p style='font-size:0.7rem; color:gray; margin:0;'>{metric_info['date']}</p>
                </div>
                """, unsafe_allow_html=True)


def render_coveted_master_vault(coveted_statuses):
    """Renders the elite high-prestige lifelong achievement locker room row section."""
    st.markdown("<br/><br/>### 💎 The Coveted Master Rewards Vault", unsafe_allow_html=True)
    cols = st.columns(4)
    
    for idx, (key, award) in enumerate(cfg.COVETED_TARGETS.items()):
        target_col = cols[idx]
        status_data = coveted_statuses.get(key, {"status": "Locked", "progress_label": "0%"})
        
        if status_data["status"] == "Unlocked":
            border_css = "border: 2px solid #f1c40f; background: rgba(241, 196, 15, 0.03);"
            text_color = "#f1c40f"
            tag_label = "🏆 MOUNTED"
        else:
            border_css = "border: 1px dashed rgba(128,128,128,0.3); background: rgba(0,0,0,0.02); opacity: 0.7;"
            text_color = "#7f8c8d"
            tag_label = "LOCKED"

        with target_col:
            st.markdown(f"""
            <div style='border-radius:6px; padding:12px; min-height:190px; text-align:center; {border_css}'>
                <span style='font-size:2.2rem;'>{award['icon']}</span>
                <h5 style='margin:4px 0 2px 0; font-weight:bold;'>{award['title']}</h5>
                <span style='font-size:0.65rem; font-weight:bold; color:white; background:#2c3e50; padding:1px 5px; border-radius:4px;'>{tag_label}</span>
                <p style='font-size:0.7rem; color:gray; line-height:1.2; margin:6px 0 4px 0;'>{award['desc']}</p>
                <p style='font-size:0.75rem; font-weight:bold; color:{text_color}; margin:0;'>{status_data['progress_label']}</p>
            </div>
            """, unsafe_allow_html=True)


def render_top_shelf_showcase(df_instances):
    """Renders the premium 3-slot pinned display row right under the billboard summary."""
    st.markdown("##### 📌 Pinned Top Shelf Favorites")
    pinned_codes = st.session_state.get("showroom_pinned_awards", ["weekly_miles_50", "patch_cold_warrior"])
    
    card_css = "border: 2px dashed rgba(241, 196, 15, 0.4); border-radius: 6px; padding: 10px; text-align: center; background: rgba(241, 196, 15, 0.02);"
    cols = st.columns(3)
    
    for idx, slot_col in enumerate(cols):
        with slot_col:
            if idx < len(pinned_codes):
                code = pinned_codes[idx]
                st.markdown(f"<div style='{card_css}'><h4 style='margin:0;'>🏆</h4><p style='font-size:0.8rem; margin:2px 0; font-weight:bold;'>{code.replace('_',' ').title()}</p><span style='font-size:0.65rem; color:gray;'>Pinned Showcase Slot</span></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='border: 2px dashed rgba(128,128,128,0.2); border-radius: 6px; padding: 10px; text-align: center; color:gray; font-size:0.8rem;'>Empty Showcase Slot</div>", unsafe_allow_html=True)


def render_biometric_arena_row(arena_medals_data):
    """Renders the multiplayer division arena challenge matches dynamically out of the config registry."""
    st.markdown("<br/><br/>### 🏟️ Coliseum Arena Championship Medals", unsafe_allow_html=True)
    cols = st.columns(2)
    
    for idx, (key, challenge) in enumerate(arena_cfg.ARENA_TOURNAMENTS_REGISTRY.items()):
        match_info = arena_medals_data.get(key, {"count": 0, "status_label": "LOCKED MATCH"})
        has_wins = match_info["count"] > 0
        
        border_css = "border: 2px solid #3498db; background: rgba(52, 152, 219, 0.02);" if has_wins else "border: 1px dashed rgba(128,128,128,0.25); background: transparent; opacity:0.65;"
        accent_color = "#3498db" if has_wins else "gray"
        
        with cols[idx]:
            st.markdown(f"""
            <div style='border-radius:6px; padding:14px; min-height:150px; {border_css}'>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <h4 style='margin:0; font-weight:bold; color:{accent_color};'>{challenge['title']}</h4>
                    <span style='font-size:1.8rem;'>{challenge['arena_icon']}</span>
                </div>
                <p style='font-size:0.78rem; margin:6px 0; line-height:1.2; color:#34495e;'>{challenge['desc']}</p>
                <span style='background:#2c3e50; color:white; font-size:0.7rem; font-weight:bold; padding:2px 6px; border-radius:4px;'>{match_info['status_label']}</span>
            </div>
            """, unsafe_allow_html=True)
# ==============================================================================
# 🎨 PART 3: ITEMISED DRILLDOWN LEDGERS & AUDIT DRAWER SUB-SYSTEMS
# ==============================================================================

def render_drilldown_ledger_drawer(df_instances):
    """Outputs itemized verification metrics with columns for distance, pace, and time."""
    code = st.session_state.get("active_showroom_drilldown_code", None)
    title = st.session_state.get("active_showroom_drilldown_title", "Award")
    
    if not code:
        st.markdown("<p style='font-size:0.8rem; color:gray; text-align:center; margin-top:15px;'>ℹ️ Click a card's '🔎 Audit' button to drill down into historical telemetry records.</p>", unsafe_allow_html=True)
        return
        
    st.markdown("---")
    st.markdown(f"#### 🔎 Verification Ledger: {title}")
    st.markdown("Below are the verified sensor logs from `save_file.json` that triggered this milestone:")
    
    filtered = df_instances[df_instances["award_code"] == code].reset_index(drop=True)
    
    st.markdown("| Core Entry Reference | Milestone Earned Date | Status Event | Captured Biometric Telemetry |")
    st.markdown("|:---|:---|:---|:---|")
    for idx, row in filtered.iterrows():
        detail_record = row.get("details", "No extra metadata captured for this event reference loop.")
        st.markdown(f"| Verification Track #{idx+1} | 📅 **{row['date']}** | 🏆 {row['metric']} | 📊 {detail_record} |")
        
    st.write("")
    if st.button("Close Earning Run History Drawer", key="close_drilldown_drawer", use_container_width=True):
        st.session_state.active_showroom_drilldown_code = None
        st.session_state.active_showroom_drilldown_title = "Award"
        st.rerun()
# ==============================================================================
# 🎨 PART 4: ORCHESTRATED SHOWROOM VIEW PORT TERMINALS (PARENT BLOCK)
# ==============================================================================

def generate_dashboard_motivation_alerts():
    """Renders a real-time training motivation board directly at the top of the main Dashboard cockpit page."""
    df_master = st.session_state.get("filtered_df", pd.DataFrame())
    curr_miles, curr_climb = eng.calculate_current_week_metrics(df_master)
    defense_state, days_elapsed = eng.check_streak_defense_status(df_master)
    
    st.markdown("### 🚨 Live Performance Training Briefing")
    
    if defense_state == "decaying":
        st.markdown(f"""<div style='border: 1px solid #c0392b; border-radius: 6px; padding: 14px; background: rgba(192, 57, 43, 0.04); margin-bottom: 12px;'>
            <h5 style='color: #c0392b; margin: 0 0 4px 0;'>⚠️ STREAK EXPIRED</h5>
            <p style='margin: 0; font-size: 0.88rem; line-height:1.3;'>You haven't logged an active workout sequence in <strong>{days_elapsed} days</strong>. Your Streak Master Patches are entering decay state! Run today to maintain defense.</p>
        </div>""", unsafe_allow_html=True)
    
    unearned = [g for g in cfg.WEEKLY_MILEAGE_REWARDS if curr_miles < g["miles"]]
    if unearned:
        next_goal = unearned[0]
        remaining = next_goal["miles"] - curr_miles
        if remaining <= 10.0:
            st.markdown(f"""<div style='border: 1px solid #2ecc71; border-radius: 6px; padding: 14px; background: rgba(46, 204, 113, 0.03); margin-bottom: 16px;'>
                <h5 style='color: #27ae60; margin: 0 0 4px 0;'>🎯 NEXT UP ON THE PERFORMANCE HORIZON</h5>
                <p style='margin: 0; font-size: 0.88rem; line-height:1.3;'>You are sitting at <strong>{curr_miles:.1f} / {next_goal['miles']} Miles</strong> compiled this week. You are only <strong>{remaining:.1f} miles away</strong> from mounting the <strong>{next_goal['title']}</strong> award in your cabinet case!</p>
            </div>""", unsafe_allow_html=True)




# ==============================================================================
# 🎨 PART 4: ORCHESTRATED SHOWROOM VIEW PORT TERMINALS (PARENT BLOCK)
# ==============================================================================

def render_trophy_showroom_tab(df_instances=None, defense_state="stable"):
    """
    Combines the dynamic filtration cockpit with advanced award matrix grids.
    100% data-driven from save_file telemetry with zero hardcoded profile defaults.
    """
    st.markdown("## 🏛️ Hall of Records & Hardware Showroom")
    st.markdown("---")

    if df_instances is None or (isinstance(df_instances, pd.DataFrame) and df_instances.empty):
        df_instances = st.session_state.get("filtered_df", pd.DataFrame())

    if df_instances is None or "award_code" not in df_instances.columns:
        df_instances = pd.DataFrame(columns=["award_code", "date", "metric", "type", "details"])

    df_master = st.session_state.get("filtered_df", pd.DataFrame())
    curr_miles, curr_climb = eng.calculate_current_week_metrics(df_master)
    defense_status, days_elapsed = eng.check_streak_defense_status(df_master)
    
    profile_dict = st.session_state.get("profile", {})
    
    p_level = int(profile_dict.get("level"))
    p_xp = int(profile_dict.get("total_xp"))
    p_title = str(profile_dict.get("name"))

    threshold = getattr(cfg, "XP_PER_LEVEL_THRESHOLD", 1000)
    if threshold <= 0:
        threshold = 1000
    p_pct = min(100, max(0, int((p_xp / threshold) * 100)))

    render_rpg_sidebar_header(p_level, p_xp, p_pct, p_title, defense_status, days_elapsed)
    render_sidebar_requirements_manual(curr_miles, curr_climb, df_instances)
    
    df_instances = df_instances.copy()
    if "Date" in df_instances.columns and "date" not in df_instances.columns:
        df_instances["date"] = df_instances["Date"]

    import datetime
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
        
    selected_season_year = st.sidebar.selectbox(
        "📅 Select Seasonal Lens Timeline:",
        options=available_years,
        index=len(available_years) - 1
    )
    
    if not df_instances.empty and 'Parsed_Date' in df_instances.columns:
        df_filtered_display = df_instances[df_instances['Parsed_Date'].dt.year == selected_season_year]
    else:
        df_filtered_display = df_instances.copy()

    hardware_filter_choices = ["Trophies", "Medals", "Ribbons", "Patches"]
    selected_hardware_types = st.sidebar.multiselect(
        "🛡️ Filter Showcase Assets:",
        options=hardware_filter_choices,
        default=hardware_filter_choices
    )

    type_conversion_mapping = {"Trophies": "trophy", "Medals": "medal", "Ribbons": "ribbon", "Patches": "patch"}
    active_type_strings = [type_conversion_mapping[lbl] for lbl in selected_hardware_types]

    if not df_filtered_display.empty and "type" in df_filtered_display.columns:
        df_filtered_display = df_filtered_display[df_filtered_display["type"].str.lower().isin(active_type_strings)]

    st.sidebar.markdown("<br/>", unsafe_allow_html=True)
    st.sidebar.info(f"""
    📊 **Active Season Metrics ({selected_season_year}):**
    * Total Hardware Unlocked: `{len(df_filtered_display)}`
    * Condition Profile Vector: `{str(defense_state).upper()}`
    """)
    pr_data = profile_dict.get("personal_records", {})
    render_personal_records_banner(pr_data)
    st.markdown("<br/>", unsafe_allow_html=True)
    
    render_top_shelf_showcase(df_filtered_display)
    st.markdown("<br/>", unsafe_allow_html=True)

    coveted_statuses = profile_dict.get("coveted_rewards_status", {})
    render_coveted_master_vault(coveted_statuses)
    
    arena_medals_data = profile_dict.get("arena_championships", {})
    render_biometric_arena_row(arena_medals_data)
    st.markdown("<br/>", unsafe_allow_html=True)

    SHELF_CONFIGS = {
        "trophy": {"title": "🏆 ELITE TROPHY SHELF", "color": "#f1c40f", "bg": "rgba(241, 196, 15, 0.04)"},
        "medal":  {"title": "🥇 COMPETITIVE MEDAL SHELF", "color": "#3498db", "bg": "rgba(52, 152, 219, 0.04)"},
        "ribbon": {"title": "🎗️ PERFORMANCE RIBBON CASE", "color": "#9b59b6", "bg": "rgba(155, 89, 182, 0.04)"},
        "patch":  {"title": "❄️ SYSTEMIC ENVIRONMENTAL PATCHES", "color": "#2ecc71", "bg": "rgba(46, 204, 113, 0.04)"}
    }

    if df_filtered_display.empty:
        st.info(f"ℹ️ No active awards logged inside the {selected_season_year} seasonal lens with current filters.")
        render_drilldown_ledger_drawer(df_filtered_display)
        return

    unique_awards = df_filtered_display["award_code"].unique()
    shelves_data = {k: [] for k in SHELF_CONFIGS.keys()}
    shelves_data["other"] = []

    for code in unique_awards:
        match_runs = df_filtered_display[df_filtered_display["award_code"] == code]
        if not match_runs.empty and "type" in match_runs.columns:
            # 🎯 FIXED HERE: Executed selection slice index mapping correctly
            award_type = str(match_runs["type"].iloc[0]).lower()
        else:
            award_type = "patch"
        
        if award_type in shelves_data:
            shelves_data[award_type].append(code)
        else:
            shelves_data["other"].append(code)

    for shelf_key, shelf_meta in SHELF_CONFIGS.items():
        if shelf_key not in active_type_strings:
            continue
            
        award_codes_on_shelf = shelves_data[shelf_key]
        if not award_codes_on_shelf:
            continue

        st.markdown(f"""
        <div style='margin-top: 25px; margin-bottom: 12px; padding: 6px 12px; border-radius: 4px; background: {shelf_meta['bg']}; border-left: 5px solid {shelf_meta['color']};'>
            <h4 style='margin: 0; color: #2c3e50; font-size: 1.05rem; letter-spacing: 0.5px;'>{shelf_meta['title']}</h4>
        </div>
        """, unsafe_allow_html=True)

        grid_cols = st.columns(4)
        for idx, code in enumerate(award_codes_on_shelf):
            target_col = grid_cols[idx % 4]
            match_runs = df_filtered_display[df_filtered_display["award_code"] == code]
            # 🎯 FIXED HERE: Executed row index assignment brackets
            award_match = match_runs.iloc[0]
            count = len(match_runs)
            
            clean_title = code.split(f"{shelf_key}_")[-1].replace("_", " ").title()
            metric_str = str(award_match.get('metric', '🛡️'))
            icon_list = metric_str.split()
            display_icon = icon_list[0] if icon_list and len(icon_list) <= 2 else "🛡️"
            
            with target_col:
                st.markdown(f"""
                <div style='border: 1px solid rgba(128,128,128,0.16); border-radius: 6px; padding: 12px; min-height: 185px; background: #ffffff; border-bottom: 3px solid {shelf_meta['color']}; box-shadow: 2px 2px 4px rgba(0,0,0,0.03);'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <span style='font-size: 1.6rem;'>{display_icon}</span>
                        <span style='background:#34495e; color:white; font-size:0.65rem; font-weight:bold; padding:2px 6px; border-radius:8px;'>x{count}</span>
                    </div>
                    <h5 style='margin: 12px 0 4px 0; font-size: 0.92rem; color: #1a252f;'>{clean_title}</h5>
                    <p style='font-size: 0.72rem; color: #7f8c8d; line-height: 1.3; margin: 0 0 10px 0;'>{metric_str}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"🔎 Audit {clean_title}", key=f"shelf_audit_{code}", use_container_width=True):
                    st.session_state.active_showroom_drilldown_code = code
                    st.session_state.active_showroom_drilldown_title = f"{clean_title} ({shelf_key.upper()})"
                    st.rerun()

    if shelves_data["other"]:
        st.markdown("<br/><h5>📦 UNCLASSIFIED LEGACY INVENTORY HANGAR</h5>", unsafe_allow_html=True)
        overflow_cols = st.columns(4)
        for idx, code in enumerate(shelves_data["other"]):
            target_col = overflow_cols[idx % 4]
            # 🎯 FIXED HERE: Executed row index assignment brackets
            award_match = df_filtered_display[df_filtered_display["award_code"] == code].iloc[0]
            with target_col:
                st.info(f"⚙️ **{code}**\n\nMetric: `{award_match.get('metric', 'N/A')}`")

    st.markdown("<br/>", unsafe_allow_html=True)
    render_drilldown_ledger_drawer(df_filtered_display)

