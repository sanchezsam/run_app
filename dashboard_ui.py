import streamlit as st
import pandas as pd
import json
import os
import calendar
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
import io
from metrics_config import FINAL_METRIC_CONFIG
from upload_ui import get_hr_zone_style









# Optional ReportLab integration for PDF generation
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# ==========================================
# COLOR PALETTE CONFIGURATION (CUSTOMIZABLE)
# ==========================================
THEME_CONFIG = {
    "CALENDAR_BG": "#1e222b",       # Base canvas bounding card background
    "WEEKDAY_HEADER": "#ffffff",    # Day labels (Mon, Tue, etc.) text color
    "REST_EVEN_BG": "#ffcc00",      # Bright yellow for even rest days
    "REST_EVEN_TEXT": "#000000",    # Black text color for legibility on yellow
    "REST_ODD_BG": "#e6b800",       # Slightly darker yellow for alternating odd rest days
    "REST_ODD_TEXT": "#000000",     # Black text color for legibility on yellow
    "RUN_EVEN_BG": "#1a3d38",       # Active workout cell background (even days)
    "RUN_ODD_BG": "#112b27",        # Active workout cell background (odd days)
    "RUN_DAY_TEXT": "#00ffff",      # Active workout primary text color
    "RUN_DAY_BORDER": "#00ffff",    # High-contrast neon border accent
    "NONAGON_LINE": "#00ffcc",      # Progression nonagon outer profile line
    "NONAGON_FILL": "#00ffcc",      # Progression nonagon translucent fill region
    "REST_DAY_BORDER": "#3e4452"    # Subtle structural border for rest cells
}

# ==========================================
# UPGRADE 1: PERFORMANCE MEMORY CACHING
# ==========================================
#@st.cache_data(ttl=600)



def get_monthly_totals(df: pd.DataFrame, target_year: int, target_month_name: str) -> dict:
    """
    Calculates aggregated monthly running totals from historical log metrics.
    
    Parameters:
    df (pd.DataFrame): The source activities DataFrame containing 'Date', 
                      'Display_Distance', 'Duration', and elevation columns.
    target_year (int): The selected year (e.g., 2026).
    target_month_name (str): The name of the month (e.g., "January", "February") 
                             or "All Months" to evaluate the full calendar year.
                             
    Returns:
    dict: A summary containing total distance, formatted total duration, and total ascent.
    """
    import calendar
    
    # 1. Standardize date features and isolate target calendar window
    temp_df = df.copy()
    temp_df['Date'] = pd.to_datetime(temp_df['Date'], errors='coerce')
    temp_df['Year_Int'] = temp_df['Date'].dt.year
    temp_df['Month_Int'] = temp_df['Date'].dt.month
    
    # Apply primary calendar year filter
    filtered = temp_df[temp_df['Year_Int'] == int(target_year)]
    
    # Apply secondary month slice if a specific month is targeted
    month_names = list(calendar.month_name)[1:]
    if target_month_name in month_names:
        month_idx = month_names.index(target_month_name) + 1
        filtered = filtered[filtered['Month_Int'] == month_idx]
        
    if filtered.empty:
        return {"distance": 0.0, "duration": "00:00:00", "elevation": 0.0}
        
    # 2. Compute Cumulative Distance Odometer Total
    filtered['Display_Distance'] = pd.to_numeric(filtered['Display_Distance'], errors='coerce').fillna(0.0)
    total_distance = filtered['Display_Distance'].sum()
    
    # 3. Compute Cumulative Vertical Elevation Ascent Total
    total_elevation = 0.0
    elev_cols = [col for col in filtered.columns if 'elev' in col.lower()]
    if elev_cols and not filtered.empty:
        # Strip string artifacts like commas or unit abbreviations from data cells safely
        cleaned_elev = filtered[elev_cols[0]].astype(str).str.replace(r'[^\d.]', '', regex=True)
        total_elevation = pd.to_numeric(cleaned_elev, errors='coerce').fillna(0.0).sum()
        
    # 4. Compute Cumulative Time Duration Total
    total_seconds = 0
    for dur in filtered.get('Duration', []):
        if pd.notna(dur) and isinstance(dur, str) and ':' in dur:
            parts = dur.split(':')
            try:
                if len(parts) == 3:
                    total_seconds += int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                elif len(parts) == 2:
                    total_seconds += int(parts[0]) * 60 + int(parts[1])
            except ValueError:
                pass
                
    # Build clean HH:MM:SS string presentation structure
    tot_hours = total_seconds // 3600
    tot_mins = (total_seconds % 3600) // 60
    tot_secs = total_seconds % 60
    
    if tot_hours > 0:
        duration_str = f"{tot_hours:02d}:{tot_mins:02d}:{tot_secs:02d}"
    else:
        duration_str = f"{tot_mins:02d}:{tot_secs:02d}"
        
    return {
        "distance": round(total_distance, 2),
        "duration": duration_str,
        "elevation": round(total_elevation, 0)
    }




def ensure_metrics_schema_is_initialized():
    """
    Surgically checks your player profile file at startup to verify that your 
    high-performance tracking containers exist. If missing, injects them seamlessly.
    """
    # 1. Identify which save file string name your active player configuration uses
    # If your player model saves to save.json or save_file.json, map it here:
    TARGET_DB = "save_file.json" 
    
    if not os.path.exists(TARGET_DB):
        # Base template file initialization if completely empty
        base_struct = {"history_logs": [], "unlocked_badges": []}
        with open(TARGET_DB, "w", encoding="utf-8") as f:
            json.dump(base_struct, f, indent=4)

    with open(TARGET_DB, "r", encoding="utf-8") as f:
        try:
            profile_data = json.load(f)
        except Exception:
            return

    # 2. Check for the final_metric_data dictionary layer
    if "final_metric_data" not in profile_data:
        profile_data["final_metric_data"] = {
            "lifetime_odometer_miles": 0.0,
            "lifetime_calories_burned": 0,
            "current_streak_tracker": {
                "current_week_runs_count": 0,
                "last_tracked_week_start": "",
                "consecutive_4_run_weeks": 0,
                "consecutive_52_run_weeks": 0
            },
            "trophy_cabinet": {
                "shelf_a_mileage": [],
                "shelf_b_elevation": [],
                "shelf_c_calories": [],
                "prestige_loops": {
                    "mileage_loops_count": 0,
                    "elevation_loops_count": 0,
                    "calorie_loops_count": 0
                }
            },
            "all_time_personal_records": {
                "fastest_1_mile_seconds": 99999,
                "fastest_5k_seconds": 99999,
                "fastest_10k_seconds": 99999,
                "longest_single_run_miles": 0.0
            }
        }
        if "unlocked_badges" not in profile_data:
            profile_data["unlocked_badges"] = []
            
        # Write the completed schema back down to your workspace directory
        with open(TARGET_DB, "w", encoding="utf-8") as f:
            json.dump(profile_data, f, indent=4, ensure_ascii=False)

# 🛑 EXECUTE THIS TRIGGER LINE AT THE VERY START OF YOUR DASHBOARD TO LOCK IN THE SCHEMA
ensure_metrics_schema_is_initialized()





def render_final_metric_dashboard(player_data: dict, target_col1, target_col2):
    """
    Renders the final_metric ledger using an advanced row-and-grid architecture.
    Col 1 displays the Telemetry Row-Matrix. Col 2 displays the Trophy Shelf-Grid.
    """
    # 1. Safely extract your metric profile containers
    m_data = player_data.get("final_metric_data", {})
    if not m_data:
        with target_col1:
            st.warning("⚠️ Telemetry ledger uninitialized. Upload a .fit track to activate.")
        return

    cabinet = m_data.get("trophy_cabinet", {})
    prestige = cabinet.get("prestige_loops", {})
    unlocked_badges = player_data.get("unlocked_badges", [])

    # =========================================================================
    # ROW/GRID MATRIX 1: DAILY TELEMETRY PATCHES (COLUMN 1 TARGET)
    # =========================================================================
    with target_col1:
        st.markdown("### 🎽 Telemetry Patch Ledger")
        st.caption("Performance badges earned on individual workouts")
        st.write("")

        # Loop over the 8 pillars, turning each one into a clean, horizontal row
        for p_id, p_config in FINAL_METRIC_CONFIG["single_run_patches"].items():
            
            # Wrap the row inside a styled container block for visual spacing
            with st.container(border=True):
                # Row Header Component
                st.markdown(f"**Pillar: {p_config['name']}**")
                
                # Nested 3-Column Item Grid for Bronze, Silver, and Gold tiers
                item_grid = st.columns(3)
                for idx, tier in enumerate(p_config["tiers"]):
                    with item_grid[idx]:
                        is_badge_unlocked = tier["id"] in unlocked_badges
                        
                        # Render item container box
                        if is_badge_unlocked:
                            # Full-color unlocked state
                            st.markdown(f"<div style='text-align: center;'><h2>{tier['icon']}</h2>"
                                        f"<p style='color:#2ECC71; font-weight:bold; font-size:12px; margin:0;'>{tier['name']}</p>"
                                        f"<p style='color:#7F8C8D; font-size:10px; margin:0;'><i>{tier['desc']}</i></p></div>", 
                                        unsafe_allow_html=True)
                        else:
                            # Dimmed locked state with visual anchor
                            st.markdown(f"<div style='text-align: center; opacity: 0.45;'><h2>🔘</h2>"
                                        f"<p style='color:#7F8C8D; font-size:12px; margin:0;'>{tier['name']}</p>"
                                        f"<p style='color:#95A5A6; font-size:10px; margin:0;'><i>{tier['desc']}</i></p></div>", 
                                        unsafe_allow_html=True)

    # =========================================================================
    # ROW/GRID MATRIX 2: MULTI-SHELF TROPHY CABINET (COLUMN 2 TARGET)
    # =========================================================================
    with target_col2:
        st.markdown("### 🏆 Milestone Trophy Case")
        st.caption("Lifelong cumulative odometers and metabolic energy counters")
        st.write("")

        # ---------------------------------------------------------------------
        # ROW ROW: MILEAGE SHELF TRACKER
        # ---------------------------------------------------------------------
        mile_cfg = FINAL_METRIC_CONFIG["trophy_cabinet"]["shelf_a_mileage"]
        earned_miles = cabinet.get("shelf_a_mileage", [])
        mile_loops = prestige.get("mileage_loops_count", 0)

        with st.container(border=True):
            # Shelf header with raw telemetry data readout metric widget
            st.markdown(f"#### 🗺️ {mile_cfg['name']}")
            st.metric(label="Total Distance Covered", value=f"{m_data.get('lifetime_odometer_miles', 0.0):,} Miles")
            
            # 4-Column Shelf Grid layout for items
            shelf_a_grid = st.columns(4)
            for idx, trophy in enumerate(mile_cfg["trophies"]):
                with shelf_a_grid[idx]:
                    if trophy["id"] in earned_miles:
                        st.markdown(f"<div style='text-align: center;'><h1>{trophy['icon']}</h1><b style='font-size:11px;'>{trophy['name']}</b><br><small style='color:#7F8C8D;'>{trophy['threshold']:,} mi</small></div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='text-align: center; opacity: 0.35;'><h1>🔒</h1><span style='color:#7F8C8D; font-size:11px;'>{trophy['name']}</span><br><small>{trophy['threshold']:,} mi</small></div>", unsafe_allow_html=True)
            
            if mile_loops > 0:
                st.markdown(f"⭐ **Prestige Loop Active**: `+{mile_loops}` Infinite Odometer Expansions completed!")

        st.write("") # Spacing row

        # ---------------------------------------------------------------------
        # ROW ROW: ELEVATION VERT VAULT SHELF
        # ---------------------------------------------------------------------
        elev_cfg = FINAL_METRIC_CONFIG["trophy_cabinet"]["shelf_b_elevation"]
        earned_elev = cabinet.get("shelf_b_elevation", [])
        vert_loops = prestige.get("elevation_loops_count", 0)

        with st.container(border=True):
            st.markdown(f"#### 🏔️ {elev_cfg['name']}")
            st.metric(label="Total Vertical Foot Climb", value=f"{player_data.get('lifetime_elevation_gain', 0.0):,} Vert Feet")
            
            shelf_b_grid = st.columns(4)
            for idx, trophy in enumerate(elev_cfg["trophies"]):
                with shelf_b_grid[idx]:



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
                
                if st.button("🚀 Synchronize Database Pipeline", width="stretch"):
                    rendering_box = st.container()
                    execute_gui_pipeline_import(log_container=rendering_box)
                    st.toast("Sync complete! Profile achievements dynamically updated.", icon="🎖️")
                








                    if trophy["id"] in earned_elev:
                        st.markdown(f"<div style='text-align: center;'><h1>{trophy['icon']}</h1><b style='font-size:11px;'>{trophy['name']}</b><br><small style='color:#7F8C8D;'>{trophy['threshold']:,} ft</small></div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='text-align: center; opacity: 0.35;'><h1>🔒</h1><span style='color:#7F8C8D; font-size:11px;'>{trophy['name']}</span><br><small>{trophy['threshold']:,} ft</small></div>", unsafe_allow_html=True)
            
            if vert_loops > 0:
                st.markdown(f"🏔️ **Prestige Vert Loop Active**: `+{vert_loops}` Alpine Summits cleared!")

        st.write("") # Spacing row

        # ---------------------------------------------------------------------
        # ROW ROW: METABOLIC BURN MENU SHELF
        # ---------------------------------------------------------------------
        cal_cfg = FINAL_METRIC_CONFIG["trophy_cabinet"]["shelf_c_calories"]
        earned_cals = cabinet.get("shelf_c_calories", [])
        cal_loops = prestige.get("calorie_loops_count", 0)

        with st.container(border=True):
            st.markdown(f"#### 🍕 {cal_cfg['name']}")
            st.metric(label="Total Cumulative Energy Burned", value=f"{m_data.get('lifetime_calories_burned', 0):,} Calories")
            
            shelf_c_grid = st.columns(4)
            for idx, trophy in enumerate(cal_cfg["trophies"]):
                with shelf_c_grid[idx]:
                    if trophy["id"] in earned_cals:
                        st.markdown(f"<div style='text-align: center;'><h1>{trophy['icon']}</h1><b style='font-size:11px;'>{trophy['name']}</b><br><small style='color:#7F8C8D;'>{trophy['threshold']:,} kcal</small></div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='text-align: center; opacity: 0.35;'><h1>🔒</h1><span style='color:#7F8C8D; font-size:11px;'>{trophy['name']}</span><br><small>{trophy['threshold']:,} kcal</small></div>", unsafe_allow_html=True)
            
            if cal_loops > 0:
                st.markdown(f"👨‍🍳 **Infinite Feast Loop Active**: Conquered `+{cal_loops}` additional major banquet tables!")





def load_data_from_save_json():
    """
    Reads save_file.json and caches the resulting raw activity list in memory.
    Prevents repetitive disk reads on widget change cycles.
    """
    possible_paths = ['save_file.json', '../save_file.json', 'data/save_file.json']
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        if "history_logs" in data:
                            return data["history_logs"]
                        for root_key in data.values():
                            if isinstance(root_key, dict) and "history_logs" in root_key:
                                return root_key["history_logs"]
                    elif isinstance(data, list):
                        return data
            except Exception as e:
                pass
    return []

# ==========================================
# DATA PARSING & UTILITY FORMULAS
# ==========================================
def pace_str_to_minutes(pace_str):
    """Converts a pace string like '10:36' or a float number into total decimal minutes."""
    if pd.isna(pace_str) or pace_str == "":
        return 0.0
    if isinstance(pace_str, (int, float)):
        return float(pace_str)
    try:
        parts = str(pace_str).strip().split(':')
        if len(parts) == 2:
            return int(parts[0]) + (int(parts[1]) / 60.0)
        return float(pace_str)
    except (ValueError, IndexError):
        return 0.0

def minutes_to_pace_str(decimal_minutes):
    """Converts decimal minutes back to a readable string format like '08:45'."""
    if pd.isna(decimal_minutes) or decimal_minutes <= 0:
        return "—"
    minutes = int(decimal_minutes)
    seconds = int(round((decimal_minutes - minutes) * 60))
    if seconds == 60:
        minutes += 1
        seconds = 0
    return f"{minutes:02d}:{seconds:02d}"

# ==========================================
# UPGRADE 2: ADVANCED ANALYTICS CALCULATIONS
# ==========================================
def calculate_grade_adjusted_pace(flat_pace_minutes, elevation_gain_feet, distance_miles):
    """
    Calculates an estimated Grade-Adjusted Pace (GAP) using climbing metrics.
    Adds a proportional penalty rule of roughly 15 seconds per 100 feet climbed per mile.
    """
    if distance_miles <= 0 or flat_pace_minutes <= 0:
        return flat_pace_minutes
    climb_per_mile = elevation_gain_feet / distance_miles
    penalty_minutes = (climb_per_mile / 100.0) * (15.0 / 60.0)
    return flat_pace_minutes + penalty_minutes

def analyze_weekly_mileage_spikes(df, current_year):
    """
    Audits the current calendar year dataset to check for week-over-week training increases.
    Flags sequences that exceed the athletic 10% volume safety guideline.
    """
    year_df = df[df['Date'].dt.year == int(current_year)].copy()
    if year_df.empty:
        return []
    
    # Group logs by sequential ISO week indexes
    year_df['ISO_Week'] = year_df['Date'].dt.isocalendar().week
    weekly_summary = year_df.groupby('ISO_Week')['Display_Distance'].sum().reset_index()
    weekly_summary = weekly_summary.sort_values('ISO_Week').reset_index(drop=True)
    
    warnings = []
    for i in range(1, len(weekly_summary)):
        prev_w = weekly_summary.loc[i-1, 'Display_Distance']
        curr_w = weekly_summary.loc[i, 'Display_Distance']
        week_num = weekly_summary.loc[i, 'ISO_Week']
        
        if prev_w > 5.0:  # Ignore baseline fluctuations
            increase_pct = ((curr_w - prev_w) / prev_w) * 100.0
            if increase_pct > 10.0:
                warnings.append({
                    "week": week_num,
                    "prev_val": prev_w,
                    "curr_val": curr_w,
                    "pct": increase_pct
                })
    return warnings

# ==========================================
# PDF DOCUMENT COMPILER
# ==========================================
def generate_pdf_report(target_df, title_text, unit_abbr, total_miles, total_time, total_elev, view_mode="📅 Grid View", cal_month_name="January", cal_year=2026, cal_df=None):
    if not REPORTLAB_AVAILABLE:
        return None

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'], fontSize=18, spaceAfter=4, textColor=colors.HexColor('#1a334d')
    )
    meta_style = ParagraphStyle(
        'DocMeta', parent=styles['Normal'], fontSize=9, spaceAfter=12, textColor=colors.HexColor('#5c6370')
    )
    
    story.append(Paragraph(f"<b>Running Performance Log Report</b>", title_style))
    story.append(Paragraph(f"Scope: {title_text} | Exported on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", meta_style))
    story.append(Spacer(1, 8))
    
    elev_cols = [col for col in target_df.columns if 'elev' in col.lower()]
    month_names = list(calendar.month_name)[1:]

    if view_mode == "📅 Grid View":
        months_to_loop = range(1, 13) if cal_month_name == "All Months" else [month_names.index(cal_month_name) + 1]
        
        for loop_m in months_to_loop:
            m_name = month_names[loop_m - 1]
            story.append(Paragraph(f"<b>📅 {m_name.upper()} {cal_year}</b>", styles['Heading2']))
            story.append(Spacer(1, 4))
            
            if cal_month_name == "All Months":
                loop_m_df = cal_df[(cal_df['Year_Int'] == cal_year) & (cal_df['Month_Int'] == loop_m)] if cal_df is not None else pd.DataFrame()
                m_miles = loop_m_df['Display_Distance'].sum() if not loop_m_df.empty else 0.0
                
                m_elev = 0.0
                if elev_cols and not loop_m_df.empty:
                    cleaned_m_elev = loop_m_df[elev_cols[0]].astype(str).str.replace(r'[^\d.]', '', regex=True)
                    m_elev = pd.to_numeric(cleaned_m_elev, errors='coerce').fillna(0).sum()
                    
                m_seconds = 0
                if not loop_m_df.empty:
                    for dur in loop_m_df.get('Duration', []):
                        if pd.notna(dur) and isinstance(dur, str) and ':' in dur:
                            parts = dur.split(':')
                            try:
                                if len(parts) == 3:
                                    m_seconds += int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                                elif len(parts) == 2:
                                    m_seconds += int(parts[0]) * 60 + int(parts[1])
                            except ValueError:
                                pass
                                
                m_hours = m_seconds // 3600
                m_mins = (m_seconds % 3600) // 60
                m_time_str = f"{m_hours}h {m_mins}m" if m_hours > 0 else f"{m_mins}m"
                
                m_summary_data = [
                    ["Monthly Distance", "Monthly Duration", "Monthly Ascent"],
                    [f"{m_miles:,.2f} {unit_abbr}", m_time_str, f"{m_elev:,.0f} ft"]
                ]
                m_summary_table = Table(m_summary_data, colWidths=[180, 180, 180])
                m_summary_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f4f6f8')),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#000000')),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dcdfe6')),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                story.append(m_summary_table)
                story.append(Spacer(1, 6))
                
            days_headers = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            grid_matrix = [days_headers]
            loop_matrix = calendar.monthcalendar(cal_year, loop_m)
            
            m_table_styles = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c313c')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#3e4452')),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]
            
            cell_p_style_run = ParagraphStyle('CellRun', parent=styles['Normal'], alignment=1, fontSize=8, textColor=colors.HexColor(THEME_CONFIG["RUN_DAY_TEXT"]), fontName='Helvetica-Bold')
            cell_p_style_rest_even = ParagraphStyle('CellRestEven', parent=styles['Normal'], alignment=1, fontSize=8, textColor=colors.HexColor(THEME_CONFIG["REST_EVEN_TEXT"]), fontName='Helvetica-Bold')
            cell_p_style_rest_odd = ParagraphStyle('CellRestOdd', parent=styles['Normal'], alignment=1, fontSize=8, textColor=colors.HexColor(THEME_CONFIG["REST_ODD_TEXT"]), fontName='Helvetica-Bold')
            cell_p_style_empty = ParagraphStyle('CellEmpty', parent=styles['Normal'], alignment=1, fontSize=8)

            for r_idx, week in enumerate(loop_matrix):
                row_cells = []
                for c_idx, day in enumerate(week):
                    if day == 0:
                        row_cells.append(Paragraph("", cell_p_style_empty))
                        m_table_styles.append(('BACKGROUND', (c_idx, r_idx + 1), (c_idx, r_idx + 1), colors.HexColor(THEME_CONFIG["CALENDAR_BG"])))
                    else:
                        target_date_str = f"{cal_year}-{loop_m:02d}-{day:02d}"
                        day_runs = cal_df[cal_df['Formatted_Date'] == target_date_str] if cal_df is not None else pd.DataFrame()
                        parity_suffix = "even" if day % 2 == 0 else "odd"
                        if not day_runs.empty:                        
                            for _, run_row in day_runs.iterrows():
                                run_dist = run_row['Display_Distance']
                                run_time = run_row.get('Duration', '--:--')
                                cell_text = f"<b>{day}</b><br/><br/><b>{run_dist:.1f}{unit_abbr}</b><br/>{run_time}"
                                row_cells.append(Paragraph(cell_text, cell_p_style_run))
                                
                                bg_color = THEME_CONFIG["RUN_EVEN_BG"] if parity_suffix == "even" else THEME_CONFIG["RUN_ODD_BG"]
                                m_table_styles.append(('BACKGROUND', (c_idx, r_idx + 1), (c_idx, r_idx + 1), colors.HexColor(bg_color)))
                        else:
                            cell_text = f"<b>{day}</b><br/><br/>—<br/>—"
                            p_style = cell_p_style_rest_even if parity_suffix == "even" else cell_p_style_rest_odd
                            row_cells.append(Paragraph(cell_text, p_style))
                            
                            bg_color = THEME_CONFIG["REST_EVEN_BG"] if parity_suffix == "even" else THEME_CONFIG["REST_ODD_BG"]
                            m_table_styles.append(('BACKGROUND', (c_idx, r_idx + 1), (c_idx, r_idx + 1), colors.HexColor(bg_color)))
                grid_matrix.append(row_cells)
                
            month_table = Table(grid_matrix, colWidths=[77]*7)
            month_table.setStyle(TableStyle(m_table_styles))
            story.append(month_table)
            story.append(Spacer(1, 14))
    else:
        headers = ['Date', 'Activity Type', 'Distance', 'Duration', 'Pace']
        if elev_cols:
            headers.append('Ascent')
            
        table_matrix = [headers]
        table_styles = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c313c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e4e7ed')),
            ('FONTSIZE', (0, 1), (-1, -1), 8.5),
        ]
        
        months_in_report = sorted(target_df['Month_Int'].unique()) if not target_df.empty else []
        
        for m_idx in months_in_report:
            m_matrix = calendar.monthcalendar(cal_year, m_idx)
            m_name = month_names[m_idx - 1]
            
            header_row = [f"📅 {m_name.upper()} LOGS", "", "", "", ""]
            if elev_cols:
                header_row.append("")
            table_matrix.append(header_row)
            r_idx = len(table_matrix) - 1
            table_styles.extend([
                ('SPAN', (0, r_idx), (-1, r_idx)),
                ('BACKGROUND', (0, r_idx), (-1, r_idx), colors.HexColor('#1a1c23')),
                ('TEXTCOLOR', (0, r_idx), (-1, r_idx), colors.HexColor('#00ffcc')),
                ('FONTNAME', (0, r_idx), (-1, r_idx), 'Helvetica-Bold'),
            ])
            
            m_dist, m_seconds, m_elev = 0.0, 0, 0.0
            
            for w_idx, week in enumerate(m_matrix):
                week_has_days = False
                week_dist = 0.0
                week_seconds = 0
                week_elev = 0.0
                week_rows = []
                
                for day in week:
                    if day == 0:
                        continue
                    week_has_days = True
                    target_date_str = f"{cal_year}-{m_idx:02d}-{day:02d}"
                    #day_runs = target_df[target_df['Formatted_Date'] == target_date_str]
                    day_runs = target_df[target_df['Formatted_Date'] == target_date_str]
                    
                    # 🪵 TEMPORARY DIAGNOSTIC PRINT
                    
                    if not day_runs.empty:
                        for _, run_row in day_runs.iterrows():
                            run_dist = float(run_row['Display_Distance'])
                            run_time = str(run_row.get('Duration', '--:--'))
                            run_pace = f"{run_row.get('pace', '—')} min/{unit_abbr.lower()}"
                            
                            day_elevation = 0.0
                            if elev_cols:
                                raw_elev_val = run_row.get(elev_cols[0], "0")
                                cleaned_run_elev = ''.join(c for c in str(raw_elev_val) if c.isdigit() or c == '.')
                                if cleaned_run_elev:
                                    day_elevation = float(cleaned_run_elev)
                                    
                            week_dist += run_dist
                            m_dist += run_dist
                            week_elev += day_elevation
                            m_elev += day_elevation
                            
                            if ':' in run_time:
                                parts = run_time.split(':')
                                try:
                                    if len(parts) == 3:
                                        secs = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                                        week_seconds += secs
                                        m_seconds += secs
                                    elif len(parts) == 2:
                                        secs = int(parts[0]) * 60 + int(parts[1])
                                        week_seconds += secs
                                        m_seconds += secs
                                except ValueError:
                                    pass
                                    
                            day_cells = [target_date_str, "RUN", f"{run_dist:.2f} {unit_abbr}", run_time, run_pace]
                            if elev_cols:
                                day_cells.append(f"{day_elevation:,.0f} ft")
                            week_rows.append(day_cells)
                    else:
                        day_cells = [target_date_str, "REST DAY", "—", "—", "—"]
                        if elev_cols:
                            day_cells.append("—")
                        week_rows.append(day_cells)
                        
                if week_has_days:
                    table_matrix.extend(week_rows)
                    
                    w_hours = week_seconds // 3600
                    w_mins = (week_seconds % 3600) // 60
                    w_time_str = f"{w_hours}h {w_mins}m" if w_hours > 0 else f"{w_mins}m"
                    if week_seconds == 0:
                        w_time_str = "—"
                        
                    w_row = [f"WEEK {w_idx + 1} TOTALS", "WEEK SUMMARY", f"{week_dist:.2f} {unit_abbr}", w_time_str, "—"]
                    if elev_cols:
                        w_row.append(f"{week_elev:,.0f} ft")
                    table_matrix.append(w_row)
                    r_idx = len(table_matrix) - 1
                    table_styles.extend([
                        ('BACKGROUND', (0, r_idx), (-1, r_idx), colors.HexColor('#0f3930')),
                        ('TEXTCOLOR', (0, r_idx), (-1, r_idx), colors.HexColor('#00ffcc')),
                        ('FONTNAME', (0, r_idx), (-1, r_idx), 'Helvetica-Bold'),
                    ])
                    
            m_hours = m_seconds // 3600
            m_mins = (m_seconds % 3600) // 60
            m_time_str = f"{m_hours}h {m_mins}m" if m_hours > 0 else f"{m_mins}m"
            if m_seconds == 0:
                m_time_str = "—"
                
            m_row = [f"{m_name.upper()} TOTALS", "MONTH OVERVIEW", f"{m_dist:.2f} {unit_abbr}", m_time_str, "—"]
            if elev_cols:
                m_row.append(f"{m_elev:,.0f} ft")
            table_matrix.append(m_row)
            r_idx = len(table_matrix) - 1
            table_styles.extend([
                ('BACKGROUND', (0, r_idx), (-1, r_idx), colors.HexColor('#1a334d')),
                ('TEXTCOLOR', (0, r_idx), (-1, r_idx), colors.HexColor('#00ffff')),
                ('FONTNAME', (0, r_idx), (-1, r_idx), 'Helvetica-Bold'),
            ])
            
        y_row = [f"🏆 {cal_year} YEAR TOTALS", "GRAND OVERVIEW", f"{total_miles:,.2f} {unit_abbr}", total_time, "—"]
        if elev_cols:
            y_row.append(f"{total_elev:,.0f} ft")
        table_matrix.append(y_row)
        r_idx = len(table_matrix) - 1
        table_styles.extend([
            ('BACKGROUND', (0, r_idx), (-1, r_idx), colors.HexColor('#332300')),
            ('TEXTCOLOR', (0, r_idx), (-1, r_idx), colors.HexColor('#ffcc00')),
            ('FONTNAME', (0, r_idx), (-1, r_idx), 'Helvetica-Bold'),
        ])
        
        col_widths = [85, 80, 85, 85, 95]
        if elev_cols:
            col_widths.append(90)
            
        log_table = Table(table_matrix, colWidths=col_widths, repeatRows=1)
        log_table.setStyle(TableStyle(table_styles))
        story.append(log_table)
        
    doc.build(story)
    buffer.seek(0)
    return buffer

# ==========================================
# UPGRADE 3: CHARTING RADAR NONAGON VISUALS
# ==========================================
import numpy as np
import matplotlib.pyplot as plt

def render_progression_nonagon(endurance_lvl, pace_lvl, hill_lvl):
    """
    REVERTED: Builds a traditional 9-slice polar radar chart representing 
    overlapping progression levels across 3 target training pillars.
    """
    num_slices = 9
    labels = [
        "Endur. L1", "Endur. L2", "Endur. L3",
        "Pace L1", "Pace L2", "Pace L3",
        "Hill L1", "Hill L2", "Hill L3"
    ]
   
    # Calculate the fractional fills across your legacy 3-tier sub-slots
    values = [
        min(endurance_lvl, 1), min(max(endurance_lvl - 1, 0), 1), min(max(endurance_lvl - 2, 0), 1),
        min(pace_lvl, 1),      min(max(pace_lvl - 1, 0), 1),      min(max(pace_lvl - 2, 0), 1),
        min(hill_lvl, 1),      min(max(hill_lvl - 1, 0), 1),      min(max(hill_lvl - 2, 0), 1)
    ]
   
    # Multiply by 3 to scale out to the radial plot geometry boundaries
    display_values = [v * 3 for v in values]
    angles = np.linspace(0, 2 * np.pi, num_slices, endpoint=False).tolist()

    # Close the circular visual line loops path cleanly
    display_values += display_values[:1]
    angles += angles[:1]

    # Initialize standard Matplotlib polar grid panels
    fig, ax = plt.subplots(figsize=(4.5, 4.5), subplot_kw=dict(polar=True))
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    # Set up peripheral axis ticks and sub-tier rings labels
    plt.xticks(angles[:-1], labels, color='#ffffff', size=8)
    ax.set_rlabel_position(0)
    plt.yticks([1, 2, 3], ["L1", "L2", "L3"], color="#7e8794", size=7)
    plt.ylim(0, 3)

    # Draw the boundary contours and alpha area fill layers
    theme_line = THEME_CONFIG["NONAGON_LINE"] if 'THEME_CONFIG' in globals() else "#4ade80"
    theme_fill = THEME_CONFIG["NONAGON_FILL"] if 'THEME_CONFIG' in globals() else "#4ade80"

    ax.plot(angles, display_values, color=theme_line, linewidth=2, linestyle='solid')
    ax.fill(angles, display_values, color=theme_fill, alpha=0.3)

    # Apply Cabinet Color Palette Background Styling Panel
    fig.patch.set_facecolor('#1e222b')
    ax.set_facecolor('#1e222b')
    ax.spines['polar'].set_color('#3e4452')
    ax.grid(color='#3e4452', linestyle='--')

    return fig







# ==========================================
# MAIN INTERACTIVE UI DASHBOARD ELEMENT
# ==========================================
def render_dashboard_overview(player):
    # Establish persistent application tab memory mapping
    if "current_dashboard_tab" not in st.session_state:
        st.session_state.current_dashboard_tab = "📅 Training Data Perspectives"
        
    if "selected_activity_date" not in st.session_state:
        st.session_state.selected_activity_date = None

    st.header("🏃‍♂️ Activity Dashboard Overview")
    
    raw_activities = []
    if hasattr(player, 'history_logs') and player.history_logs:
        raw_activities = player.history_logs
    if not raw_activities:
        raw_activities = load_data_from_save_json()

    if isinstance(raw_activities, str):
        try:
            raw_activities = json.loads(raw_activities)
        except Exception:
            raw_activities = []

    if isinstance(raw_activities, list):
        raw_activities = [row for row in raw_activities if isinstance(row, dict)]
    else:
        raw_activities = []

    if not raw_activities:
        st.info("👋 Welcome! No fitness tracking history found in your save file.")
        st.markdown("Please head over to the **Upload UI** page to import your Garmin data files.")
        return

    df = pd.DataFrame(raw_activities)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    
    # 🟢 INJECT THIS SANITIZATION SHIELD:
    if 'Type' in df.columns:
        df = df[df['Type'] != "Coliseum_Arena_Match"]
    if 'type' in df.columns:
        df = df[df['type'] != "Coliseum_Arena_Match"]




    df['Distance (Miles)'] = pd.to_numeric(df['Distance (Miles)'], errors='coerce').fillna(0)
    df = df.dropna(subset=['Date']).sort_values('Date')
    
    df['Year'] = df['Date'].dt.year.astype(str)
    df['Month_Period'] = df['Date'].dt.to_period('M')  
    df['Month_Label'] = df['Date'].dt.strftime('%b %Y')  
    df['Formatted_Date'] = df['Date'].dt.strftime('%Y-%m-%d')

    st.subheader("🎛️ Unit & Filter Configuration")
    config_col1, config_col2 = st.columns(2)
    
    #with config_col2:
    #    unit_system = st.selectbox(
    #        label="🔄 Select System Unit:",
    #        options=["Miles (mi)", "Kilometers (km)"],
    #        index=0
    #    )
    #
    is_km = False
    unit_abbr = "Mi"
    df['Display_Distance'] = df['Distance (Miles)'] * 1.0

    with config_col1:
        unique_years = sorted(df['Year'].unique(), reverse=True)
        selected_year = st.radio(
            label="Select Tracking Year to Filter Below Trends:",
            options=["All Years"] + unique_years,
            index=0,
            horizontal=True
        )

    if selected_year != "All Years":
        filtered_df = df[df['Year'] == selected_year].reset_index(drop=True)
    else:
        filtered_df = df.reset_index(drop=True)

    st.write("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("🏃 Daily Activity")
        total_daily_records = len(filtered_df)
        if total_daily_records > 0:
            daily_range = st.slider(
                label="Select Day Index Window Range:",
                min_value=0,
                max_value=total_daily_records - 1,
                value=(max(0, total_daily_records - 15), total_daily_records - 1),
                step=1,
                key="daily_range_slider"
            )
            start_daily, end_daily = daily_range
            daily_plot_df = filtered_df.iloc[start_daily : end_daily + 1]
            st.bar_chart(data=daily_plot_df, x='Formatted_Date', y='Display_Distance', width="stretch")
            st.metric(f"Daily Segment Total ({unit_abbr})", f"{daily_plot_df['Display_Distance'].sum():,.2f} {unit_abbr}")
        else:
            st.caption("No data for current filters.")

    with col2:
        st.subheader("📅 Monthly Trends")
        if not filtered_df.empty:
            monthly_df = filtered_df.groupby(['Month_Period', 'Month_Label'])['Display_Distance'].sum().reset_index()
            monthly_df = monthly_df.sort_values('Month_Period').reset_index(drop=True)
            total_months = len(monthly_df)
            
            month_range = st.slider(
                label="Select Month Window Range:",
                min_value=0,
                max_value=total_months - 1,
                value=(0, total_months - 1),
                step=1,
                key="month_range_slider"
            )
            start_month, end_month = month_range
            monthly_plot_df = monthly_df.iloc[start_month : end_month + 1]
            st.bar_chart(data=monthly_plot_df, x='Month_Label', y='Display_Distance', width="stretch")
            st.metric(f"Monthly Segment Total ({unit_abbr})", f"{monthly_plot_df['Display_Distance'].sum():,.2f} {unit_abbr}")
        else:
            st.caption("No data for current filters.")

    with col3:
        st.subheader("📈 Annual Totals")
        yearly_df = df.groupby('Year')['Display_Distance'].sum().reset_index().sort_values('Year').reset_index(drop=True)
        total_years = len(yearly_df)
        if total_years > 0:
            year_range = st.slider(
                label="Select Year Window Range:",
                min_value=0,
                max_value=total_years - 1,
                value=(0, total_years - 1),
                step=1,
                key="year_range_slider"
            )
            start_year, end_year = year_range
            yearly_plot_df = yearly_df.iloc[start_year : end_year + 1]
            st.bar_chart(data=yearly_plot_df, x='Year', y='Display_Distance', width="stretch")
            st.metric(f"All-Time History Total ({unit_abbr})", f"{yearly_plot_df['Display_Distance'].sum():,.2f} {unit_abbr}")
        else:
            st.caption("No dynamic historical year structures found.")

    # Force component retention through click execution loops
    if "current_dashboard_tab" not in st.session_state:
        st.session_state.current_dashboard_tab = "📅 Training Data Perspectives"
    # Force component view retention through click execution loops
    if st.session_state.get('current_dashboard_tab') == "📅 Training Data Perspectives":
        show_cal(player=None, external_df=df, unit_abbr=unit_abbr)
    else:
        show_cal(player=None, external_df=df, unit_abbr=unit_abbr)

def show_cal(player=None, external_df=None, unit_abbr="Mi"):
    # Intercept session dictionary allocations to prevent page-snapping loops
    for state_key in ["sidebar_nav", "main_menu", "app_tabs", "navigation_options", "page_selection"]:
        if state_key in st.session_state:
            st.session_state[state_key] = "📅 Training Data Perspectives" 
            
    # 🛰️ NEW: Intercept URL query parameters on reload to preserve user navigation context
    if "select_date" in st.query_params:
        st.session_state.selected_activity_date = st.query_params["select_date"]
    if "view" in st.query_params and st.query_params["view"] == "spreadsheet":
        st.session_state.calendar_display_view = "📊 Spreadsheet View"

    if "selected_activity_date" not in st.session_state:
        st.session_state.selected_activity_date = None


    if external_df is not None:
        df = external_df
    else:
        raw_activities = load_data_from_save_json()
        if isinstance(raw_activities, str):
            try: raw_activities = json.loads(raw_activities)
            except Exception: raw_activities = []
        raw_activities = [row for row in raw_activities if isinstance(row, dict)] if raw_activities else []
        if not raw_activities: return
        df = pd.DataFrame(raw_activities)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Distance (Miles)'] = pd.to_numeric(df['Distance (Miles)'], errors='coerce').fillna(0)
        df = df.dropna(subset=['Date']).sort_values('Date')
        df['Formatted_Date'] = df['Date'].dt.strftime('%Y-%m-%d')
        df['Display_Distance'] = df['Distance (Miles)']

    # 🟢 INJECT FILTER SHIELD HERE (Handles both local or external dataframes safely):
    if 'Type' in df.columns:
        df = df[df['Type'] != "Coliseum_Arena_Match"]
    if 'type' in df.columns:
        df = df[df['type'] != "Coliseum_Arena_Match"]

    elev_cols = [col for col in df.columns if 'elev' in col.lower()]

    st.write("---")
    st.subheader("📅 Training Data Perspectives")

    cal_df = df.copy()
    cal_df['Year_Int'] = cal_df['Date'].dt.year
    cal_df['Month_Int'] = cal_df['Date'].dt.month
    years_available = sorted(cal_df['Year_Int'].unique(), reverse=True)
    month_names = list(calendar.month_name)[1:]

    active_year_default = years_available[0] if years_available else datetime.now().year
    raw_month_max = cal_df[cal_df['Year_Int'] == active_year_default]['Month_Int'].max()
    active_month_default_idx = int(raw_month_max) - 1 if pd.notna(raw_month_max) else 0

    if st.session_state.selected_activity_date:
        try:
            parsed_dt = datetime.strptime(st.session_state.selected_activity_date, '%Y-%m-%d')
            if parsed_dt.year in years_available:
                active_year_default = parsed_dt.year
                active_month_default_idx = parsed_dt.month - 1
        except Exception: pass

    if "grid_year_dropdown" not in st.session_state:
        st.session_state.grid_year_dropdown = active_year_default
    if "grid_month_dropdown" not in st.session_state:
        st.session_state.grid_month_dropdown = month_names[max(0, min(active_month_default_idx, 11))]
    if "calendar_display_view" not in st.session_state:
        st.session_state.calendar_display_view = "📅 Grid View"

    #st.radio(label="Layout Perspective Selector Switch:", options=["📅 Grid View", "📊 Spreadsheet View", "📆 Full Year View"], key="calendar_display_view", horizontal=True)
    st.radio(label="Layout Perspective Selector Switch:", options=["📅 Grid View", "📊 Spreadsheet View"], key="calendar_display_view", horizontal=True)
    st.write("")

    sel_col1, sel_col2 = st.columns(2)
    with sel_col1:
        if st.session_state.grid_year_dropdown not in years_available:
            st.session_state.grid_year_dropdown = years_available[0] if years_available else active_year_default
        # Dynamic index calculation logic
        year_idx = years_available.index(st.session_state.grid_year_dropdown) if st.session_state.grid_year_dropdown in years_available else 0
        cal_year = st.selectbox("Select Display Year:", years_available, index=year_idx)
        
    with sel_col2:
        is_year_view = st.session_state.calendar_display_view == "📆 Full Year View"
        month_options = ["All Months"] + month_names
        if st.session_state.grid_month_dropdown not in month_options:
            st.session_state.grid_month_dropdown = month_options[1]
        # Dynamic index calculation logic
        month_idx = month_options.index(st.session_state.grid_month_dropdown) if st.session_state.grid_month_dropdown in month_options else 1
        cal_month_name = st.selectbox(label="Select Display Month:", options=month_options, index=month_idx, disabled=is_year_view)







    cal_month = 1 if cal_month_name == "All Months" else month_names.index(cal_month_name) + 1

    if is_year_view or cal_month_name == "All Months":
        prev_year, prev_month_idx = cal_year - 1, 0
        next_year, next_month_idx = cal_year + 1, 0
    else:
        prev_month, prev_year = (12, cal_year - 1) if cal_month == 1 else (cal_month - 1, cal_year)
        next_month, next_year = (1, cal_year + 1) if cal_month == 12 else (cal_month + 1, cal_year)
        prev_month_idx, next_month_idx = prev_month - 1, next_month - 1

    min_date, max_date = cal_df['Date'].min(), cal_df['Date'].max()

    if is_year_view or cal_month_name == "All Months":
        has_prev = (prev_year >= min_date.year) if pd.notna(min_date) else False
        has_next = (next_year <= max_date.year) if pd.notna(max_date) else False
    else:
        # Standard parent level alignment (8 spaces from the margin)
        has_prev = (prev_year > min_date.year) or (prev_year == min_date.year and prev_month >= min_date.month) if pd.notna(min_date) else False
        has_next = (next_year < max_date.year) or (next_year == max_date.year and next_month <= max_date.month) if pd.notna(max_date) else False

    # REALIGNED TO 4 SPACES: Keep the function definition aligned with your column blocks
    def handle_navigation_callback(target_year, target_month_name):
        st.session_state.grid_year_dropdown = target_year
        st.session_state.grid_month_dropdown = target_month_name
        st.session_state.selected_activity_date = None
        
        # 1. Enforce global page persistence variables across ALL common app tabs monikers
        # This stops app.py from resetting your tab selection on a rerun cycle
        for state_key in [
            'sidebar_nav', 'main_menu', 'app_tabs', 'navigation_options', 
            'page_selection', 'current_tab', 'view_selection', 'menu_selection'
        ]:
            st.session_state[state_key] = '📅 Training Data Perspectives'
            
        # 2. Synchronize full year parameters 
        if "calendar_display_view" not in st.session_state:
            st.session_state.calendar_display_view = "📆 Full Year View"
            
        # 3. Fire off the synchronized interface refresh
        st.rerun() 
    # Standard child block layout alignment (4 spaces from the margin)
    main_layout_col1, main_layout_col2 = st.columns([1.3, 0.7])
    with main_layout_col1:
        st.markdown(
            f"""
            <style>
            div[data-testid="stColumn"]:has(.calendar-bg-trigger) {{
                background-color: {THEME_CONFIG["CALENDAR_BG"]} !important;
                border: 3px solid {THEME_CONFIG["RUN_DAY_BORDER"]} !important;
                padding: 24px !important;
                border-radius: 12px !important;
                box-shadow: 0 0 15px rgba(0, 255, 204, 0.2) !important;
                margin-bottom: 20px !important;
            }}
            .original-day-header {{
                color: {THEME_CONFIG["WEEKDAY_HEADER"]} !important;
                font-weight: bold !important;
                font-size: 14px !important;
                text-align: center !important;
                padding: 10px 0;
                text-transform: uppercase;
                letter-spacing: 1px;
                display: block !important;
                border-bottom: 2px solid #3e4452;
                margin-bottom: 12px;
            }}
            .cal-btn-placeholder {{
                min-width: 75px !important;
                width: 100% !important;
                min-height: 105px !important;
                height: 105px !important;
                display: block !important;
                background-color: transparent !important;
            }}
            div[data-testid="stRadio"] label p, div[data-testid="stRadio"] p {{
                color: #000000 !important;
                font-weight: bold !important;
            }}


            div[data-testid="stVerticalBlock"]:has(.rest-even-marker, .rest-odd-marker, .run-even-marker, .run-odd-marker) div[data-testid="stButton"] button {{
                min-width: 75px !important;
                width: 100% !important;
                min-height: 105px !important;
                height: auto !important;
                padding: 8px 4px !important;
                font-size: 10.5px !important;
                border-radius: 8px !important;
                display: flex !important;
                flex-direction: column !important;
                justify-content: center !important;
                align-items: center !important;
                text-align: center !important;
                white-space: pre-wrap !important;
                word-wrap: break-word !important;
                line-height: 1.15 !important;
                overflow: visible !important;
            }}
            div[data-testid="stVerticalBlock"]:has(.rest-even-marker) div[data-testid="stButton"] button {{
                background-color: {THEME_CONFIG["REST_EVEN_BG"]} !important;
                color: {THEME_CONFIG["REST_EVEN_TEXT"]} !important;
                border: 1px solid {THEME_CONFIG["REST_DAY_BORDER"]} !important;
                font-weight: bold !important;
            }}
            div[data-testid="stVerticalBlock"]:has(.rest-odd-marker) div[data-testid="stButton"] button {{
                background-color: {THEME_CONFIG["REST_ODD_BG"]} !important;
                color: {THEME_CONFIG["REST_ODD_TEXT"]} !important;
                border: 1px solid {THEME_CONFIG["REST_DAY_BORDER"]} !important;
                font-weight: bold !important;
            }}

            /* ✅ THE NEW LAYOUT INTERNALS OVERRIDE SITS PERFECTLY HERE: */
            div[data-testid="stVerticalBlock"]:has(.run-even-marker, .run-odd-marker) {{
                height: auto !important;
                overflow: visible !important;
                display: flex !important;
                flex-direction: column !important;
                gap: 6px !important;
            }}

            div[data-testid="stVerticalBlock"]:has(.run-even-marker) div[data-testid="stButton"] button {{
                background-color: {THEME_CONFIG["RUN_EVEN_BG"]} !important;
                color: {THEME_CONFIG["RUN_DAY_TEXT"]} !important;
                border: 2px solid {THEME_CONFIG["RUN_DAY_BORDER"]} !important;
                font-weight: bold !important;
            }}
            div[data-testid="stVerticalBlock"]:has(.run-odd-marker) div[data-testid="stButton"] button {{
                background-color: {THEME_CONFIG["RUN_ODD_BG"]} !important;
                color: {THEME_CONFIG["RUN_DAY_TEXT"]} !important;
                border: 2px solid {THEME_CONFIG["RUN_DAY_BORDER"]} !important;
                font-weight: bold !important;
            }}
            .spreadsheet-table {{
                width: 100%; border-collapse: collapse; color: #ffffff; margin-top: 10px; font-size: 11.5px; font-family: monospace;
            }}
            .spreadsheet-table th {{
                background-color: #2c313c !important; color: #00ffcc !important; text-align: left; padding: 10px; font-weight: bold; text-transform: uppercase; border-bottom: 2px solid #3e4452;
            }}

            .spreadsheet-table td {{ padding: 8px 10px; border-bottom: 1px solid #232731; vertical-align: middle; }}
            .spreadsheet-table tr.day-row:nth-child(even) {{ background-color: #1e222b !important; }}
            .spreadsheet-table tr.day-row:nth-child(odd) {{ background-color: #242935 !important; }}
            .spreadsheet-table tr.weekly-total-row {{
                background-color: #0f3930 !important; color: #00ffcc !important; font-weight: bold !important; border-top: 2px solid #00ffcc !important; border-bottom: 2px solid #00ffcc !important;
            }}
            .spreadsheet-table tr.monthly-total-row {{
                background-color: #1a334d !important; color: #00ffff !important; font-weight: bold !important; border-top: 2px solid #00ffff !important; border-bottom: 2px solid #00ffff !important;
            }}
            .spreadsheet-table tr.yearly-total-row {{
                background-color: #332300 !important; color: #ffcc00 !important; font-weight: bold !important; border-top: 3px solid #ffcc00 !important; border-bottom: 3px solid #ffcc00 !important;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
        
        with st.container():
            st.markdown("<div class='calendar-bg-trigger'></div>", unsafe_allow_html=True)
            
            if is_year_view or cal_month_name == "All Months":
                target_df = cal_df[cal_df['Year_Int'] == cal_year]
                current_header_title = f"Full Year Timeline: {cal_year}"
            else:
                target_df = cal_df[(cal_df['Year_Int'] == cal_year) & (cal_df['Month_Int'] == cal_month)]
                current_header_title = f"{month_names[cal_month - 1]} {cal_year}"
                
            total_miles_aggregated = target_df['Display_Distance'].sum()
            elev_columns = [col for col in target_df.columns if 'elev' in col.lower()]
            
            total_elevation_aggregated = 0
            if elev_columns:
                cleaned_elev = target_df[elev_columns[0]].astype(str).str.replace(r'[^\d.]', '', regex=True)
                total_elevation_aggregated = pd.to_numeric(cleaned_elev, errors='coerce').fillna(0).sum()
                
            total_seconds = 0
            for dur in target_df.get('Duration', []):
                if pd.notna(dur) and isinstance(dur, str) and ':' in dur:
                    parts = dur.split(':')
                    try:
                        if len(parts) == 3: total_seconds += int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                        elif len(parts) == 2: total_seconds += int(parts[0]) * 60 + int(parts[1])
                    except ValueError: pass
                        
            tot_hours = total_seconds // 3600
            tot_mins = (total_seconds % 3600) // 60
            total_time_str = f"{tot_hours}h {tot_mins}m" if tot_hours > 0 else f"{tot_mins}m"
            
            st.markdown(
                f"""
                <div style='display: flex; justify-content: space-around; background: #ffffff; padding: 14px; border-radius: 8px; margin-bottom: 20px; border: 1px solid #2c313c;'>
                    <div style='text-align: center;'>
                        <div style='font-size: 10px; color: #5c6370; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; font-weight: 600;'>Aggregated Distance</div>
                        <div style='font-size: 18px; font-weight: bold; color: #000000;'>{total_miles_aggregated:,.2f} {unit_abbr}</div>
                    </div>
                    <div style='text-align: center;'>
                        <div style='font-size: 10px; color: #5c6370; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; font-weight: 600;'>Aggregated Duration</div>
                        <div style='font-size: 18px; font-weight: bold; color: #000000;'>{total_time_str}</div>
                    </div>
                    <div style='text-align: center;'>
                        <div style='font-size: 10px; color: #5c6370; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; font-weight: 600;'>Aggregated Ascent</div>
                        <div style='font-size: 18px; font-weight: bold; color: #000000;'>{total_elevation_aggregated:,.0f} ft</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            if REPORTLAB_AVAILABLE:
                pdf_data_stream = generate_pdf_report(
                    target_df, current_header_title, unit_abbr, 
                    total_miles_aggregated, total_time_str, total_elevation_aggregated,
                    view_mode=st.session_state.calendar_display_view, cal_month_name=cal_month_name, cal_year=cal_year, cal_df=cal_df
                )
                if pdf_data_stream:
                    st.download_button(label="📄 Export Data to PDF Report", data=pdf_data_stream, file_name=f"running_report_{cal_year}_{cal_month_name.replace(' ', '_')}.pdf", mime="application/pdf")
            # 1. Create your layout navigation columns
            nav_col1, nav_col2, nav_col3 = st.columns([0.15, 0.7, 0.15])

            # 2. Extract current integers dynamically from your app's session state dropdown records
            current_year_int = int(st.session_state.grid_year_dropdown)
            
            # Map month name back to a 1-12 integer for math parsing
            current_month_str = st.session_state.grid_month_dropdown
            if current_month_str in month_names:
                current_month_int = month_names.index(current_month_str) + 1
            else:
                current_month_int = 1 # Fallback default to January if viewing 'All Months'

            # 3. Calculate adjacent dates cleanly in background memory
            prev_month = current_month_int - 1 if current_month_int > 1 else 12
            prev_year = current_year_int if current_month_int > 1 else current_year_int - 1
            next_month = current_month_int + 1 if current_month_int < 12 else 1
            next_year = current_year_int if current_month_int < 12 else current_year_int + 1

            # 4. Convert math results into string configuration tags for your button args
            month_options_list = ["All Months"] + month_names
            prev_month_str = month_options_list[prev_month] if current_month_str != "All Months" else "All Months"
            next_month_str = month_options_list[next_month] if current_month_str != "All Months" else "All Months"
        
            # 5. Render your directional arrows safely
            with nav_col1:
                if has_prev: 
                    st.button(
                        "◀", 
                        key=f"prev_nav_btn_{st.session_state.grid_year_dropdown}_{st.session_state.grid_month_dropdown}", 
                        width="stretch", 
                        on_click=handle_navigation_callback, 
                        args=(prev_year, prev_month_str)
                    )

            with nav_col2:
                st.markdown(f"<h3 style='text-align: center; color: white; margin-top: 5px; margin-bottom: 5px; letter-spacing: 1px;'>{current_header_title}</h3>", unsafe_allow_html=True)
            with nav_col3:

                if has_next: st.button("▶", key=f"next_nav_btn_{st.session_state.grid_year_dropdown}_{st.session_state.grid_month_dropdown}", width="stretch", on_click=handle_navigation_callback, args=(next_year, next_month_str))




















            # Full Year View
            if is_year_view:
                table_body_html = ""
                
                # 🥇 INITIALIZE ALL-TIME YEAR GRAND OVERVIEW TRACKERS
                total_miles_aggregated = 0.0
                total_seconds = 0
                total_elevation_aggregated = 0.0
                
                for m_idx in range(1, 13):
                    m_matrix = calendar.monthcalendar(cal_year, m_idx)
                    m_name = month_names[m_idx - 1]
                    m_df = target_df[target_df['Month_Int'] == m_idx]
                    
                    table_body_html += f"<tr><td colspan='6' style='background-color: #1a1c23; color: #00ffcc; font-weight: bold; padding: 10px; text-transform: uppercase;'>📅 {m_name.upper()} LOGS</td></tr>"
                    m_dist, m_seconds, m_elev = 0.0, 0, 0.0
                    
                    for w_idx, week in enumerate(m_matrix):
                        week_has_days = False
                        week_dist, week_seconds, week_elev = 0.0, 0, 0.0
                        week_rows_buffer = ""
                        
                        for day in week:
                            if day == 0: continue
                            week_has_days = True
                            target_date_str = f"{cal_year}-{m_idx:02d}-{day:02d}"
                            day_runs = cal_df[cal_df['Formatted_Date'] == target_date_str]
                            day_runs = target_df[target_df['Formatted_Date'] == target_date_str]
                            
                            # 🪵 TEMPORARY DIAGNOSTIC PRINT
                            # --- 🏃 WORKOUT DAY RUN CONTAINER BLOCK ---
                            if not day_runs.empty:
                                # 🪵 LOG 1: Year View Spreadsheet Console Diagnostic Tracker
                                # Active multi-run row iterator loop to build distinct <tr> elements
                                for loop_idx, (_, run_row) in enumerate(day_runs.iterrows()):
                                    
                                    run_dist = float(run_row['Display_Distance'])
                                    run_time = str(run_row.get('Duration', '--:--'))
                                    raw_p = run_row.get('pace', '—')

                                    # 🧮 1. DURATION-TO-MINUTES CONVERTER FUNCTION
                                    def duration_str_to_minutes(d_str):
                                        try:
                                            parts = [int(p) for p in str(d_str).strip().split(':')]
                                            if len(parts) == 3:   # HH:MM:SS
                                                return parts[0]*60 + parts[1] + parts[2]/60.0
                                            elif len(parts) == 2: # MM:SS
                                                return parts[0] + parts[1]/60.0
                                            return 0.0
                                        except Exception:
                                            return 0.0

                                    # 🧮 2. EVALUATE DIRECT RUN PACE DECIMAL SIZES SAFELY
                                    raw_p_str = str(raw_p).strip().lower()
                                    is_invalid_pace = pd.isna(raw_p) or raw_p_str in ["nan", "—", "-", ""]

                                    run_pace_decimal = 0.0
                                    if not is_invalid_pace:
                                        try:
                                            float_p = float(raw_p)
                                            if float_p > 0:
                                                run_pace_decimal = float_p
                                        except (ValueError, TypeError):
                                            pass

                                    # 🧮 3. BACKUP TIME-DISTANCE RECALCULATOR IF VALUES ARE EMPTY
                                    if run_pace_decimal == 0.0 and run_dist > 0:
                                        total_minutes = duration_str_to_minutes(run_time)
                                        if total_minutes > 0:
                                            run_pace_decimal = total_minutes / run_dist

                                    # 🧮 4. BUILD THE STANDARDIZED PACE TEXT FIELD STRING
                                    if run_pace_decimal > 0:
                                        m_part = int(run_pace_decimal)
                                        s_part = int(round((run_pace_decimal - m_part) * 60))
                                        if s_part == 60:
                                            m_part += 1
                                            s_part = 0
                                        run_pace = f"{m_part}:{s_part:02d} min/{unit_abbr.lower()}"
                                    else:
                                        run_pace = f"— min/{unit_abbr.lower()}"
                                    # =====================================================================
                                    # 🎽 AMBIGUITY-SAFE: SPREADSHEET VIEW PATCH INJECTOR
                                    # =====================================================================
                                    raw_p_cell = run_row.get("earned_patches", [])
                                    run_patches_list = []
                                    if isinstance(raw_p_cell, list):
                                        run_patches_list = raw_p_cell
                                    elif isinstance(raw_p_cell, str):
                                        try:
                                            import json
                                            run_patches_list = json.loads(raw_p_cell.replace("'", '"'))
                                        except Exception:
                                            run_patches_list = []

                                    if isinstance(run_patches_list, list) and len(run_patches_list) > 0:
                                        badge_emojis = " ".join([p.get("icon", "") for p in run_patches_list if isinstance(p, dict) and "icon" in p])
                                        #if badge_emojis.strip():
                                        #    run_pace = f"{run_pace}   {badge_emojis}"
                                    # =====================================================================

                                    day_elevation = 0.0
                                    if elev_cols:
                                        raw_elev_val = run_row.get(elev_cols[0], "0")
                                        cleaned_run_elev = ''.join(c for c in str(raw_elev_val) if c.isdigit() or c == '.')
                                        if cleaned_run_elev:
                                            day_elevation = float(cleaned_run_elev)

                                    # Update your run metrics accumulators
                                    week_dist += run_dist
                                    m_dist += run_dist
                                    week_elev += day_elevation
                                    m_elev += day_elevation

                                    # Parse your runtime strings into seconds counters
                                    if isinstance(run_time, str) and ':' in run_time:
                                        parts = run_time.split(':')
                                        try:
                                            if len(parts) == 3:
                                                week_seconds += int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                                                m_seconds += int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                                            elif len(parts) == 2:
                                                week_seconds += int(parts[0]) * 60 + int(parts[1])
                                                m_seconds += int(parts[0]) * 60 + int(parts[1])
                                        except ValueError:
                                            pass

                                    # ─── 🛠️   REPOSITION PATCHES AFTER DURATION CELL LAYER ───
                                    raw_patches_array = run_row.get("earned_patches", run_row.get("patches", []))
                                    extracted_emojis = []
                                    if isinstance(run_patches_list, list):
                                        for patch in run_patches_list:
                                            if isinstance(patch, dict):
                                                icon_char = patch.get("icon", patch.get("emoji", ""))
                                                if icon_char:
                                                    extracted_emojis.append(icon_char)
                                            elif isinstance(patch, str):
                                                award_id = patch.lower().strip()
                                                config_icon = "🏅"

                                                if cfg and hasattr(cfg, "FINAL_METRIC_CONFIG"):
                                                    award_rules = cfg.FINAL_METRIC_CONFIG.get(award_id, {})
                                                    config_icon = award_rules.get("icon", award_rules.get("emoji", "🏅"))
                                                elif cfg and hasattr(cfg, "METRIC_CONFIG"):
                                                    award_rules = cfg.METRIC_CONFIG.get(award_id, {})
                                                    config_icon = award_rules.get("icon", award_rules.get("emoji", "🏅"))

                                                if config_icon == "🏅":
                                                    fallback_map = {
                                                        "deer": "🦌", "bighorn": "🐏", "overdrive": "💥",
                                                        "endurance_laurel": "📜", "cardio_cyborg": "🫀",
                                                        "medal_speed_demon": "⚡", "patch_altitude_titan": "🏔️  ",
                                                        "patch_cold_warrior": "❄️"
                                                    }
                                                    config_icon = fallback_map.get(award_id, "🏅")

                                                extracted_emojis.append(config_icon)

                                    patch_emojis = "".join(extracted_emojis)

                                    # 📋 2. Append to your rich HTML string template cell structure (Inserts inside the row loop)
                                    table_body_html += f"<tr class='day-row'><td><b>{target_date_str}</b></td><td style='color: #00ffff; font-weight: bold;'>🏃 RUN</td><td>{run_dist:.2f} {unit_abbr}</td><td>{run_time} <span style='margin-left: 6px;'>{patch_emojis}</span></td><td>{run_pace}</td><td>{day_elevation:,.0f} ft</td></tr>"

                            # --- 🧘 REST DAY CONTAINER BLOCK ---
                            else:
                                table_body_html += f"<tr class='day-row'><td>{target_date_str}</td><td style='color: #ffcc00; font-weight: bold;'>🧘 REST DAY</td><td style='color: #7e8794;'>—</td><td style='color: #7e8794;'>—</td><td style='color: #7e8794;'>—</td><td style='color: #7e8794;'>—</td></tr>"



  
                            #### --- 🏃 ACTIVE WORKOUT TRACKER ---
                            ###if not day_runs.empty:
                            ###    run_row = day_runs.iloc[0]
                            ###    run_dist = float(run_row['Display_Distance'])
                            ###    run_time = run_row.get('Duration', '--:--')
                            ###    raw_p = run_row.get('pace', '—')

                            ###    # 🧮 1. DURATION-TO-MINUTES CONVERTER FUNCTION
                            ###    def duration_str_to_minutes(d_str):
                            ###        try:
                            ###            parts = [int(p) for p in str(d_str).strip().split(':')]
                            ###            if len(parts) == 3:   # HH:MM:SS
                            ###                return parts[0]*60 + parts[1] + parts[2]/60.0
                            ###            elif len(parts) == 2: # MM:SS
                            ###                return parts[0] + parts[1]/60.0
                            ###            return 0.0
                            ###        except Exception:
                            ###            return 0.0

                            ###    # 🧮 2. EVALUATE DIRECT RUN PACE DECIMAL SIZES
                            ###    is_invalid_pace = pd.isna(raw_p) or str(raw_p).lower() == "nan" or raw_p == "—"
                            ###    if not is_invalid_pace:
                            ###        try:
                            ###            float_p = float(raw_p)
                            ###            run_pace_decimal = float_p if float_p > 0 else 0.0
                            ###        except (ValueError, TypeError):
                            ###            run_pace_decimal = 0.0
                            ###    else:
                            ###        run_pace_decimal = 0.0

                            ###    # 🧮 3. BACKUP TIME-DISTANCE RECALCULATOR IF VALUES ARE EMPTY
                            ###    if run_pace_decimal == 0.0 and run_dist > 0:
                            ###        total_minutes = duration_str_to_minutes(run_time)
                            ###        if total_minutes > 0:
                            ###            run_pace_decimal = total_minutes / run_dist

                            ###    # 🧮 4. BUILD THE STANDARDIZED PACE TEXT FIELD STRING
                            ###    if run_pace_decimal > 0:
                            ###        m_part = int(run_pace_decimal)
                            ###        s_part = int(round((run_pace_decimal - m_part) * 60))
                            ###        if s_part == 60:
                            ###            m_part += 1
                            ###            s_part = 0
                            ###        run_pace = f"{m_part}:{s_part:02d} min/{unit_abbr.lower()}"
                            ###    else:
                            ###        run_pace = f"— min/{unit_abbr.lower()}"

                            ###    # =====================================================================
                            ###    # 🎽 5. AMBIGUITY-SAFE PATCH ASSET INJECTOR (FIXED!)
                            ###    # =====================================================================
                            ###    raw_patches_cell = run_row.get('earned_patches', [])
                            ###    run_patches_list = []
                            ###    
                            ###    # Use explicit type checks to safeguard against multi-element array ambiguity
                            ###    if isinstance(raw_patches_cell, list):
                            ###        run_patches_list = raw_patches_cell
                            ###    elif isinstance(raw_patches_cell, str):
                            ###        try:
                            ###            import json
                            ###            cleaned_str = raw_patches_cell.replace("'", '"')
                            ###            run_patches_list = json.loads(cleaned_str)
                            ###        except Exception:
                            ###            run_patches_list = []
                            ###                
                            ###    if isinstance(run_patches_list, list) and len(run_patches_list) > 0:
                            ###        patch_emoji_string = " ".join([
                            ###            p.get('icon', '') if isinstance(p, dict) else '' 
                            ###            for p in run_patches_list
                            ###        ])
                            ###    else:
                            ###        patch_emoji_string = ""

                            ###    if patch_emoji_string.strip():
                            ###        run_pace = f"{run_pace}   {patch_emoji_string}"
                            ###    # =====================================================================
                            ###    # 🧗 6. EXTRACT CLIMBED ELEVATION VALUES
                            ###    day_elevation = 0.0
                            ###    if elev_cols:
                            ###        raw_elev_val = run_row.get(elev_cols[0], "0")
                            ###        cleaned_run_elev = ''.join(c for c in str(raw_elev_val) if c.isdigit() or c == '.')
                            ###        if cleaned_run_elev:
                            ###            day_elevation = float(cleaned_run_elev)

                            ###    # 📈 7. INCREMENT RUN METRICS ACCUMULATORS
                            ###    week_dist += run_dist
                            ###    m_dist += run_dist
                            ###    total_miles_aggregated += run_dist
                            ###    
                            ###    week_elev += day_elevation
                            ###    m_elev += day_elevation
                            ###    total_elevation_aggregated += day_elevation

                            ###    # ⏱️ 8. PARSE TIME STRINGS INTO LEADERBOARD SECONDS COUNTERS
                            ###    if isinstance(run_time, str) and ':' in run_time:
                            ###        parts = run_time.split(':')
                            ###        try:
                            ###            if len(parts) == 3:
                            ###                run_secs = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                            ###            elif len(parts) == 2:
                            ###                run_secs = int(parts[0]) * 60 + int(parts[1])
                            ###            else:
                            ###                run_secs = 0
                            ###            week_seconds += run_secs
                            ###            m_seconds += run_secs
                            ###            total_seconds += run_secs
                            ###        except ValueError:
                            ###            pass

                            ###    # 📋 9. COMPILE RUN LOG AS AN HTML COMPONENT ROW
                            ###    week_rows_buffer += f"<tr class='day-row'><td><b>{target_date_str}</b></td><td style='color: #00ffff; font-weight: bold;'>🏃 RUN</td><td>{run_dist:.2f} {unit_abbr}</td><td>{run_time}</td><td>{run_pace}</td><td>{day_elevation:,.0f} ft</td></tr>"
                            ###
                            #### --- 🧘 SAFE REST DAY HANDLER ---
                            ###else:
                            ###    week_rows_buffer += f"<tr class='day-row'><td>{target_date_str}</td><td style='color: #ffcc00; font-weight: bold;'>🧘 REST DAY</td><td style='color: #7e8794;'>—</td><td style='color: #7e8794;'>—</td><td style='color: #7e8794;'>—</td><td style='color: #7e8794;'>—</td></tr>"
                        
                        # 📝 10. FLUSH WEEK ROWS TO MASTER OUTPUT AND COMPLEMENT WEEKLY TOTAL SUMMARIES
                        if week_has_days:
                            table_body_html += week_rows_buffer
                            w_hours = week_seconds // 3600
                            w_mins = (week_seconds % 3600) // 60
                            w_time_str = f"{w_hours}h {w_mins}m" if w_hours > 0 else f"{w_mins}m"
                            table_body_html += f"<tr class='weekly-total-row'><td>WEEK {w_idx + 1} TOTALS</td><td>📊 SUMMARY</td><td>{week_dist:.2f} {unit_abbr}</td><td>{w_time_str if week_seconds > 0 else '—'}</td><td>—</td><td>{week_elev:,.0f} ft</td></tr>"

                    # 📝 11. INJECT MONTHLY SUMMARY ROW ONCE WEEKS CONCLUDE
                    m_hours = m_seconds // 3600
                    m_mins = (m_seconds % 3600) // 60
                    table_body_html += f"<tr class='monthly-total-row'><td>{m_name.upper()} TOTALS</td><td>📈 MONTH SUMMARY</td><td>{m_dist:.2f} {unit_abbr}</td><td>{f'{m_hours}h {m_mins}m' if m_seconds > 0 else '—'}</td><td>—</td><td>{m_elev:,.0f} ft</td></tr>"

                # 📝 12. INJECT FINAL YEARLY GRAND OVERVIEW TOTALS ROW AT BOTTOM
                y_hours = total_seconds // 3600
                y_mins = (total_seconds % 3600) // 60
                table_body_html += f"<tr class='yearly-total-row'><td>🏆 {cal_year} YEAR TOTALS</td><td>🌟 GRAND OVERVIEW</td><td>{total_miles_aggregated:.2f} {unit_abbr}</td><td>{f'{y_hours}h {y_mins}m' if total_seconds > 0 else '—'}</td><td>—</td><td>{total_elevation_aggregated:,.0f} ft</td></tr>"

                year_html = f"<table class='spreadsheet-table'><thead><tr><th>Run Date</th><th>Status</th><th>Distance</th><th>Duration</th><th>Average Pace</th><th>Ascent Gain</th></tr></thead><tbody>{table_body_html}</tbody></table>"
                st.markdown(year_html, unsafe_allow_html=True)






            # =========================================================================
            # 📊 SPREADSHEET DISPLAY VIEW (IN-MEMORY BUTTON LEDGER + HOVER STYLING)
            # =========================================================================
            elif st.session_state.calendar_display_view == "📊 Spreadsheet View":

                if cal_month_name != "All Months":
                    # Find the exact numeric index of your selected month (e.g., "January" -> 1)
                    selected_month_idx = month_names.index(cal_month_name) + 1
                    months_to_loop = [selected_month_idx]
                else:
                    # Otherwise, let it default to its original all-month array sequence
                    months_to_loop = sorted(target_df['Month_Int'].unique()) if not target_df.empty else []

                # Inject a custom stylesheet to completely strip out native button widget skins

                st.markdown('<div class="spreadsheet-view-marker"></div>', unsafe_allow_html=True)

                st.markdown("""
                <style>
/* 🔒 SCANNED CONTEXT LOCATOR: Ensures the widget block expands to the absolute container edges */
div[data-testid="stVerticalBlock"]:has(.spreadsheet-view-marker) div[data-testid="stButton"] {
    width: 100% !important;
}


/* 🏃 ACTIVE RUN ENTRIES: Targets the button and ALL inner text labels to stop column squishing */
div[data-testid="stVerticalBlock"]:has(.spreadsheet-view-marker) div[data-testid="stButton"] button,
div[data-testid="stVerticalBlock"]:has(.spreadsheet-view-marker) div[data-testid="stButton"] button * {
    background-color: transparent !important;
    background: transparent !important;
    background-image: none !important;         /* Completely strips out native button gradient colors */
    color: #E2E8F0 !important;                 
    border: none !important;
    text-align: left !important;
    justify-content: flex-start !important;
    font-family: monospace !important;
    font-size: 13px !important;
    width: 100% !important;
    max-width: 100% !important;                /* 🎯 ADD THIS: Prevents the horizontal row asset from overflowing window limits */
    overflow: hidden !important;               /* 🎯 ADD THIS: Sharp-clips the hover color overlay strictly inside the visible row borders */
    box-shadow: none !important;
    outline: none !important;
    white-space: pre !important;               /* 🔥 CRITICAL: Overrides inner span styles to honor all padding spaces */
    line-height: 16px !important;              /* 🔍 Locks text height */
    box-sizing: border-box !important;          /* 🔍 Syncs layout math */
    transition: background-color 0.1s ease-in-out, color 0.1s ease-in-out;
}


/* 🛠️ WIDGET BASE PROPERTIES: Defines row boundary lines and vertical padding heights */
div[data-testid="stVerticalBlock"]:has(.spreadsheet-view-marker) div[data-testid="stButton"] button {
    border-bottom: 1px solid #2D3748 !important;      
    padding: 14px 16px !important;             /* Tall, clean premium row expansion height */
    border-radius: 0px !important;
    margin: 0px !important;
    transition: background-color 0.1s ease-in-out, color 0.1s ease-in-out;
}

/* 🌟 INVERTED HOVER STATE: Semi-transparent overlay mask activates only on hover events */
div[data-testid="stVerticalBlock"]:has(.spreadsheet-view-marker) div[data-testid="stButton"] button:hover {
    background-color: rgba(255, 255, 255, 0.12) !important; 
    color: #00ffcc !important;                             
    cursor: pointer !important;
}

/* 🛑 FOCUS & ACTIVE INSULATION: Stops clicked buttons from shifting back to solid white blocks */
div[data-testid="stVerticalBlock"]:has(.spreadsheet-view-marker) div[data-testid="stButton"] button:focus,
div[data-testid="stVerticalBlock"]:has(.spreadsheet-view-marker) div[data-testid="stButton"] button:active,
div[data-testid="stVerticalBlock"]:has(.spreadsheet-view-marker) div[data-testid="stButton"] button:focus-visible {
    background-color: transparent !important;
    background: transparent !important;
    background-image: none !important;
    box-shadow: none !important;
    outline: none !important;
}

  /* 🧘 REST DAY & SUMMARY ENTRIES: Matches monospace alignment matrices while making the background lighter */
.spreadsheet-text-block {
    background: transparent !important;
    border-bottom: 1px solid #2D3748 !important;
    font-family: monospace !important;
    font-size: 13px !important;
    line-height: 16px !important;              /* 🔒 Locks text height to match active run rows */
    padding: 12px 16px !important;
    width: 100% !important;
    box-sizing: border-box !important;          /* 🔒 Syncs layout math to match active run rows */
    display: block !important;
    white-space: pre !important;
}

  /* 🔍 ADD THESE EXACT LINES RIGHT HERE: */
                    div[data-testid="stVerticalBlock"]:has(.spreadsheet-view-marker) {
                        gap: 0px !important;
                    }
                    /* 🧱 VERTICAL GAP FIX FOR REST DAYS: Strips out Streamlit's default markdown block wrapper margins */
                    div[data-testid="stVerticalBlock"]:has(.spreadsheet-view-marker) div[data-testid="stMarkdown"],
                    div[data-testid="stVerticalBlock"]:has(.spreadsheet-view-marker) div[data-testid="stMarkdownContainer"] p {
                        margin: 0px !important;
                        padding: 0px !important;
                    }

                    /* 🔍 PASTE THE NEW TRANSITION GAP RULE RIGHT HERE: */
                    div[data-testid="stVerticalBlock"]:has(.spreadsheet-view-marker) div[data-testid="stMarkdown"] + div[data-testid="stButton"],
                    div[data-testid="stVerticalBlock"]:has(.spreadsheet-view-marker) div[data-testid="stButton"] + div[data-testid="stMarkdown"] {
                        margin-top: 12px !important;
                    }
                </style>
                """, unsafe_allow_html=True)

                # Render Table Header Layout Block using high-contrast text sizing scales

                st.markdown('<div style="font-family: monospace; font-size: 13px; font-weight: bold; color: #00ffcc; padding: 12px 16px; background-color: #1a1c23; border-bottom: 2px solid #00ffcc; display: block; width: 100%; box-sizing: border-box; white-space: pre; margin-bottom: 12px;">DATE        STATUS         DISTANCE       DURATION TIME       OVERALL PACE           CLIMBED ELEV</div>', unsafe_allow_html=True)

                # Render Table Header Layout Block using high-contrast text sizing scales
                #st.markdown('<div style="font-family: monospace; font-size: 13px; font-weight: bold; color: #00ffcc; padding: 14px 16px; background-color: #1a1c23; border-bottom: 2px solid #00ffcc; display: block; width: 100%; box-sizing: border-box; white-space: pre;">DATE       | STATUS       | DISTANCE     | DURATION TIME     | OVERALL PACE         | CLIMBED ELEV</div>', unsafe_allow_html=True)




                table_body_html = ""
                months_to_loop = range(1, 13) if cal_month_name == "All Months" else [cal_month]
                
                for loop_m in months_to_loop:


                    m_name = month_names[loop_m - 1]
                    cal_matrix = calendar.monthcalendar(cal_year, loop_m)
                    m_dist, m_seconds, m_elev = 0.0, 0, 0.0

                    if cal_month_name == "All Months":
                        st.markdown(f"<div style='font-family: monospace; font-size: 13px; font-weight: bold; color: #00ffcc; padding: 12px 16px; background-color: #1a1c23; text-transform: uppercase; border-bottom: 1px solid #2D3748;'>📅 {month_names[loop_m - 1].upper()} LOGS</div>", unsafe_allow_html=True)
                        
                    cal_matrix = calendar.monthcalendar(cal_year, loop_m)
                    m_dist, m_seconds, m_elev = 0.0, 0, 0.0

                    for w_idx, week in enumerate(cal_matrix): 
                        week_has_days = False
                        week_dist, week_seconds, week_elev = 0.0, 0, 0.0
                        
                        for day in week: 
                            if day == 0: continue
                            week_has_days = True
                            target_date_str = f"{cal_year}-{loop_m:02d}-{day:02d}"
                            
                            # Query your master dataframe array safely
                            day_runs = cal_df[cal_df['Formatted_Date'] == target_date_str] if cal_df is not None else pd.DataFrame()
                            
                            # --- 🏃 Workout Record Processing Path ---
                            if not day_runs.empty:
                                for loop_idx, (_, run_row) in enumerate(day_runs.iterrows()):
                                    run_dist = float(run_row['Display_Distance'])
                                    run_time = str(run_row.get('Duration', '--:--'))
                                    raw_p = run_row.get('pace', '—')

                                    def duration_str_to_minutes(d_str):
                                        try:
                                            parts = [int(p) for p in str(d_str).strip().split(':')]
                                            if len(parts) == 3:   # HH:MM:SS
                                                return parts[0]*60 + parts[1] + parts[2]/60.0
                                            elif len(parts) == 2: # MM:SS
                                                return parts[0] + parts[1]/60.0
                                            return 0.0
                                        except Exception:
                                            return 0.0

                                    raw_p_str = str(raw_p).strip().lower()
                                    is_invalid_pace = pd.isna(raw_p) or raw_p_str in ["nan", "—", "-", ""]

                                    run_pace_decimal = 0.0
                                    if not is_invalid_pace:
                                        try:
                                            float_p = float(raw_p)
                                            if float_p > 0:
                                                run_pace_decimal = float_p
                                        except (ValueError, TypeError):
                                            pass

                                    if run_pace_decimal == 0.0 and run_dist > 0:
                                        total_minutes = duration_str_to_minutes(run_time)
                                        if total_minutes > 0:
                                            run_pace_decimal = total_minutes / run_dist

                                    if run_pace_decimal > 0:
                                        m_part = int(run_pace_decimal)
                                        s_part = int(round((run_pace_decimal - m_part) * 60))
                                        if s_part == 60:
                                            m_part += 1
                                            s_part = 0
                                        run_pace = f"{m_part}:{s_part:02d} min/{unit_abbr.lower()}"
                                    else:
                                        run_pace = f"— min/{unit_abbr.lower()}"

                                    raw_p_cell = run_row.get("earned_patches", [])
                                    run_patches_list = []
                                    if isinstance(raw_p_cell, list):
                                        run_patches_list = raw_p_cell
                                    elif isinstance(raw_p_cell, str):
                                        try:
                                            import json
                                            run_patches_list = json.loads(raw_p_cell.replace("'", '"'))
                                        except Exception:
                                            run_patches_list = []

                                    if isinstance(run_patches_list, list) and len(run_patches_list) > 0:
                                        badge_emojis = " ".join([p.get("icon", "") for p in run_patches_list if isinstance(p, dict) and "icon" in p])
                                        #if badge_emojis.strip():
                                        #    run_pace = f"{run_pace}  {badge_emojis}"

                                    day_elevation = 0.0
                                    if elev_cols:
                                        raw_elev_val = run_row.get(elev_cols[0], "0")
                                        cleaned_run_elev = ''.join(c for c in str(raw_elev_val) if c.isdigit() or c == '.')
                                        if cleaned_run_elev:
                                            day_elevation = float(cleaned_run_elev)

                                    week_dist += run_dist
                                    m_dist += run_dist
                                    week_elev += day_elevation
                                    m_elev += day_elevation

                                    if isinstance(run_time, str) and ':' in run_time:
                                        parts = run_time.split(':')
                                        try:
                                            if len(parts) == 3:
                                                week_seconds += int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                                                m_seconds += int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                                            elif len(parts) == 2:
                                                week_seconds += int(parts[0]) * 60 + int(parts[1])
                                                m_seconds += int(parts[0]) * 60 + int(parts[1])
                                        except ValueError:
                                            pass

                                    raw_patches_array = run_row.get("earned_patches", run_row.get("patches", []))
                                    extracted_emojis = []
                                    if isinstance(run_patches_list, list):
                                        for patch in run_patches_list:
                                            if isinstance(patch, dict):
                                                icon_char = patch.get("icon", patch.get("emoji", ""))
                                                if icon_char:
                                                    extracted_emojis.append(icon_char)
                                            elif isinstance(patch, str):
                                                award_id = patch.lower().strip()
                                                config_icon = "🏅"
                                                if cfg and hasattr(cfg, "FINAL_METRIC_CONFIG"):
                                                    config_icon = cfg.FINAL_METRIC_CONFIG.get(award_id, {}).get("icon", "🏅")
                                                extracted_emojis.append(config_icon)

                                    #patch_emojis = "".join(extracted_emojis)
                                    #dur_display = f"{run_time}  {patch_emojis}".strip()
                                    dur_display = run_time.strip()


# Compile padded character matrices to establish clear tracking headers alignment
                                    d_col = f"{target_date_str:<10}"
                                    s_col = f"{'🏃 RUN':<12}"
                                    dist_col = f"{f'{run_dist:.2f} {unit_abbr.lower()}':<12}"
                                    t_col = f"{dur_display:<17}"
                                    p_col = f"{run_pace:<20}"
                                    e_col = f"+{day_elevation:,.0f} ft"
                                    
                                    # 🎯 Increased the trailing padding gap to 6 explicit spaces ("      ") 
                                    # right before `{badge_emojis}` to create a clean, intentional separation 
                                    # between your final elevation metric and your earned milestone badges.
                                    row_text = f"{d_col}  {s_col}  {dist_col}  {t_col}  {p_col}  {e_col}      {badge_emojis}".strip()
 
                                    # Render native in-memory click trackers
                                    st.markdown(f'<div class="spreadsheet-row-container">', unsafe_allow_html=True)
                                    if st.button(row_text, key=f"ledger_run_select_click_{target_date_str}_{loop_idx}", width="stretch"):
                                        st.session_state.selected_activity_date = target_date_str
                                        st.rerun()
                                    st.markdown('</div>', unsafe_allow_html=True)

                            # --- 🧘 Rest Day Processing Path (Retains dark background styling perfectly) ---
                            else:
                                d_col = f"{target_date_str:<10}"
                                s_col = f"{'🧘 REST DAY':<12}"
                                dist_col = f"{'—':<12}"
                                t_col = f"{'—':<17}"
                                p_col = f"{'—':<20}"
                                e_col = "—"
                                
                                rest_html = f"<div class='spreadsheet-text-block' style='color: #E2E8F0;'>{d_col}  <span style='color: #ffcc00; font-weight: bold;'>{s_col}</span>  <span style='color: #7e8794;'>{dist_col}</span>  <span style='color: #7e8794;'>{t_col}</span>  <span style='color: #7e8794;'>{p_col}</span>  <span style='color: #7e8794;'>{e_col}</span></div>"
                                st.markdown(rest_html, unsafe_allow_html=True)

                        if week_has_days:
                            w_hours = week_seconds // 3600
                            w_mins = (week_seconds % 3600) // 60
                            w_time_str = f"{w_hours}h {w_mins}m" if w_hours > 0 else f"{w_mins}m"
                            
                            d_col = f"{f'WEEK {w_idx + 1} TOTALS':<10}"
                            s_col = f"{'📊 SUMMARY':<12}"
                            dist_col = f"{f'{week_dist:.2f} {unit_abbr.lower()}':<12}"
                            t_col = f"{w_time_str if week_seconds > 0 else '—':<17}"
                            p_col = f"{'—':<20}"
                            e_col = f"{week_elev:,.0f} ft"
                            
                            summary_html = f"<div class='spreadsheet-text-block' style='background-color: #1a1c23; font-weight: bold; border-color: #4A5568 !important; color: #E2E8F0;'>{d_col}  <span style='color: #00ffcc;'>{s_col}</span>  {dist_col}  {t_col}  <span style='color: #7e8794;'>{p_col}</span>  {e_col}</div>"
                            st.markdown(summary_html, unsafe_allow_html=True)
                            st.markdown("<div style='margin-bottom: 4px;'></div>", unsafe_allow_html=True)



                    # -----------------------------------------------------------------
                    # 🧮 FIX 2: INDENT THE MONTHLY TOTALS INSIDE THE "loop_m" BLOCK
                    # -----------------------------------------------------------------
                    # This position fires EXACTLY when a month's weeks finish rendering.
                    month_totals = get_monthly_totals(target_df, cal_year, m_name)
                    m_dist_raw = f"{month_totals['distance']:.2f} {unit_abbr.lower()}"
                    
                    d_col_m = f"{f'{m_name.upper()}':<10}"
                    s_col_m = f"{'TOTALS':<12}"
                    dist_col_m = f"{m_dist_raw:<12}"
                    t_col_m = f"{month_totals['duration']:<17}"
                    p_col_m = f"{'—':<20}"
                    e_col_m = f"{month_totals['elevation']:,.0f} ft"

                    month_totals_html = (
                        f"<div class='spreadsheet-text-block' style='"
                        f"background-color: #1a2230; color: #FFFFFF; font-weight: bold; "
                        f"border: 1px solid #00ffff; box-shadow: inset 0 0 4px rgba(0, 255, 255, 0.1);'>"
                        f"{d_col_m}  <span style='color: #00ffff;'>{s_col_m}</span>  "
                        f"{dist_col_m}  {t_col_m}  <span style='color: #7e8794;'>{p_col_m}</span>  "
                        f"<span style='color: #00ffff;'>{e_col_m}</span></div>"
                    )
                    st.markdown(month_totals_html, unsafe_allow_html=True)
                    st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)

                # =========================================================================
                # 🏆 FIX 3: RENDER THE GRAND YEARLY BANNER OUTSIDE THE MONTH LOOP
                # =========================================================================
                # Notice this is lined up with the "for loop_m" statement. It triggers once at the bottom.
                if cal_month_name == "All Months":
                    yearly_totals = get_monthly_totals(target_df, cal_year, "All Months")
                    y_dist_raw = f"{yearly_totals['distance']:.2f} {unit_abbr.lower()}"
                    
                    d_col_y = f"{f'{cal_year} ':<10}"
                    s_col_y = f"{'TOTALS ':<12}"
                    dist_col_y = f"{y_dist_raw:<12}"
                    t_col_y = f"{yearly_totals['duration']:<17}"
                    p_col_y = f"{'—':<20}"
                    e_col_y = f"{yearly_totals['elevation']:,.0f} ft"

                    grand_yearly_html = (
                        f"<div class='spreadsheet-text-block' style='"
                        f"background-color: #2c2104; color: #FFFFFF; font-weight: bold; "
                        f"border: 1px solid #ffcc00; box-shadow: inset 0 0 6px rgba(255, 204, 0, 0.2);'>"
                        f"{d_col_y}  <span style='color: #ffcc00;'>{s_col_y}</span>  "
                        f"{dist_col_y}  {t_col_y}  <span style='color: #7e8794;'>{p_col_y}</span>  "
                        f"<span style='color: #ffcc00;'>{e_col_y}</span></div>"
                    )
                    st.markdown(grand_yearly_html, unsafe_allow_html=True)
                    st.markdown("<div style='margin-bottom: 24px;'></div>", unsafe_allow_html=True)







            # Classic Grid View
            else:
                months_to_loop = range(1, 13) if cal_month_name == "All Months" else [cal_month]
                for loop_m in months_to_loop:
                    if cal_month_name == "All Months":
                        st.markdown(f"<h4 style='color: #00ffcc; border-bottom: 1px solid #3e4452; padding-top: 20px; padding-bottom: 5px; margin-bottom: 8px;'>🗓️ {month_names[loop_m - 1]}</h4>", unsafe_allow_html=True)
                        loop_m_df = cal_df[(cal_df['Year_Int'] == cal_year) & (cal_df['Month_Int'] == loop_m)]
                        m_miles = loop_m_df['Display_Distance'].sum()
                        
                        m_elev = 0.0
                        if elev_columns:
                            cleaned_m_elev = loop_m_df[elev_columns[0]].astype(str).str.replace(r'[^\d.]', '', regex=True)
                            m_elev = pd.to_numeric(cleaned_m_elev, errors='coerce').fillna(0).sum()
                            
                        m_seconds = 0
                        for dur in loop_m_df.get('Duration', []):
                            if pd.notna(dur) and isinstance(dur, str) and ':' in dur:
                                parts = dur.split(':')
                                try:
                                    if len(parts) == 3: m_seconds += int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                                    elif len(parts) == 2: m_seconds += int(parts[0]) * 60 + int(parts[1])
                                except ValueError: pass
                                    
                        m_hours = m_seconds // 3600
                        m_mins = (m_seconds % 3600) // 60
                        m_time_str = f"{m_hours}h {m_mins}m" if m_hours > 0 else f"{m_mins}m"
                        
                        st.markdown(
                            f"""
                            <div style='display: flex; justify-content: space-around; background: #ffffff; padding: 10px; border-radius: 6px; margin-bottom: 15px; border: 1px solid #2c313c;'>
                                <div style='text-align: center;'>
                                    <div style='font-size: 9px; color: #5c6370; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 2px; font-weight: 600;'>Monthly Distance</div>
                                    <div style='font-size: 15px; font-weight: bold; color: #000000;'>{m_miles:,.2f} {unit_abbr}</div>
                                </div>
                                <div style='text-align: center;'>
                                    <div style='font-size: 9px; color: #5c6370; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 2px; font-weight: 600;'>Monthly Duration</div>
                                    <div style='font-size: 15px; font-weight: bold; color: #000000;'>{m_time_str}</div>
                                </div>
                                <div style='text-align: center;'>
                                    <div style='font-size: 9px; color: #5c6370; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 2px; font-weight: 600;'>Monthly Ascent</div>
                                    <div style='font-size: 15px; font-weight: bold; color: #000000;'>{m_elev:,.0f} ft</div>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    
                    loop_matrix = calendar.monthcalendar(cal_year, loop_m)
                    days_headers = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                    header_cols = st.columns(7)
                    for i, h_name in enumerate(days_headers):
                        header_cols[i].markdown(f"<div class='original-day-header'>{h_name}</div>", unsafe_allow_html=True)

                    for week in loop_matrix:
                        cols = st.columns(7)
                        for idx, day in enumerate(week):
                            with cols[idx]:
                                if day == 0:
                                    st.markdown('<div class="cal-btn-placeholder"></div>', unsafe_allow_html=True)
                                else:
                                    target_date_str = f"{cal_year}-{loop_m:02d}-{day:02d}"
                                    day_runs = cal_df[cal_df['Formatted_Date'] == target_date_str]
                                    parity_suffix = "even" if day % 2 == 0 else "odd"

                                    # 🪵 FULL YEAR GRID TARGET LOOKUP DIAGNOSTIC
                                    if not day_runs.empty:
                                        # 🪵 LOG 1: Track full-year grid entries for multiple runs
                                        # Initialize aggregated holders for our display label text
                                        total_day_dist = 0.0
                                        duration_stamps = []

                                        # Inline tracker loop to unpack every single run on this specific day
                                        for loop_idx, (_, run_row) in enumerate(day_runs.iterrows()):
                                            total_day_dist += float(run_row['Display_Distance'])
                                            duration_stamps.append(str(run_row.get('Duration', '--:--')))
                                            
                                        # Compile individual duration metrics into a joined layout display (e.g. "02:53:23 + 00:06:54")
                                        joined_times = " + ".join(duration_stamps)

                                        # Construct the multi-line calendar button layout label text cleanly
                                        btn_label = f"{day}\n\n{total_day_dist:.1f}{unit_abbr}\n{joined_times}"

                                        # 🪵 STEP 3 DIAGNOSTIC: WHAT TEXT IS INSIDE THE BUTTON BOX?
                                        with st.container():
                                            st.markdown(f'<div class="run-{parity_suffix}-marker"></div>', unsafe_allow_html=True)
                                            if st.button(btn_label, key=f"run_{parity_suffix}_{target_date_str}"):
                                                st.session_state.selected_activity_date = target_date_str
                                                st.rerun()

                                    else:
                                        with st.container():
                                            st.markdown(f'<div class="rest-{parity_suffix}-marker"></div>', unsafe_allow_html=True)
                                            if st.button(f"{day}\n\n—\n—", key=f"rest_{parity_suffix}_{target_date_str}"):
                                                st.session_state.selected_activity_date = target_date_str
                                                st.rerun()

    # ==========================================
    # RIGHT SIDE PANEL: ADAPTIVE VIEWS & UPGRADES
    # ==========================================


    with main_layout_col2:
        if st.session_state.selected_activity_date:
            active_date = st.session_state.selected_activity_date
            matched_runs = df[df['Formatted_Date'] == active_date]

            if not matched_runs.empty:
                st.markdown(f"### 📊 Activity Log Summary: {active_date}")

                # 🏁 Loop opens cleanly
                for run_idx, (_, run_row_raw) in enumerate(matched_runs.iterrows()):
                    matched_run = run_row_raw.to_dict()

                    # Create a distinct visual header for multi-activity days
                    if len(matched_runs) > 1:
                        st.markdown(f"#### 🏃 Workout Activity #{run_idx + 1}")
                                        
                    # Single Run Elevation parsing (Moved inside loop)
                    run_elevation = 0.0     
                    if elev_columns:        
                        raw_elev_val = matched_run.get(elev_columns[0], "0")
                        cleaned_run_elev = ''.join(c for c in str(raw_elev_val) if c.isdigit() or c == '.')
                        parsed_elev = pd.to_numeric(cleaned_run_elev, errors='coerce')
                        if pd.notna(parsed_elev): 
                            run_elevation = parsed_elev

                    if "splits" in matched_run and isinstance(matched_run["splits"], list) and len(matched_run["splits"]) > 0:
                        try:
                            splits_df = pd.DataFrame(matched_run["splits"])
                            splits_df['Split Mile'] = "M" + splits_df['split_num'].astype(str)
                            
                            # Secure raw heart rate data into your preferred 'average_heart_rate' column
                            if 'average_heart_rate' not in splits_df.columns and 'avg_heart_rate' in splits_df.columns:
                                splits_df['average_heart_rate'] = splits_df['avg_heart_rate']
                            elif 'average_heart_rate' not in splits_df.columns:
                                splits_df['average_heart_rate'] = 120  # Baseline fallback if completely missing

                            # Safely resolve max_heart_rate for line tracking
                            if 'max_heart_rate' not in splits_df.columns:
                                splits_df['max_heart_rate'] = splits_df['average_heart_rate']

                            # Clean Heart Rate Color Assigner with explicit numeric coercion
                            def assign_bar_color_by_hr(avg_hr):
                                try:
                                    hr = int(float(avg_hr))
                                    bg_color, _, _ = get_hr_zone_style(hr)
                                    return bg_color
                                except:
                                    return "#A0AEC0" # Distinct grey fallback
                            
                            # Map colors directly over your cleaned average heart rate column
                            splits_df['Zone_Color'] = splits_df['average_heart_rate'].apply(assign_bar_color_by_hr)
                            
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
                            
                            st.caption(f"⏱️     Lap Split Profiles - Activity #{run_idx + 1} (Bars = Pace, Line = Max HR)") 
                            
                            import altair as alt
                            
                            # 1. Base Shared X-Axis Config
                            base_chart = alt.Chart(splits_df).encode(
                                x=alt.X('Split Mile:N', sort=None, title="Workout Segment")
                            )

                            # Shared Tooltip Definitions
                            shared_tooltips = [
                                alt.Tooltip('Split Mile', title='Split'),
                                alt.Tooltip('pace', title='Pace'),
                                alt.Tooltip('average_heart_rate:Q', title='Avg Heart Rate (bpm)'),
                                alt.Tooltip('max_heart_rate:Q', title='Max Peak HR (bpm)')
                            ]

                            # 2. Base Bar Layer (Pace heights, Colored by Average HR)
                            bar_layer = base_chart.mark_bar(opacity=0.85).encode(
                                y=alt.Y('Pace (Minutes):Q', title="Pace Minutes"),
                                color=alt.Color('Zone_Color:N').scale(None),
                                tooltip=shared_tooltips
                            )

                            # 3. Base Line Layer (Max Heart Rate running across)
                            line_layer = base_chart.mark_line(color="#2B6CB0", strokeWidth=3.5, interpolate="monotone").encode(
                                y=alt.Y('max_heart_rate:Q', title="Max Heart Rate (bpm)", scale=alt.Scale(zero=False)),
                                tooltip=shared_tooltips
                            )

                            # 4. Point Overlay on top of Line to make hover targets easier to hit
                            point_layer = base_chart.mark_point(color="#2B6CB0", size=60, filled=True).encode(
                                y=alt.Y('max_heart_rate:Q'),
                                tooltip=shared_tooltips
                            )

                            # 5. Layer them together and resolve independent independent Y-axes
                            combo_chart = alt.layer(
                                bar_layer, line_layer, point_layer
                            ).resolve_scale(
                                y='independent'
                            ).properties(height=340)
                            
                            # Render combo chart fresh
                            st.altair_chart(combo_chart, theme=None, key=f"split_chart_refresh_id_{run_idx}_v3")
                            
                        except Exception as e:
                            st.error(f"❌ Chart Processing Error: {str(e)}")

                    # Metric visualization metrics blocks (Moved inside loop)
                    st.metric(f"Activity #{run_idx + 1} Distance", f"{matched_run['Display_Distance']:.2f} {unit_abbr}")
                    st.metric(f"Activity #{run_idx + 1} Duration", matched_run.get('Duration', 'N/A'))
                    if run_elevation > 0:
                        st.metric(f"Activity #{run_idx + 1} Elevation Gain", f"{run_elevation:,.0f} ft") 
                    
                    # ------------------------------------------------------------------
                    # 💓 DYNAMIC AVERAGE HEART RATE INDICATOR
                    # ------------------------------------------------------------------
                    avg_hr_val = matched_run.get("average_heart_rate") or matched_run.get("avg_heart_rate")
                    splits_list = matched_run.get("splits", [])
                    
                    if not avg_hr_val and isinstance(splits_list, list) and splits_list:
                        valid_lap_hrs = [
                            float(item.get("average_heart_rate", item.get("avg_heart_rate", 0)))
                            for item in splits_list 
                            if isinstance(item, dict) and (item.get("average_heart_rate") or item.get("avg_heart_rate"))
                        ]
                        if valid_lap_hrs:
                            avg_hr_val = sum(valid_lap_hrs) / len(valid_lap_hrs)

                    if avg_hr_val:
                        try:
                            avg_hr_int = int(round(float(avg_hr_val)))
                            bg_color, zone_lbl, text_color = get_hr_zone_style(avg_hr_int)
                            
                            hr_html = (
                                f'<div style="background-color:{bg_color}; color:{text_color}; '
                                f'padding:6px 12px; border-radius:8px; font-weight:bold; '
                                f'font-size:14px; display:inline-block; margin-top:8px; margin-bottom:12px; '
                                f'border: 1px solid rgba(0,0,0,0.1);">'
                                f'💓 Overall Avg HR: {avg_hr_int} bpm — {zone_lbl}'
                                f'</div>'
                            )
                            st.markdown(hr_html, unsafe_allow_html=True)
                        except Exception:
                            st.caption(f"💓 Overall Avg HR: {int(round(float(avg_hr_val)))} bpm")
                                            
                    try:                        
                        if matched_run:
                            show_run_lap_breakdown(matched_run, unit_abbr=unit_abbr)
                            render_zone_octagon_display(matched_run)
                                        
                    except Exception:       
                        pass





                if 'pace' in matched_run:
                    flat_pace = pace_str_to_minutes(matched_run['pace'])
                    st.metric("Flat Overall Pace", f"{matched_run['pace']} min/{unit_abbr.lower()}")
                    
                    # Grade Adjusted Pace (GAP) calculation output
                    gap_pace = calculate_grade_adjusted_pace(flat_pace, run_elevation, matched_run['Display_Distance'])
                    st.metric("🔋 Grade-Adjusted Pace (GAP)", f"{minutes_to_pace_str(gap_pace)} min/{unit_abbr.lower()}", delta=f"{run_elevation:,.0f} ft climbing effort penalty" if run_elevation > 0 else None, delta_color="inverse")

                if run_elevation > 0:
                    st.metric("Elevation Gain", f"{run_elevation:,.0f} ft")
            else:
                st.caption("Select a run date inside the grid to load data.")

###    with main_layout_col2:
###        if st.session_state.selected_activity_date:
###            active_date = st.session_state.selected_activity_date
###            matched_runs = df[df['Formatted_Date'] == active_date]
###
###            if not matched_runs.empty:
###                st.markdown(f"### 📊 Activity Log Summary: {active_date}")
###
###                # 🏁 Loop opens cleanly
###                for run_idx, (_, run_row_raw) in enumerate(matched_runs.iterrows()):
###                    matched_run = run_row_raw.to_dict()
###
###                    # Create a distinct visual header for multi-activity days
###                    if len(matched_runs) > 1:
###                        st.markdown(f"#### 🏃‍♂️ Workout Activity #{run_idx + 1}")
###                                        
###                    # Single Run Elevation parsing (Moved inside loop)
###                    run_elevation = 0.0     
###                    if elev_columns:        
###                        raw_elev_val = matched_run.get(elev_columns[0], "0")
###                        cleaned_run_elev = ''.join(c for c in str(raw_elev_val) if c.isdigit() or c == '.')
###                        parsed_elev = pd.to_numeric(cleaned_run_elev, errors='coerce')
###                        if pd.notna(parsed_elev): 
###                            run_elevation = parsed_elev
###                                        
###                    if "splits" in matched_run and isinstance(matched_run["splits"], list) and len(matched_run["splits"]) > 0:
###                        splits_df = pd.DataFrame(matched_run["splits"])
###                        splits_df['Split Mile'] = "M" + splits_df['split_num'].astype(str)
###                        splits_df['Pace (Minutes)'] = splits_df['pace'].apply(pace_str_to_minutes)
###                                                
###                        st.caption(f"⏱️  Lap Split Profiles - Activity #{run_idx + 1} (Shorter bars are faster)") 
###                        st.bar_chart(data=splits_df, x='Split Mile', y='Pace (Minutes)', width="stretch")
###
###                    # Metric visualization metrics blocks (Moved inside loop)
###                    st.metric(f"Activity #{run_idx + 1} Distance", f"{matched_run['Display_Distance']:.2f} {unit_abbr}")
###                    st.metric(f"Activity #{run_idx + 1} Duration", matched_run.get('Duration', 'N/A'))
###                    if run_elevation > 0:
###                        st.metric(f"Activity #{run_idx + 1} Elevation Gain", f"{run_elevation:,.0f} ft") 
###                                            
###                    # ------------------------------------------------------------------
###                    # LAUNCH THE DYNAMIC LAP BREAKDOWN (Moved inside loop)
###                    # ------------------------------------------------------------------
###                    try:                        
###                        if matched_run:
###                            show_run_lap_breakdown(matched_run, unit_abbr=unit_abbr)
###                            # --------------------------------------------------------------
###                            # LAUNCH THE INTENSITY OCTAGON VISUALIZATION
###                            # --------------------------------------------------------------
###                            render_zone_octagon_display(matched_run)
###                            # --------------------------------------------------------------
###                                        
###                    except Exception:       
###                        pass
###
###
###                if 'pace' in matched_run:
###                    flat_pace = pace_str_to_minutes(matched_run['pace'])
###                    st.metric("Flat Overall Pace", f"{matched_run['pace']} min/{unit_abbr.lower()}")
###                    
###                    # Grade Adjusted Pace (GAP) calculation output
###                    gap_pace = calculate_grade_adjusted_pace(flat_pace, run_elevation, matched_run['Display_Distance'])
###                    st.metric("🔋 Grade-Adjusted Pace (GAP)", f"{minutes_to_pace_str(gap_pace)} min/{unit_abbr.lower()}", delta=f"{run_elevation:,.0f} ft climbing effort penalty" if run_elevation > 0 else None, delta_color="inverse")
###
###                if run_elevation > 0:
###                    st.metric("Elevation Gain", f"{run_elevation:,.0f} ft")
###            else:
###                st.caption("Select a run date inside the grid to load data.")













            
            if st.button("↩️ Close & View Radar Profile"):
                st.session_state.selected_activity_date = None
                st.rerun()
        else:
            # ==========================================
            # UPGRADE 3: REAL-TIME OVERALL ANALYSIS & RADAR VISUALS
            # ==========================================
            st.markdown("### 🧬 Performance Analytics Panel")
            
            if not target_df.empty:
                avg_dist = target_df['Display_Distance'].mean()
                pace_mins = target_df['pace'].apply(pace_str_to_minutes)
                avg_pace = pace_mins[pace_mins > 0].mean() if not pace_mins[pace_mins > 0].empty else 0.0
                
                avg_elev = 0.0
                if elev_columns:
                    c_elev = target_df[elev_columns[0]].astype(str).str.replace(r'[^\d.]', '', regex=True)
                    avg_elev = pd.to_numeric(c_elev, errors='coerce').fillna(0).mean()
                
                # Dynamic mapping profile logic for the polar radar nonagon
                endurance_score = 3 if avg_dist >= 8.0 else (2 if avg_dist >= 4.0 else 1)
                pace_score = 3 if (0 < avg_pace <= 7.75) else (2 if (7.75 < avg_pace <= 9.75) else 1)
                hill_score = 3 if avg_elev >= 250.0 else (2 if avg_elev >= 75.0 else 1)
                
                st.write("✨ **Progression Radar Athlete Matrix Profile**")
                # FIXED: Pull the dynamically calculated trend levels straight from the active player state
                # FIXED: Checks every potential attribute naming variation to ensure your real values are captured
                current_endurance = getattr(player, 'fuel_level', getattr(player, 'endurance_level', 1))
                current_pace      = getattr(player, 'nitro_level', getattr(player, 'pace_level', 1))
                current_hill      = getattr(player, 'torque_level', getattr(player, 'hill_level', 1))
               
                # Generate the graphic using the verified values
                fig = render_progression_nonagon(
                    endurance_lvl=current_endurance,
                    pace_lvl=current_pace,
                    hill_lvl=current_hill
                )
                


                nonagon_fig = render_progression_nonagon(endurance_score, pace_score, hill_score)
                st.pyplot(nonagon_fig)
            else:
                st.caption("No dynamic metrics data available to compile radar metrics.")
            
            # 10% Training Injury Spike Watchdog Alert Panel
            st.write("---")
            st.markdown("### ⚠️ Training Volume Monitor")
            spikes = analyze_weekly_mileage_spikes(df, cal_year)
            if spikes:
                st.error(f"🚨 Workload Increase Flags detected for {cal_year}!")
                for s in spikes[-2:]: # Show most recent 2 warnings
                    st.warning(f"**Week {s['week']}:** Mileage jumped from {s['prev_val']:.1f} to {s['curr_val']:.1f} {unit_abbr} (+{s['pct']:.1f}% volume spike)")
            else:
                st.success("✅ Consistent structural building. No acute weekly mileage spikes over 10% encountered.")

            # All-Time Hall of Fame Personal Records Panel
            st.write("---")
            st.markdown("### 🏆 All-Time Records PR Vault")
            if not df.empty:
                max_dist_row = df.loc[df['Display_Distance'].idxmax()]
                st.metric("🥇 Longest Distance Record", f"{max_dist_row['Display_Distance']:.2f} {unit_abbr}", f"Achieved on {max_dist_row['Formatted_Date']}")
                
                if elev_columns:
                    all_c_elev = df[elev_columns[0]].astype(str).str.replace(r'[^\d.]', '', regex=True)
                    df['Numeric_Elev'] = pd.to_numeric(all_c_elev, errors='coerce').fillna(0)
                    max_elev_row = df.loc[df['Numeric_Elev'].idxmax()]
                    st.metric("⛰️ King of Mountain Climb", f"{max_elev_row['Numeric_Elev']:,.0f} ft", f"Achieved on {max_elev_row['Formatted_Date']}")





def load_data_from_save_json():
    """
    Directly reads save_file.json and extracts records from the 'history_logs' root key.
    """
    possible_paths = ['save_file.json', '../save_file.json', 'data/save_file.json']
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        if "history_logs" in data:
                            return data["history_logs"]
                        for root_key in data.values():
                            if isinstance(root_key, dict) and "history_logs" in root_key:
                                return root_key["history_logs"]
                    elif isinstance(data, list):
                        return data
            except Exception as e:
                st.error(f"Error reading save_file.json: {e}")
    return []

def pace_str_to_minutes(pace_str):
    """Converts a pace string like '10:36' or a float number into total decimal minutes."""
    if pd.isna(pace_str) or pace_str == "":
        return 0.0
    if isinstance(pace_str, (int, float)):
        return float(pace_str)
    try:
        parts = str(pace_str).strip().split(':')
        if len(parts) == 2:
            return int(parts[0]) + (int(parts[1]) / 60.0)
        return float(pace_str)
    except (ValueError, IndexError):
        return 0.0
def render_dashboard_overview(player):
    """
    Renders an interactive running dashboard featuring:
    - Side-by-side Dual Slider charts (Daily, Monthly, Annual)
    - Miles vs Kilometers unit toggling
    - Custom monthly inline calendar matrix table with selectable activity squares
    """
    import streamlit as st
    import pandas as pd
    # Initialize structural session memory state for layout views if missing
    if "current_dashboard_tab" not in st.session_state:
        st.session_state.current_dashboard_tab = "📅 Training Data Perspectives"
        
    if "selected_activity_date" not in st.session_state:
        st.session_state.selected_activity_date = None

    st.header("🏃‍♂️ Activity Dashboard Overview")
    
    # 1. Gather and sanitize input data log records
    raw_activities = []
    if hasattr(player, 'history_logs') and player.history_logs:
        raw_activities = player.history_logs
    if not raw_activities:
        raw_activities = load_data_from_save_json()

    if isinstance(raw_activities, str):
        try:
            raw_activities = json.loads(raw_activities)
        except Exception:
            raw_activities = []

    if isinstance(raw_activities, list):
        raw_activities = [row for row in raw_activities if isinstance(row, dict)]
    else:
        raw_activities = []

    if not raw_activities:
        st.info("👋 Welcome! No fitness tracking history found in your save file.")
        st.markdown("Please head over to the **Upload UI** page to import your Garmin data files.")
        return

    # 2. Build Core DataFrame and Parse explicit Datetime Columns
    df = pd.DataFrame(raw_activities)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df['Distance (Miles)'] = pd.to_numeric(df['Distance (Miles)'], errors='coerce').fillna(0)
    df = df.dropna(subset=['Date']).sort_values('Date')
    
    # Extract time dimensions for groupings and labels
    df['Year'] = df['Date'].dt.year.astype(str)
    df['Month_Period'] = df['Date'].dt.to_period('M')  
    df['Month_Label'] = df['Date'].dt.strftime('%b %Y')  
    df['Formatted_Date'] = df['Date'].dt.strftime('%Y-%m-%d')

    # ==========================================
    # UNIT CONVERSION SETTINGS (MILES ⇄ KM)
    # ==========================================
    st.subheader("🎛️ Unit & Filter Configuration")
    config_col1, config_col2 = st.columns(2)
    
    #with config_col2:
    #    unit_system = st.selectbox(
    #        label="🔄 Select System Unit:",
    #        options=["Miles (mi)", "Kilometers (km)"],
    #        index=0
    #    )
    
    # Conversion multiplier variables
    is_km = False
    unit_abbr = "Mi"
    df['Display_Distance'] = df['Distance (Miles)'] * 1.0
    with config_col1:
        unique_years = sorted(df['Year'].unique(), reverse=True)
        selected_year = st.radio(
            label="Select Tracking Year to Filter Below Trends:",
            options=["All Years"] + unique_years,
            index=0,
            horizontal=True
        )

    # Apply Year Radio filters to the DataFrame segment
    if selected_year != "All Years":
        filtered_df = df[df['Year'] == selected_year].reset_index(drop=True)
    else:
        filtered_df = df.reset_index(drop=True)

    st.write("---")

    # ==========================================
    # LAYOUT ENGINE: 3-COLUMN CHART ROW
    # ==========================================
    col1, col2, col3 = st.columns(3)


    # ==============================================================================
    # 🎨 GLOBAL MASTER COLOR REGISTRY (PLACE DIRECTLY ABOVE st.columns(3))
    # ==============================================================================
    
    # 1. Establish your curated fixed palette array once at the top
    racing_colors = ['#3b82f6', '#22c55e', '#f59e0b', '#f43f5e', '#a855f7']
    
    # 2. Extract and sort every available unique year dynamically from the active data
    if 'filtered_df' in locals() and not filtered_df.empty:
        master_years_source = filtered_df
    elif 'df' in locals() and not df.empty:
        master_years_source = df
    else:
        master_years_source = pd.DataFrame({'Year': [2022, 2023, 2024, 2025, 2026]})
    
    global_sorted_years = sorted(master_years_source['Year'].dropna().astype(str).unique().tolist())
    
    # 3. Build the global map using a cyclic index % pattern to prevent out-of-range errors
    global_year_color_map = {
        yr: racing_colors[idx % len(racing_colors)] 
        for idx, yr in enumerate(global_sorted_years)
    }
    
    # 4. Provide a reliable default color code fallback for unmapped variables
    default_fallback_color = racing_colors[0]




    # ==============================================================================
    # 🏃 COLUMN 1: WEEKLY TOTALS TRAINING METRICS & CHRONOLOGICAL OVERVIEW
    # ==============================================================================
    st.markdown("""
            <style>
                div[data-testid="stMetricValue"] > div { font-size: 1.15rem !important; font-weight: 700; }
                div[data-testid="stMetricLabel"] > div { font-size: 0.75rem !important; opacity: 0.85; }
            </style>
        """, unsafe_allow_html=True)




#COL1
    # ==============================================================================
    # 📊 COLUMN 1: PART 1 - BASE HEADER AND WEEK SLIDER SETUP
    # ==============================================================================
    with col1:
        st.markdown("<h3 style='margin:0 0 2px 0; padding:0; display:inline-block; min-height:32px;'>📊 Weekly Stats</h3>", unsafe_allow_html=True)

        import altair as alt

        # 1. Base 53-week layout template skeleton tracking 
        standard_weeks = pd.DataFrame({
            'Week_Period': list(range(1, 54)),
            'Week_Label': [f"Wk {w}" for w in range(1, 54)]
        })

        # 2. Interactive Week Filter Slider
        week_range = st.slider(
            label="📊 Filter Workout Week Range",
            min_value=1,
            max_value=53,
            value=(1, 26),
            step=1,
            key="col1_week_slider_unique_final"
        )
        start_week, end_week = week_range
        # ==============================================================================
        # 📊 COLUMN 1: PART 2 - TIMELINE SCAFFOLDING & ALTAIR CHART CANVAS
        # ==============================================================================
        if not filtered_df.empty:
            df_working_col1 = filtered_df.copy()

            # 3. Safe date column discovery loop
            date_col = None
            for col in ['Date', 'Calendar Date', 'Date_Time', 'timestamp']:
                if col in df_working_col1.columns:
                    date_col = col
                    break
            
            if date_col is not None:
                parsed_dates = pd.to_datetime(df_working_col1[date_col], errors='coerce')
                # 🔥 FIXED: Swapped out broken .dt.week attribute for robust .dt.isocalendar().week method
                df_working_col1['Week_Period'] = parsed_dates.dt.isocalendar().week
            
            df_working_col1['Week_Period'] = pd.to_numeric(df_working_col1['Week_Period'], errors='coerce').fillna(1).astype(int)
            df_working_col1['Year_Tag'] = df_working_col1['Year'].astype(str)

            # 4. Group data array bounds by training year and calendar week slots
            weekly_df = df_working_col1.groupby(['Year_Tag', 'Week_Period'])['Display_Distance'].sum().reset_index()
            weekly_df['Week_Period'] = weekly_df['Week_Period'].astype(int)

            # 5. Check if filtering a single distinct year
            is_single_year = False
            if 'Year' in df_working_col1.columns and df_working_col1['Year'].nunique() == 1:
                is_single_year = True
            elif 'year_range_slider' in st.session_state and st.session_state.year_range_slider is not None:
                try:
                    sy, ey = st.session_state.year_range_slider
                    if sy == ey:
                        is_single_year = True
                except Exception:
                    pass

            # 6. Route metrics array into target timeline scaffolds
            if is_single_year:
                # 🎯 FIXED: Appended [0] to execute iloc and dynamically resolve the calendar year fallback
                import datetime
                fallback_current_year = str(datetime.datetime.now().year)
                single_year_value_col1 = df_working_col1['Year_Tag'].iloc[0] if not df_working_col1.empty else fallback_current_year
                
                weekly_plot_df = pd.merge(standard_weeks, weekly_df, on='Week_Period', how='left')
                weekly_plot_df['Display_Distance'] = weekly_plot_df['Display_Distance'].fillna(0.0)
                weekly_plot_df['Year_Tag'] = weekly_plot_df['Year_Tag'].fillna(single_year_value_col1)
            else:
                active_years = pd.DataFrame({'Year_Tag': sorted(weekly_df['Year_Tag'].unique().tolist())})
                scaffold_3d = standard_weeks.merge(active_years, how='cross')
                weekly_plot_df = pd.merge(scaffold_3d, weekly_df, on=['Week_Period', 'Year_Tag'], how='left')
                weekly_plot_df['Display_Distance'] = weekly_plot_df['Display_Distance'].fillna(0.0)

            # 7. Filter rows strictly by slider windows
            weekly_plot_df = weekly_plot_df[
                (weekly_plot_df['Week_Period'] >= start_week) & 
                (weekly_plot_df['Week_Period'] <= end_week)
            ].copy()

            weekly_plot_df = weekly_plot_df.sort_values(['Week_Period', 'Year_Tag']).reset_index(drop=True)

            # 8. ROW DISPLAY CAP ENGINE: Prevents wide layouts from drifting out of layout containers
            total_rendered_weeks = len(weekly_plot_df)
            is_capped_weeks = False
            if total_rendered_weeks > 14:
                weekly_plot_df = weekly_plot_df.head(14).copy()
                total_rendered_weeks = 14
                is_capped_weeks = True

            # 9. GLOBAL COLOR CONSUMER ENGINE (Matches Column 2 and Column 3 exactly)
            active_years_list = sorted(weekly_plot_df['Year_Tag'].unique().tolist())
            unique_years_count = len(active_years_list)
            
            if unique_years_count > 1:
                extended_range = [global_year_color_map.get(yr, default_fallback_color) for yr in active_years_list]
                color_encoding = alt.Color(
                    'Year_Tag:N',
                    scale=alt.Scale(domain=active_years_list, range=extended_range),
                    legend=alt.Legend(title="📅 Training Year", orient="top", labelFontSize=9, titleFontSize=9)
                )
                
                x_axis_config = alt.X('Year_Tag:N', title='', axis=alt.Axis(labels=False, ticks=False))
                facet_config = alt.Column(
                    'Week_Label:N', 
                    title='Calendar Week Index', 
                    sort=standard_weeks['Week_Label'].tolist(),
                    header=alt.Header(labelOrient='bottom', titleOrient='bottom', labelFontSize=9, titleFontSize=9)
                )
                calculated_step = max(20, min(65, int(430 / max(1, total_rendered_weeks))))
                chart_width_property = alt.Step(calculated_step)
            else:
                # Extract the first string element from the list to avoid unhashable type errors
                selected_year = active_years_list[0] if len(active_years_list) > 0 else "2026"
                matched_annual_color = global_year_color_map.get(selected_year, default_fallback_color)
    
                color_encoding = alt.value(matched_annual_color) 

                x_axis_config = alt.X('Week_Label:N', title='Calendar Week Index', sort=standard_weeks['Week_Label'].tolist(), axis=alt.Axis(labelFontSize=9, titleFontSize=9))
                facet_config = None
                chart_width_property = 'container'

            # 10. Build chart parameters with layout-locked step scaling
            base_chart_col1 = alt.Chart(weekly_plot_df).mark_bar(
                cornerRadiusTopLeft=3,
                cornerRadiusTopRight=3
            ).encode(
                x=x_axis_config,
                y=alt.Y('Display_Distance:Q', title=f'Weekly Distance ({unit_abbr})', axis=alt.Axis(labelFontSize=9, titleFontSize=9)),
                color=color_encoding,
                tooltip=[
                    alt.Tooltip('Year_Tag:N', title='Year'),
                    alt.Tooltip('Week_Label:N', title='Week Block'),
                    alt.Tooltip('Display_Distance:Q', title='Distance Total', format='.1f')
                ]
            ).properties(
                height=220,
                width=chart_width_property 
            )

            if facet_config is not None:
                final_chart_col1 = base_chart_col1.facet(column=facet_config).resolve_scale(
                    x='independent'
                ).configure_view(strokeWidth=0).configure_facet(spacing=4)
            else:
                final_chart_col1 = base_chart_col1.configure_view(strokeWidth=0)

            st.altair_chart(final_chart_col1, theme=None)
            
            #if is_capped_weeks:
                #st.caption("⚠️ *Graph display capped at 14 weeks to match column layout size constraints.*")
        # ==============================================================================
        # 📊 COLUMN 1: PART 3 - WEEK-BY-WEEK LEDGER OUTPUT & STATISTICS
        # ==============================================================================
            st.markdown("<p style='font-size: 0.85rem; font-weight: bold; margin-bottom: 4px;'>📊 Week-by-Week Aggregation Ledger:</p>", unsafe_allow_html=True)
            
            ledger_df_col1 = weekly_plot_df.sort_values(by=['Week_Period', 'Year_Tag']).reset_index(drop=True)
            
            n_rows_col1 = len(ledger_df_col1)
            midpoint_col1 = (n_rows_col1 + 1) // 2
            
            left_df_col1 = ledger_df_col1.iloc[:midpoint_col1]
            right_df_col1 = ledger_df_col1.iloc[midpoint_col1:]
            
            ledger_cols_col1 = st.columns(2)
            
            with ledger_cols_col1[0]:
                for _, row in left_df_col1.iterrows():
                    wk_lookup = standard_weeks[standard_weeks['Week_Period'] == row['Week_Period']]['Week_Label'].values
                    wk_str = wk_lookup if len(wk_lookup) > 0 else "Wk 1"
                    timeline_str = f"{row['Year_Tag']}- {wk_str}"
                    st.markdown(f"<p style='font-size: 0.8rem; margin: 1px 0;'>📊 <b>{timeline_str}</b>: {row['Display_Distance']:,.1f} {unit_abbr}</p>", unsafe_allow_html=True)
            
            with ledger_cols_col1[1]:
                for _, row in right_df_col1.iterrows():
                    wk_lookup = standard_weeks[standard_weeks['Week_Period'] == row['Week_Period']]['Week_Label'].values
                    wk_str = wk_lookup if len(wk_lookup) > 0 else "Wk 1"
                    timeline_str = f"{row['Year_Tag']}- {wk_str}"
                    st.markdown(f"<p style='font-size: 0.8rem; margin: 1px 0;'>📊 <b>{timeline_str}</b>: {row['Display_Distance']:,.1f} {unit_abbr}</p>", unsafe_allow_html=True)
                
            st.markdown("<hr style='margin: 8px 0; opacity: 0.2;'/>", unsafe_allow_html=True)
            
            # Dynamic metric summary card
            visible_sum_col1 = weekly_plot_df['Display_Distance'].sum()
            st.metric(
                label=f"Weekly Segment Total ({unit_abbr})", 
                value=f"{visible_sum_col1:,.1f} {unit_abbr}"
            )
        else:
            # Fallback frame for blank conditions
            standard_weeks['Display_Distance'] = 0.0
            empty_plot_df_col1 = standard_weeks[
                (standard_weeks['Week_Period'] >= start_week) & 
                (standard_weeks['Week_Period'] <= end_week)
            ]
            
            empty_chart_col1 = alt.Chart(empty_plot_df_col1).mark_bar(color='#3b82f6').encode(
                x=alt.X('Week_Label:N', title='Calendar Week Index', sort=standard_weeks['Week_Label'].tolist(), axis=alt.Axis(labelFontSize=9, titleFontSize=9)),
                y=alt.Y('Display_Distance:Q', title=f'Weekly Distance ({unit_abbr})', axis=alt.Axis(labelFontSize=9, titleFontSize=9))
            ).properties(height=240, width='container').configure_view(strokeWidth=0)
            
            st.altair_chart(empty_chart_col1, theme=None)
            st.metric(label=f"Weekly Segment Total ({unit_abbr})", value=f"0.0 {unit_abbr}")



















#COL2
    # ==============================================================================
    # 📅 COLUMN 2: PART 1 - BASE HEADER AND SLIDER SETUP
    # ==============================================================================
    with col2:
        st.markdown("<h3 style='margin:0 0 2px 0; padding:0; display:inline-block; min-height:32px;'>📅 Monthly Trends</h3>", unsafe_allow_html=True)

        import altair as alt

        # Base 12-month calendar template framework
        standard_months = pd.DataFrame({
            'Month_Period': list(range(1, 13)),
            'Month_Label': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        })

        # Interactive Month Filter Slider
        month_range = st.slider(
            label="📅 Filter Workout Month Range",
            min_value=1,
            max_value=12,
            value=(1, 12),
            step=1,
            key="col2_month_slider_unique_final"
        )
        start_month, end_month = month_range
        # ==============================================================================
        # 📅 COLUMN 2: PART 2 - DATAFRAME HANDLING & DYNAMIC ALTAIR BAR CANVAS
        # ==============================================================================
        if not filtered_df.empty:
            df_working = filtered_df.copy()

            # Parse the true month from raw activity dates safely
            date_col = None
            for col in ['Date', 'Calendar Date', 'Date_Time', 'timestamp']:
                if col in df_working.columns:
                    date_col = col
                    break
            
            if date_col is not None:
                parsed_dates = pd.to_datetime(df_working[date_col], errors='coerce')
                df_working['Month_Period'] = parsed_dates.dt.month
            
            df_working['Month_Period'] = pd.to_numeric(df_working['Month_Period'], errors='coerce').fillna(1).astype(int)
            df_working['Year_Tag'] = df_working['Year'].astype(str)

            # Group and sum by BOTH Year and Month to prevent data flattening
            monthly_df = df_working.groupby(['Year_Tag', 'Month_Period'])['Display_Distance'].sum().reset_index()
            monthly_df['Month_Period'] = monthly_df['Month_Period'].astype(int)

            # Check if filtering a single distinct year
            is_single_year = False
            if 'Year' in df_working.columns and df_working['Year'].nunique() == 1:
                is_single_year = True
            elif 'year_range_slider' in st.session_state and st.session_state.year_range_slider is not None:
                try:
                    sy, ey = st.session_state.year_range_slider
                    if sy == ey:
                        is_single_year = True
                except Exception:
                    pass

            # Route data into full calendar layout scaffold
            if is_single_year:
                single_year_value = df_working['Year_Tag'].iloc[0] if not df_working.empty else "2026"
                monthly_plot_df = pd.merge(standard_months, monthly_df, on='Month_Period', how='left')
                monthly_plot_df['Display_Distance'] = monthly_plot_df['Display_Distance'].fillna(0.0)
                monthly_plot_df['Year_Tag'] = monthly_plot_df['Year_Tag'].fillna(single_year_value)
            else:
                active_years = pd.DataFrame({'Year_Tag': sorted(monthly_df['Year_Tag'].unique().tolist())})
                scaffold_3d = standard_months.merge(active_years, how='cross')
                monthly_plot_df = pd.merge(scaffold_3d, monthly_df, on=['Month_Period', 'Year_Tag'], how='left')
                monthly_plot_df['Display_Distance'] = monthly_plot_df['Display_Distance'].fillna(0.0)

            # Apply month slider bounds
            monthly_plot_df = monthly_plot_df[
                (monthly_plot_df['Month_Period'] >= start_month) & 
                (monthly_plot_df['Month_Period'] <= end_month)
            ].copy()

            monthly_plot_df = monthly_plot_df.sort_values(['Month_Period', 'Year_Tag']).reset_index(drop=True)

            # Caps chart display count at 14 segments to keep width locked inside columns
            total_rendered_bars = len(monthly_plot_df)
            is_capped = False
            if total_rendered_bars > 14:
                monthly_plot_df = monthly_plot_df.head(14).copy()
                total_rendered_bars = 14
                is_capped = True

            # 🏆 RE-ENGINEERED PALETTE MATCHING ENGINE (Consumes your top-level global registry map)
            active_years_list = sorted(monthly_plot_df['Year_Tag'].unique().tolist())
            unique_years_count = len(active_years_list)
            
            if unique_years_count > 1:
                extended_range = [global_year_color_map.get(yr, default_fallback_color) for yr in active_years_list]
                color_encoding = alt.Color(
                    'Year_Tag:N',
                    scale=alt.Scale(domain=active_years_list, range=extended_range),
                    legend=alt.Legend(title="📅 Training Year", orient="top", labelFontSize=9, titleFontSize=9)
                )
                
                x_axis_config = alt.X('Year_Tag:N', title='', axis=alt.Axis(labels=False, ticks=False))
                facet_config = alt.Column(
                    'Month_Label:N', 
                    title='Calendar Month', 
                    sort=standard_months['Month_Label'].tolist(),
                    header=alt.Header(labelOrient='bottom', titleOrient='bottom', labelFontSize=9, titleFontSize=9)
                )
                calculated_step = max(20, min(65, int(430 / max(1, total_rendered_bars))))
                chart_width_property = alt.Step(calculated_step)
            else:
                # Extract the first string element from the list to avoid unhashable type errors
                selected_year = active_years_list[0] if len(active_years_list) > 0 else "2026"
                matched_annual_color = global_year_color_map.get(selected_year, default_fallback_color)
                
                color_encoding = alt.value(matched_annual_color) 

                x_axis_config = alt.X('Month_Label:N', title='Calendar Month', sort=standard_months['Month_Label'].tolist(), axis=alt.Axis(labelFontSize=9, titleFontSize=9))
                facet_config = None
                chart_width_property = 'container'

            # Build chart parameters with layout-locked step scaling
            base_chart = alt.Chart(monthly_plot_df).mark_bar(
                cornerRadiusTopLeft=3,
                cornerRadiusTopRight=3
            ).encode(
                x=x_axis_config,
                y=alt.Y('Display_Distance:Q', title=f'Total Distance ({unit_abbr})', axis=alt.Axis(labelFontSize=9, titleFontSize=9)),
                color=color_encoding,
                tooltip=[
                    alt.Tooltip('Year_Tag:N', title='Year'),
                    alt.Tooltip('Month_Label:N', title='Month'),
                    alt.Tooltip('Display_Distance:Q', title='Distance', format='.1f')
                ]
            ).properties(
                height=220,
                width=chart_width_property 
            )

            if facet_config is not None:
                final_chart = base_chart.facet(column=facet_config).resolve_scale(
                    x='independent'
                ).configure_view(strokeWidth=0).configure_facet(spacing=4)
            else:
                final_chart = base_chart.configure_view(strokeWidth=0)

            st.altair_chart(final_chart, theme=None)
            
            #if is_capped:
                #st.caption("⚠️ *Graph display capped at 14 bars to fit your screen. Use the slider above to see other months.*")
        # ==============================================================================
        # 📅 COLUMN 2: PART 3 - MONTH-GROUPED LEDGER OUTPUT & TRAILING STATISTICS
        # ==============================================================================
            st.markdown("<p style='font-size: 0.85rem; font-weight: bold; margin-bottom: 4px;'>📊 Sequential Month-by-Month Log:</p>", unsafe_allow_html=True)
            
            ledger_df = monthly_plot_df.sort_values(by=['Month_Period', 'Year_Tag']).reset_index(drop=True)
            
            n_rows = len(ledger_df)
            midpoint = (n_rows + 1) // 2
            
            left_df = ledger_df.iloc[:midpoint]
            right_df = ledger_df.iloc[midpoint:]
            
            ledger_cols = st.columns(2)
            
            with ledger_cols[0]:
                for _, row in left_df.iterrows():
                    month_lookup = standard_months[standard_months['Month_Period'] == row['Month_Period']]['Month_Label'].values
                    month_str = month_lookup[0] if len(month_lookup) > 0 else "Jan"
                    timeline_str = f"{row['Year_Tag']}- {month_str}"
                    st.markdown(f"<p style='font-size: 0.8rem; margin: 1px 0;'>📅 <b>{timeline_str}</b>: {row['Display_Distance']:,.1f} {unit_abbr}</p>", unsafe_allow_html=True)
            
            with ledger_cols[1]:
                for _, row in right_df.iterrows():
                    month_lookup = standard_months[standard_months['Month_Period'] == row['Month_Period']]['Month_Label'].values
                    month_str = month_lookup[0] if len(month_lookup) > 0 else "Jan"
                    timeline_str = f"{row['Year_Tag']}- {month_str}"
                    st.markdown(f"<p style='font-size: 0.8rem; margin: 1px 0;'>📅 <b>{timeline_str}</b>: {row['Display_Distance']:,.1f} {unit_abbr}</p>", unsafe_allow_html=True)
                
            st.markdown("<hr style='margin: 8px 0; opacity: 0.2;'/>", unsafe_allow_html=True)
            
            visible_sum = monthly_plot_df['Display_Distance'].sum()
            st.metric(
                label=f"Monthly Segment Total ({unit_abbr})", 
                value=f"{visible_sum:,.1f} {unit_abbr}"
            )
        else:
            # Fallback for empty frames
            standard_months['Display_Distance'] = 0.0
            empty_plot_df = standard_months[
                (standard_months['Month_Period'] >= start_month) & 
                (standard_months['Month_Period'] <= end_month)
            ]
            
            empty_chart = alt.Chart(empty_plot_df).mark_bar(color='#22c55e').encode(
                x=alt.X('Month_Label:N', title='Calendar Month', sort=standard_months['Month_Label'].tolist(), axis=alt.Axis(labelFontSize=9, titleFontSize=9)),
                y=alt.Y('Display_Distance:Q', title=f'Total Distance ({unit_abbr})', axis=alt.Axis(labelFontSize=9, titleFontSize=9))
            ).properties(height=240, width='container').configure_view(strokeWidth=0)
            
            st.altair_chart(empty_chart, theme=None)
            st.metric(label=f"Monthly Segment Total ({unit_abbr})", value=f"0.0 {unit_abbr}")





#Col3
    # ==============================================================================
    # 🏆 COLUMN 3: ANNUAL PANEL (SCALE BALANCED FOR 100% VISUAL ALIGNMENT)
    # ==============================================================================
    with col3:
        st.markdown("<h3 style='margin:0 0 2px 0; padding:0; display:inline-block; min-height:32px;'>🏆 Annual Totals</h3>", unsafe_allow_html=True)

        import altair as alt

        # 1. ALWAYS build a static backbone containing every unique year from your registry
        available_registry_years = sorted([int(yr) for yr in global_year_color_map.keys()])
        scaffold_all_years = pd.DataFrame({'Year_Tag': [str(yr) for yr in available_registry_years]})

        # 2. INTERACTIVE YEAR RANGE SLIDER FRAMEWORK
        if len(available_registry_years) > 1:
            min_year_val = min(available_registry_years)
            max_year_val = max(available_registry_years)
            
            selected_year_bounds = st.slider(
                label="🏆 Filter Workout Year Range",
                min_value=min_year_val,
                max_value=max_year_val,
                value=(min_year_val, max_year_val),
                step=1,
                key="col3_year_slider_range_final"
            )
            start_year_filter, end_year_filter = selected_year_bounds
        else:
            start_year_filter = available_registry_years if available_registry_years else 2026
            end_year_filter = start_year_filter

        # 3. Extract and sum distance fields based strictly on active global filters
        if not filtered_df.empty:
            df_working_col3 = filtered_df.copy()
            df_working_col3['Year_Tag'] = df_working_col3['Year'].astype(str)
            annual_filtered_sums = df_working_col3.groupby('Year_Tag')['Display_Distance'].sum().reset_index()
            
            # Left-merge to keep all years mapped out initially
            annual_df = pd.merge(scaffold_all_years, annual_filtered_sums, on='Year_Tag', how='left')
            annual_df['Display_Distance'] = annual_df['Display_Distance'].fillna(0.0)
        else:
            annual_df = scaffold_all_years.copy()
            annual_df['Display_Distance'] = 0.0

        # Create numerical year helper column for processing
        annual_df['Year_Int'] = annual_df['Year_Tag'].astype(int)
        
        # Drop rows completely to force Altair to rewrite the X-axis labels automatically
        annual_df = annual_df[
            (annual_df['Year_Int'] >= start_year_filter) & 
            (annual_df['Year_Int'] <= end_year_filter)
        ].copy()

        annual_df = annual_df.sort_values('Year_Tag').reset_index(drop=True)

        # 4. Extract axis categories to pull synchronized keys from your master registry
        active_years_col3 = sorted(annual_df['Year_Tag'].unique().tolist())
        extended_range_col3 = [global_year_color_map.get(yr, default_fallback_color) for yr in active_years_col3]
        
        # Invisible legend block with empty title matching Col 1 and 2 bounding height
        color_encoding_col3 = alt.Color(
            'Year_Tag:N',
            scale=alt.Scale(domain=active_years_col3, range=extended_range_col3),
            legend=alt.Legend(
                title="", 
                orient="top", 
                labelExpr="''", 
                symbolType='square',
                symbolSize=0,
                labelFontSize=0,
                titleFontSize=0
            )
        )

        # 5. Build the annual summary bar chart
        # 🔥 EXTENDED HEIGHT TO 255: This compensates for the facet height additions in Col 2
        annual_chart = alt.Chart(annual_df).mark_bar(
            cornerRadiusTopLeft=3,
            cornerRadiusTopRight=3
        ).encode(
            x=alt.X('Year_Tag:N', title='Training Year', axis=alt.Axis(labelFontSize=9, titleFontSize=9, labelAngle=0)),
            y=alt.Y('Display_Distance:Q', title=f'Total Distance ({unit_abbr})', axis=alt.Axis(labelFontSize=9, titleFontSize=9)),
            color=color_encoding_col3,
            tooltip=[
                alt.Tooltip('Year_Tag:N', title='Year'),
                alt.Tooltip('Display_Distance:Q', title='Total Distance', format='.1f')
            ]
        ).properties(
            height=350,  # 🔥 Fixed: Scale extended to match outer facet size boundaries
            width='container'
        ).configure_view(
            strokeWidth=0
        )

        st.altair_chart(annual_chart, theme=None)

        # 6. LEDGER BREAKDOWNS & HISTORICAL METRICS
        st.markdown("<p style='font-size: 0.85rem; font-weight: bold; margin-bottom: 4px;'>🏆 Year-by-Year Log Summary:</p>", unsafe_allow_html=True)
        
        for _, row in annual_df.iterrows():
            st.markdown(f"<p style='font-size: 0.8rem; margin: 1px 0;'>🏆 <b>Year {row['Year_Tag']}</b>: {row['Display_Distance']:,.1f} {unit_abbr}</p>", unsafe_allow_html=True)
            
        st.markdown("<hr style='margin: 8px 0; opacity: 0.2;'/>", unsafe_allow_html=True)
        
        # Print total distance sum accumulating inside current slider scope
        total_dashboard_distance = annual_df['Display_Distance'].sum()
        st.metric(
            label=f"All-Time Training Total ({unit_abbr})", 
            value=f"{total_dashboard_distance:,.1f} {unit_abbr}"
        )




















# ==============================================================================
# EXTENSION: ADVANCED DYNAMIC LAP SPLIT PROFILER (REAL DATA SPLITS)
# ==============================================================================
def show_run_lap_breakdown(matched_run_dict, unit_abbr="Mi"):
    """
    Extracts real mile-by-mile split records from the activity logs to generate
    authentic color-gradient variations, cumulative charts, and lap heart rates.
    Renders an HTML matrix where both the Avg HR cells and the Speed Metric bars
    automatically match the color signature of their target training intensity zones.
    """
    import pandas as pd
    import streamlit as st
    
    st.markdown("---")
    st.markdown("#### ⏱️  1-Mile Split & Performance Analysis")
                        
    if not matched_run_dict:
        st.info("Select an active run day to view performance split curves.")
        return

    raw_splits = matched_run_dict.get("splits", [])
    lap_records = []
    cumulative_seconds = 0.0
    
            
    # CASE 1: If real nested splits exist, parse their actual varied pacing records

    if isinstance(raw_splits, list) and len(raw_splits) > 0:
        total_activity_distance = float(matched_run_dict.get('Display_Distance', 0.0))

        for idx, split_item in enumerate(raw_splits):
            lap_idx = split_item.get("split_num", idx + 1)
            is_last_row = (idx == len(raw_splits) - 1)

            # 🚨 FIXED DISTANCE PARSING: Prioritize the explicit distance parameters from the split log itself
            raw_lap_dist = split_item.get("distance_mi") or split_item.get("distance")
            try:
                lap_dist = float(raw_lap_dist) if raw_lap_dist is not None else 1.0
            except Exception:
                lap_dist = 1.0

            pace_str = str(split_item.get("pace", "08:00"))

            try:
                parts = pace_str.strip().split(':')
                if len(parts) == 3:   # HH:MM:SS
                    lap_pace_secs = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                elif len(parts) == 2: # MM:SS
                    lap_pace_secs = int(parts[0]) * 60 + int(parts[1])
                else:
                    lap_pace_secs = float(pace_str) * 60
            except Exception:
                lap_pace_secs = 480.0

            # 🚨 REMOVED BREAKING FIX 1: Rely entirely on the actual recorded lap intervals rather than truncating math

            # Calculate this split's actual elapsed duration based on its real distance
            lap_seconds = lap_dist * lap_pace_secs
            cumulative_seconds += lap_seconds

            lap_avg_hr = split_item.get("average_heart_rate") or split_item.get("avg_heart_rate")
            hr_display_str = f"{int(lap_avg_hr)} bpm" if lap_avg_hr else "—"

            lap_pace_mins = lap_pace_secs / 60.0
            lap_speed = 60.0 / lap_pace_mins if lap_pace_mins > 0 else 0.0

            def format_cumulative_clock(total_secs):
                total_secs_rounded = int(round(total_secs))
                hrs = total_secs_rounded // 3600
                mins = (total_secs_rounded % 3600) // 60
                secs = total_secs_rounded % 60
                return f"{hrs:02d}:{mins:02d}:{secs:02d}" if hrs > 0 else f"{mins:02d}:{secs:02d}"

            # 🚨 FIXED LABELING CLEANUP: Generically flag intervals cleanly as 'Split X'
            split_title = f"Split {lap_idx}"
            if is_last_row and lap_dist != 1.0:
                split_title += f" ({lap_dist:.2f} {unit_abbr.lower()} Final)"

            lap_records.append({
                "Split": split_title,
                "Distance": f"{lap_dist:.2f} {unit_abbr.lower()}", # Displays your true dynamic distance
                "Pace": pace_str,
                "Avg HR (bpm)": hr_display_str,
                "Total Time": format_cumulative_clock(cumulative_seconds),
                "Cumulative Minutes": cumulative_seconds / 60.0,
                "Speed Metric": lap_speed
            })

    # CASE 2: Fallback to simulated intervals if activity contains no sub-split logs
    else:
        try:
            run_distance = float(matched_run_dict.get('Display_Distance', 0.0))
            average_pace_str = matched_run_dict.get('pace', '08:00')
            
            parts = str(average_pace_str).strip().split(':')
            base_secs = int(parts[0]) * 60 + int(parts[1]) if len(parts) == 2 else 480.0
            
            remaining_dist = run_distance
            sim_lap_idx = 1
            while remaining_dist > 0:
                current_lap_dist = 1.0 if remaining_dist >= 1.0 else remaining_dist
                remaining_dist -= current_lap_dist
                
                variance_multiplier = 0.96 + (sim_lap_idx * 0.02) if run_distance > 1 else 1.0
                lap_pace_secs = base_secs * variance_multiplier
                lap_seconds = current_lap_dist * lap_pace_secs
                cumulative_seconds += lap_seconds
                split_mins = int(lap_pace_secs) // 60
                split_secs = int(round(lap_pace_secs % 60))
                if split_secs == 60: split_mins += 1; split_secs = 0
                
                split_mins_float = lap_pace_secs / 60.0
                lap_speed = 60.0 / split_mins_float if split_mins_float > 0 else 0.0

                lap_records.append({
                    "Split": f"Mile {sim_lap_idx}" if current_lap_dist == 1.0 else f"Mile {sim_lap_idx} (Final)",
                    "Distance": f"{current_lap_dist:.2f} {unit_abbr.lower()}",
                    "Pace": f"{split_mins:02d}:{split_secs:02d}",
                    "Avg HR (bpm)": "—",
                    "Total Time": f"{int(cumulative_seconds)//3600:02d}:{int(cumulative_seconds%3600)//60:02d}:{int(cumulative_seconds%60):02d}" if cumulative_seconds >= 3600 else f"{int(cumulative_seconds)//60:02d}:{int(cumulative_seconds%60):02d}",
                    "Cumulative Minutes": cumulative_seconds / 60.0,
                    "Speed Metric": lap_speed
                })
                sim_lap_idx += 1
        except Exception:
            pass

    if not lap_records:
        st.info("No numerical split vectors available to process.")
        return

    df_splits = pd.DataFrame(lap_records)
    st.caption("🟢 Performance Summary Matrix: Split data segments compiled with synchronized metabolic formatting handles")

    # =========================================================================
    # 🎨 DYNAMIC STRUCTURED TABLE RENDERING VIA HTML GENERATOR (FIXED INDENTATION)
    # =========================================================================
    max_speed = df_splits["Speed Metric"].max() if not df_splits.empty else 1.0
    speed_unit = "mph" if unit_abbr.lower() == "mi" else "km/h"
    html_rows = []

    for _, row in df_splits.iterrows():
        hr_str = str(row["Avg HR (bpm)"])
        bg_color = "#4A5568"
        text_color = "#FFFFFF"
        zone_lbl = "No Data"
        
        if hr_str and hr_str != "—" and "bpm" in hr_str:
            try:
                hr_val = int(hr_str.split()[0])
                from upload_ui import get_hr_zone_style
                bg_color, zone_lbl, text_color = get_hr_zone_style(hr_val)
            except:
                pass

        speed_val = row["Speed Metric"]
        speed_pct = (speed_val / max_speed) * 100 if max_speed > 0 else 0

        # Constructed via explicit line continuation to guarantee ZERO leading spaces/tabs
        bar_html = f'<div style="display: flex; align-items: center; gap: 8px; width: 100%;">' \
                   f'<div style="flex-grow: 1; background-color: #E2E8F0; border-radius: 4px; height: 12px; overflow: hidden;">' \
                   f'<div style="width: {speed_pct:.1f}%; background-color: {bg_color}; height: 100%; border-radius: 4px;"></div>' \
                   f'</div>' \
                   f'<span style="font-size: 12px; font-weight: bold; min-width: 55px; text-align: left; color: #4A5568;">{speed_val:.1f} {speed_unit}</span>' \
                   f'</div>'

        html_rows.append(f'<tr style="border-bottom: 1px solid #E2E8F0;">' \
                         f'<td style="padding: 10px; border: 1px solid #E2E8F0; font-weight: bold; color: #2D3748;">{row["Split"]}</td>' \
                         f'<td style="padding: 10px; border: 1px solid #E2E8F0; text-align: center; color: #4A5568;">{row["Distance"]}</td>' \
                         f'<td style="padding: 10px; border: 1px solid #E2E8F0; text-align: center; font-family: monospace; font-weight: bold; color: #2D3748;">{row["Pace"]}</td>' \
                         f'<td style="background-color: {bg_color}; color: {text_color}; font-weight: bold; padding: 10px; border: 1px solid #E2E8F0; text-align: center; font-size: 13px;">{hr_str}</td>' \
                         f'<td style="padding: 10px; border: 1px solid #E2E8F0; text-align: center; font-family: monospace; color: #4A5568;">{row["Total Time"]}</td>' \
                         f'<td style="padding: 10px; border: 1px solid #E2E8F0; width: 35%; vertical-align: middle;">{bar_html}</td>' \
                         f'</tr>')

    table_html = f'<table style="width: 100%; border-collapse: collapse; font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif; margin-top: 10px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">' \
                 f'<thead>' \
                 f'<tr style="background-color: #F7FAFC; border: 1px solid #E2E8F0; border-bottom: 2px solid #CBD5E0; color: #4A5568; font-size: 13px;">' \
                 f'<th style="padding: 12px; text-align: left; border: 1px solid #E2E8F0;">Split</th>' \
                 f'<th style="padding: 12px; text-align: center; border: 1px solid #E2E8F0;">Distance</th>' \
                 f'<th style="padding: 12px; text-align: center; border: 1px solid #E2E8F0;">Pace</th>' \
                 f'<th style="padding: 12px; text-align: center; border: 1px solid #E2E8F0;">Avg HR</th>' \
                 f'<th style="padding: 12px; text-align: center; border: 1px solid #E2E8F0;">Total Time</th>' \
                 f'<th style="padding: 12px; text-align: left; border: 1px solid #E2E8F0; width: 35%;">Speed Scale (Color-Mapped to Intensity Zone)</th>' \
                 f'</tr>' \
                 f'</thead>' \
                 f'<tbody style="font-size: 14px;">' \
                 f'{"".join(html_rows)}' \
                 f'</tbody>' \
                 f'</table>'
    
    # Render table onto layout without markdown indentation constraints
    st.markdown(table_html, unsafe_allow_html=True)

    st.markdown("##### 📈 Cumulative Runtime Build-up (Minutes)")
    chart_data = df_splits[["Split", "Cumulative Minutes"]].copy().set_index("Split")
    st.line_chart(chart_data, width="stretch")

# =========================================================================
# 📊 MAIN SECOND COLUMN ACTIVITY DISPLAY RENDERING
# =========================================================================

def render_activity_column(df, elev_columns, unit_abbr):
    """Renders column 2 dashboard container views matching your loop layout structure."""
    if "selected_activity_date" not in st.session_state:
        st.session_state.selected_activity_date = None

    main_layout_col2 = st.container()
    with main_layout_col2:
        if st.session_state.selected_activity_date:
            active_date = st.session_state.selected_activity_date
            matched_runs = df[df['Formatted_Date'] == active_date]

            if not matched_runs.empty:
                st.markdown(f"### 📊 Activity Log Summary: {active_date}")

                # 🏁 Loop opens cleanly
                for run_idx, (_, run_row_raw) in enumerate(matched_runs.iterrows()):
                    matched_run = run_row_raw.to_dict()

                    # Create a distinct visual header for multi-activity days
                    if len(matched_runs) > 1:
                        st.markdown(f"#### 🏃‍♂️ Workout Activity #{run_idx + 1}")
                                        
                    # Single Run Elevation parsing (Moved inside loop)
                    run_elevation = 0.0     
                    if elev_columns:        
                        raw_elev_val = matched_run.get(elev_columns[0], "0")
                        cleaned_run_elev = ''.join(c for c in str(raw_elev_val) if c.isdigit() or c == '.')
                        parsed_elev = pd.to_numeric(cleaned_run_elev, errors='coerce')
                        if pd.notna(parsed_elev): 
                            run_elevation = parsed_elev

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
                            
                            st.caption(f"⏱️    Lap Split Profiles - Activity #{run_idx + 1} (Shorter bars are faster)") 
                            
                            import altair as alt
                            altair_bar_chart = (
                                alt.Chart(splits_df).mark_bar().encode(
                                    x=alt.X('Split Mile:N', sort=None, title="Workout Segment"),
                                    y=alt.Y('Pace (Minutes):Q', title="Pace Minutes"),
                                    color=alt.Color('Zone_Color:N').scale(None), # Feeds direct color vectors
                                    tooltip=['Split Mile', 'pace']
                                ).properties(height=320)
                            )
                            
                            # Render fresh by avoiding Streamlit's old layout memory
                            st.altair_chart(altair_bar_chart, theme=None, key=f"split_chart_refresh_id_{run_idx}_v3")
                            
                        except Exception as e:
                            st.error(f"❌ Chart Processing Error: {str(e)}")

                    # Metric visualization metrics blocks (Moved inside loop)
                    st.metric(f"Activity #{run_idx + 1} Distance", f"{matched_run['Display_Distance']:.2f} {unit_abbr}")
                    st.metric(f"Activity #{run_idx + 1} Duration", matched_run.get('Duration', 'N/A'))
                    if run_elevation > 0:
                        st.metric(f"Activity #{run_idx + 1} Elevation Gain", f"{run_elevation:,.0f} ft") 
                    
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


                if 'pace' in matched_run:
                    flat_pace = pace_str_to_minutes(matched_run['pace'])
                    st.metric("Flat Overall Pace", f"{matched_run['pace']} min/{unit_abbr.lower()}")
                    
                    # Grade Adjusted Pace (GAP) calculation output
                    gap_pace = calculate_grade_adjusted_pace(flat_pace, run_elevation, matched_run['Display_Distance'])
                    st.metric("🔋 Grade-Adjusted Pace (GAP)", f"{minutes_to_pace_str(gap_pace)} min/{unit_abbr.lower()}", delta=f"{run_elevation:,.0f} ft climbing effort penalty" if run_elevation > 0 else None, delta_color="inverse")

                if run_elevation > 0:
                    st.metric("Elevation Gain", f"{run_elevation:,.0f} ft")
            else:
                st.caption("Select a run date inside the grid to load data.")















# ==============================================================================
# EXTENSION: TRAINING ZONE INTENSITY GRAPHIC (WITH TIME DURATION CODES)
# ==============================================================================


def render_zone_octagon_display(matched_run_dict):
    """
    Calculates exact time spent in each heart rate zone based on split duration
    and average_heart_rate, then generates a side-by-side interface displaying 
    a native donut ring and a breakdown table of minutes spent.
    """
    import pandas as pd
    import streamlit as st
    import altair as alt
    
    from character_economy_config import HR_ZONE_CONFIG

    st.markdown("---")
    st.markdown("#### 🛑 Intensity Zone Distribution")

    if not matched_run_dict:
        st.info("Select a workout day to review cardiovascular intensity zone matrices.")
        return

    splits_data = matched_run_dict.get("splits", [])
    if not isinstance(splits_data, list) or not splits_data:
        st.warning("⚠️ No lap split telemetry available to calculate intensity zones.")
        return

    # 1. FIXED: Explicitly unpack string tokens into independent variables to guarantee parsing execution
    def time_str_to_seconds(t_str) -> int:
        try:
            parts = str(t_str).strip().split(':')
            if len(parts) == 3:    # HH:MM:SS
                h_val, m_val, s_val = parts[0], parts[1], parts[2]
                return int(h_val) * 3600 + int(m_val) * 60 + int(s_val)
            elif len(parts) == 2:  # MM:SS
                m_val, s_val = parts[0], parts[1]
                return int(m_val) * 60 + int(s_val)
            return int(float(t_str))
        except (ValueError, TypeError, IndexError):
            return 0

    # 2. Track total elapsed time (seconds) per zone configuration index
    zone_bins = {idx: 0 for idx in range(len(HR_ZONE_CONFIG["zones"]))}
    total_seconds = 0

    for lap in splits_data:
        if not isinstance(lap, dict):
            continue
            
        # Extract heart rate safely (prioritizing average_heart_rate over legacy tags)
        raw_hr = lap.get("average_heart_rate") or lap.get("avg_heart_rate")
        hr = int(float(raw_hr)) if raw_hr is not None else 120
        
        lap_seconds = time_str_to_seconds(lap.get("time", "00:00"))
        total_seconds += lap_seconds

        # Match heart rate value into your HR_ZONE_CONFIG bounds
        matched_idx = 0  # Default fallback index ("No Data")
        if hr > 0:
            for idx, cfg in enumerate(HR_ZONE_CONFIG["zones"]):
                if cfg["max"] == 0:
                    continue
                if hr <= cfg["max"]:
                    matched_idx = idx
                    break
            else:
                matched_idx = len(HR_ZONE_CONFIG["zones"]) - 1
        
        zone_bins[matched_idx] += lap_seconds

    # 3. Format calculated arrays into data frames for layout components
    chart_rows = []
    table_rows = []
    
    for idx, cfg in enumerate(HR_ZONE_CONFIG["zones"]):
        # Skip displaying the 'No Data' row in the presentation layers if empty
        if cfg["max"] == 0 and zone_bins[idx] == 0:
            continue
            
        seconds_spent = zone_bins[idx]
        pct = (seconds_spent / total_seconds * 100) if total_seconds > 0 else 0
        mins, secs = divmod(seconds_spent, 60)
        time_formatted = f"{mins:02d}:{secs:02d}"

        # Donut Chart Dataset (Only includes active zones to preserve slice cleanly)
        if seconds_spent > 0:
            chart_rows.append({
                "Zone": cfg["label"],
                "Percentage": pct,
                "Time": time_formatted,
                "HexColor": cfg["color"]
            })
            
        # Side Summary Table Dataset (Shows active layout distributions)
        table_rows.append({
            "Intensity Zone": cfg["label"],
            "Time Spent": time_formatted,
            "Distribution": f"{pct:.1f}%"
        })

    if not chart_rows:
        st.info("No active heart rate metrics to calculate distributions.")
        return

    df_chart = pd.DataFrame(chart_rows)
    df_table = pd.DataFrame(table_rows)

    # 4. Generate the Donut Ring Graphic Configuration
    domain = df_chart["Zone"].tolist()
    range_colors = df_chart["HexColor"].tolist()

    donut_chart = (
        alt.Chart(df_chart).mark_arc(innerRadius=65, stroke="#fff", strokeWidth=1).encode(
            theta=alt.Theta(field="Percentage", type="quantitative"),
            color=alt.Color(
                field="Zone", 
                type="nominal", 
                scale=alt.Scale(domain=domain, range=range_colors),
                legend=alt.Legend(title="Intensity Status")
            ),
            tooltip=[
                alt.Tooltip("Zone:N", title="Zone"),
                alt.Tooltip("Percentage:Q", format=".1f", title="Percent"),
                alt.Tooltip("Time:N", title="Duration")
            ]
        ).properties(width=340, height=280)
    )

    # 5. FIXED: Added an explicit 2 to st.columns specifier to prevent layout engine collapse
    col_chart, col_table = st.columns(2)

    with col_chart:
        st.altair_chart(donut_chart, theme=None, use_container_width=True)

    with col_table:
        st.markdown("<br><br>", unsafe_allow_html=True) # Aligns the table with the center of the ring
        st.dataframe(
            df_table, 
            hide_index=True, 
            use_container_width=True
        )






#def render_zone_octagon_display(matched_run_dict):
#    """
#    Simulates training zone distributions based on split velocities or pace logs,
#    calculates exact time spent in each zone using the overall run duration,
#    and generates a native geometric donut ring.
#    """
#    import pandas as pd
#    import streamlit as st
#    import altair as alt
#
#    st.markdown("---")
#    st.markdown("#### 🛑 Intensity Zone Distribution")
#
#    if not matched_run_dict:
#        st.info("Select a workout day to review cardiovascular intensity zone matrices.")
#        return
#
#    print(matched_run_dict)
#    # 1. Base Setup and Percentage Allocation
#    zones = [
#        {"name": "Z1: Recovery", "color": "#00ffcc", "pct": 15},
#        {"name": "Z2: Endurance", "color": "#00ccff", "pct": 45},
#        {"name": "Z3: Tempo", "color": "#ffcc00", "pct": 20},
#        {"name": "Z4: Threshold", "color": "#ff6600", "pct": 15},
#        {"name": "Z5: Anaerobic", "color": "#ff3333", "pct": 5}
#    ]
#
#    # Parse real splits array to distribute percentages dynamically
#    raw_splits = matched_run_dict.get("splits", [])
#    if isinstance(raw_splits, list) and len(raw_splits) > 0:
#        paces = []
#        for s in raw_splits:
#            p_str = str(s.get("pace", "08:00"))
#            try:
#                parts = p_str.split(':')
#                if len(parts) == 2: 
#                    paces.append(int(parts[0])*60 + int(parts[1]))
#            except Exception: 
#                pass
#        
#        if len(paces) > 1:
#            slowest = max(paces)
#            fastest = min(paces)
#            span = max(1, slowest - fastest)
#            
#            z1, z2, z3, z4, z5 = 0, 0, 0, 0, 0
#            for p in paces:
#                rel = (slowest - p) / span
#                if rel < 0.2: z1 += 1
#                elif rel < 0.5: z2 += 1
#                elif rel < 0.75: z3 += 1
#                elif rel < 0.92: z4 += 1
#                else: z5 += 1
#            
#            total = len(paces)
#            p1 = int((z1 / total) * 100)
#            p2 = int((z2 / total) * 100)
#            p3 = int((z3 / total) * 100)
#            p4 = int((z4 / total) * 100)
#            p5 = 100 - (p1 + p2 + p3 + p4)
#            
#            z_vals = [p1, p2, p3, p4, p5]
#            for idx, z_item in enumerate(zones):
#                z_item["pct"] = max(5, z_vals[idx])
#
#    # 2. NEW LOGIC: Parse run duration into total seconds to calculate exact zone times
#    duration_str = str(matched_run_dict.get('Duration', '00:00')).strip()
#    total_duration_seconds = 0
#    
#    try:
#        time_parts = duration_str.split(':')
#        if len(time_parts) == 2:  # MM:SS format
#            total_duration_seconds = int(time_parts[0]) * 60 + int(time_parts[1])
#        elif len(time_parts) == 3:  # HH:MM:SS format
#            total_duration_seconds = int(time_parts[0]) * 3600 + int(time_parts[1]) * 60 + int(time_parts[2])
#    except Exception:
#        total_duration_seconds = 2400  # Fallback baseline (40 minutes) if parsing fails
#
#    # Helper function to convert seconds back to a nice time string
#    def format_seconds_to_clock(secs):
#        hrs = secs // 3600
#        mins = (secs % 3600) // 60
#        secs = secs % 60
#        if hrs > 0:
#            return f"{hrs:02d}:{mins:02d}:{secs:02d}"
#        return f"{mins:02d}:{secs:02d}"
#
#    # 3. Build Dataset for Charting
#    chart_rows = []
#    for z in zones:
#        chart_rows.append({
#            "Zone": z["name"],
#            "Percentage": z["pct"]
#        })
#    df_chart = pd.DataFrame(chart_rows)
#    # 4. Render Layout Columns Side-by-Side Natively (UPSCALED CHART SIZING)
#    col_g1, col_g2 = st.columns([0.5, 0.5])
#    
#    with col_g1:
#        # Increased innerRadius to 45, width/height to 170 for a significantly larger visual display
#        donut_chart = alt.Chart(df_chart).mark_arc(innerRadius=45, stroke="#1e222b", strokeWidth=2).encode(
#            theta=alt.Theta(field="Percentage", type="quantitative"),
#            color=alt.Color(field="Zone", type="nominal", scale=alt.Scale(
#                domain=[z["name"] for z in zones],
#                range=[z["color"] for z in zones]
#            ), legend=None),
#            tooltip=["Zone", "Percentage"]
#        ).properties(
#            width=170,
#            height=170
#        )
#        
#        st.altair_chart(donut_chart, theme=None)
#        
#    with col_g2:
#        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
#        for z in zones:
#            zone_color = z["color"]
#            zone_name = z["name"]
#            zone_pct = z["pct"]
#            
#            # Calculate exact seconds spent in this zone based on its percentage weight
#            zone_seconds = int(round(total_duration_seconds * (zone_pct / 100.0)))
#            zone_time_str = format_seconds_to_clock(zone_seconds)
#            
#            st.markdown(
#                f"<span style='color:{zone_color}; font-size:18px;'>■</span> "
#                f"**{zone_name}**: `{zone_pct}%` ({zone_time_str})", 
#                unsafe_allow_html=True
#            )


# ==============================================================================
# EXTENSION: RPG CHARACTER TRAINING LEDGER REWARDS (READ ONLY CALENDAR CAPTURE)
# ==============================================================================
def render_rpg_xp_rewards(matched_run_dict, player_profile_obj=None):
    """
    Displays historical summary receipts of character attributes and currency earned 
    from real-world workouts. Submissions are read-only to prevent farming loops.
    """
    import streamlit as st

    st.markdown("---")
    st.markdown("#### ⚔️ Coliseum Training Attribute Rewards")

    if not matched_run_dict:
        st.info("Select a completed activity day to view rewarded training attributes.")
        return

    try:
        distance = float(matched_run_dict.get('Display_Distance', 0.0))
        if distance <= 0:
            distance = float(matched_run_dict.get('Distance (Miles)', 0.0))
    except Exception:
        distance = 0.0

    base_xp = int(distance * 10)  # 10 Base XP per Mile
    
    # Isolate nested split percentage logs
    z1 = matched_run_dict.get('z1_pct', 15)
    z2 = matched_run_dict.get('z2_pct', 45)
    z3 = matched_run_dict.get('z3_pct', 20)
    z4 = matched_run_dict.get('z4_pct', 15)
    z5 = matched_run_dict.get('z5_pct', 5)

    stamina_xp = max(5, int(base_xp * (z1 + z2) / 50.0)) if distance > 0 else 0
    agility_xp = max(0, int(base_xp * (z3 + z4) / 50.0)) if distance > 0 else 0
    power_xp = max(0, int(base_xp * (z5 * 3) / 50.0)) if distance > 0 else 0
    gold_earned = max(2, int(distance * 5 + (stamina_xp + agility_xp + power_xp) * 0.1)) if distance > 0 else 0

    col_xp1, col_xp2 = st.columns([0.5, 0.5])
    with col_xp1:
        st.markdown(f"🟢 **Stamina XP:** `+{stamina_xp} XP` *(Z1/Z2 Engine)*")
        st.markdown(f"🟡 **Agility XP:** `+{agility_xp} XP` *(Z3/Z4 Tempo)*")
        st.markdown(f"🔴 **Power XP:** `+{power_xp} XP` *(Z5 Anaerobic)*")
        
    with col_xp2:
        st.markdown(f"🪙 **Gold Shards:** `+{gold_earned} Gold`")
        st.markdown("✨ **Status:** `🛡️ Claimed & Processed`")

