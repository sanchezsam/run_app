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
@st.cache_data(ttl=600)



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
                            run_row = day_runs.iloc[0]
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
                    day_runs = target_df[target_df['Formatted_Date'] == target_date_str]
                    
                    if not day_runs.empty:
                        run_row = day_runs.iloc[0]
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
def render_progression_nonagon(endurance_lvl, pace_lvl, hill_lvl):
    """
    Builds and returns a 9-slice polar chart representing progression levels.
    """
    num_slices = 9
    labels = [
        "Endur. L1", "Endur. L2", "Endur. L3",
        "Pace L1", "Pace L2", "Pace L3",
        "Hill L1", "Hill L2", "Hill L3"
    ]
    
    values = [
        min(endurance_lvl, 1), min(max(endurance_lvl - 1, 0), 1), min(max(endurance_lvl - 2, 0), 1),
        min(pace_lvl, 1),      min(max(pace_lvl - 1, 0), 1),      min(max(pace_lvl - 2, 0), 1),
        min(hill_lvl, 1),      min(max(hill_lvl - 1, 0), 1),      min(max(hill_lvl - 2, 0), 1)
    ]
    
    display_values = [v * 3 for v in values]
    angles = np.linspace(0, 2 * np.pi, num_slices, endpoint=False).tolist()
    
    display_values += display_values[:1]
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(4.5, 4.5), subplot_kw=dict(polar=True))
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    
    plt.xticks(angles[:-1], labels, color='#ffffff', size=8)
    ax.set_rlabel_position(0)
    plt.yticks([1, 2, 3], ["L1", "L2", "L3"], color="#7e8794", size=7)
    plt.ylim(0, 3)
    
    ax.plot(angles, display_values, color=THEME_CONFIG["NONAGON_LINE"], linewidth=2, linestyle='solid')
    ax.fill(angles, display_values, color=THEME_CONFIG["NONAGON_FILL"], alpha=0.3)
    
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
    df['Distance (Miles)'] = pd.to_numeric(df['Distance (Miles)'], errors='coerce').fillna(0)
    df = df.dropna(subset=['Date']).sort_values('Date')
    
    df['Year'] = df['Date'].dt.year.astype(str)
    df['Month_Period'] = df['Date'].dt.to_period('M')  
    df['Month_Label'] = df['Date'].dt.strftime('%b %Y')  
    df['Formatted_Date'] = df['Date'].dt.strftime('%Y-%m-%d')

    st.subheader("🎛️ Unit & Filter Configuration")
    config_col1, config_col2 = st.columns(2)
    
    with config_col2:
        unit_system = st.selectbox(
            label="🔄 Select System Unit:",
            options=["Miles (mi)", "Kilometers (km)"],
            index=0
        )
    
    is_km = unit_system == "Kilometers (km)"
    unit_abbr = "Km" if is_km else "Mi"
    df['Display_Distance'] = df['Distance (Miles)'] * (1.60934 if is_km else 1.0)

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
            st.bar_chart(data=daily_plot_df, x='Formatted_Date', y='Display_Distance', use_container_width=True)
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
            st.bar_chart(data=monthly_plot_df, x='Month_Label', y='Display_Distance', use_container_width=True)
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
            st.bar_chart(data=yearly_plot_df, x='Year', y='Display_Distance', use_container_width=True)
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

    st.radio(label="Layout Perspective Selector Switch:", options=["📅 Grid View", "📊 Spreadsheet View", "📆 Full Year View"], key="calendar_display_view", horizontal=True)
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
                        use_container_width=True, 
                        on_click=handle_navigation_callback, 
                        args=(prev_year, prev_month_str)
                    )

            with nav_col2:
                st.markdown(f"<h3 style='text-align: center; color: white; margin-top: 5px; margin-bottom: 5px; letter-spacing: 1px;'>{current_header_title}</h3>", unsafe_allow_html=True)
            with nav_col3:

                if has_next: st.button("▶", key=f"next_nav_btn_{st.session_state.grid_year_dropdown}_{st.session_state.grid_month_dropdown}", use_container_width=True, on_click=handle_navigation_callback, args=(next_year, next_month_str))









            # Full Year View
            if is_year_view:
                table_body_html = ""
                for m_idx in range(1, 13):
                    m_matrix = calendar.monthcalendar(cal_year, m_idx)
                    m_name = month_names[m_idx - 1]
                    m_df = target_df[target_df['Month_Int'] == m_idx]
                    
                    table_body_html += f"<tr><td colspan='6' style='background-color: #1a1c23; color: #00ffcc; font-weight: bold; padding: 10px; text-transform: uppercase;'>📅 {m_name} Logs</td></tr>"
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
                            
                            if not day_runs.empty:
                                run_row = day_runs.iloc[0]
                                run_dist = run_row['Display_Distance']
                                run_time = run_row.get('Duration', '--:--')
                                # 🧮 UPGRADED LIVE CALCULATOR FIX:
                                raw_p = run_row.get('pace', '—')
                                
                                # Convert duration string "HH:MM:SS" or "MM:SS" into total minutes
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

                                # 1. If the direct pace value is valid, attempt to read it
                                is_invalid_pace = pd.isna(raw_p) or str(raw_p).lower() == "nan" or raw_p == "—"
                                
                                if not is_invalid_pace:
                                    try:
                                        float_p = float(raw_p)
                                        run_pace_decimal = float_p if float_p > 0 else 0.0
                                    except (ValueError, TypeError):
                                        run_pace_decimal = 0.0
                                else:
                                    run_pace_decimal = 0.0

                                # 2. BACKUP CALCULATOR IN ACTION: If missing, calculate it right now from Time & Distance!
                                if run_pace_decimal == 0.0 and run_dist > 0:
                                    total_minutes = duration_str_to_minutes(run_time)
                                    if total_minutes > 0:
                                        run_pace_decimal = total_minutes / run_dist

                                # 3. Convert the finalized decimal into clean, professional MM:SS text layout
                                if run_pace_decimal > 0:
                                    m_part = int(run_pace_decimal)
                                    s_part = int(round((run_pace_decimal - m_part) * 60))
                                    if s_part == 60:
                                        m_part += 1
                                        s_part = 0
                                    run_pace = f"{m_part}:{s_part:02d} min/{unit_abbr.lower()}"
                                else:
                                    run_pace = f"— min/{unit_abbr.lower()}"
                                # --- 🎽 PATCH ROW VISUAL INJECTOR ---
                                # Extract the patch dictionary list attached to this run row object
                                run_patches_list = run_row.get('earned_patches', [])
                                
                                # Safety conversion check: Handle string entries or list data frames safely
                                if isinstance(run_patches_list, str):
                                    try:
                                        # Parse string literal structures if stored as flat text data fields
                                        run_patches_list = json.loads(run_patches_list.replace("'", '"'))
                                    except Exception:
                                        run_patches_list = []
                                        
                                # Pull out just the iconic emojis from the patch dictionary objects
                                if isinstance(run_patches_list, list) and len(run_patches_list) > 0:
                                    # Extracts and merges emojis into a clean visual row (e.g. "🐇 🏔️ 📜")
                                    patch_emoji_string = " ".join([p.get('icon', '') for p in run_patches_list if isinstance(p, dict) and 'icon' in p])
                                else:
                                    patch_emoji_string = ""

                                # Append the visual achievement badges onto your calendar pace label
                                if patch_emoji_string:
                                    run_pace = f"{run_pace}   {patch_emoji_string}"
                                # --- 🎽 PATCH ROW VISUAL INJECTOR ---
                                # Extract the patch dictionary list attached to this run row object
                                run_patches_list = run_row.get('earned_patches', [])
                                
                                # Safety conversion check: Handle string entries or list data frames safely
                                if isinstance(run_patches_list, str):
                                    try:
                                        # Parse string literal structures if stored as flat text data fields
                                        run_patches_list = json.loads(run_patches_list.replace("'", '"'))
                                    except Exception:
                                        run_patches_list = []
                                        
                                # Pull out just the iconic emojis from the patch dictionary objects
                                if isinstance(run_patches_list, list) and len(run_patches_list) > 0:
                                    # Extracts and merges emojis into a clean visual row (e.g. "🐇 🏔️ 📜")
                                    patch_emoji_string = " ".join([p.get('icon', '') for p in run_patches_list if isinstance(p, dict) and 'icon' in p])
                                else:
                                    patch_emoji_string = ""

                                # Append the visual achievement badges onto your calendar pace label
                                if patch_emoji_string:
                                    run_pace = f"{run_pace}   {patch_emoji_string}"




















                                
                                day_elevation = 0.0
                                if run_elev_cols := [c for c in m_df.columns if 'elev' in c.lower()]:
                                    raw_elev_val = run_row.get(run_elev_cols[0], "0")
                                    cleaned_run_elev = ''.join(c for c in str(raw_elev_val) if c.isdigit() or c == '.')
                                    parsed_elev = pd.to_numeric(cleaned_run_elev, errors='coerce')
                                    if pd.notna(parsed_elev): day_elevation = parsed_elev
                                    
                                week_dist += run_dist
                                m_dist += run_dist
                                week_elev += day_elevation
                                m_elev += day_elevation
                                
                                if isinstance(run_time, str) and ':' in run_time:
                                    parts = run_time.split(':')
                                    try:
                                        if len(parts) == 3: week_seconds += int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                                        elif len(parts) == 2: week_seconds += int(parts[0]) * 60 + int(parts[1])
                                    except ValueError: pass
                                        
                                week_rows_buffer += f"<tr class='day-row'><td><b>{target_date_str}</b></td><td style='color: #00ffff; font-weight: bold;'>🏃 RUN</td><td>{run_dist:.2f} {unit_abbr}</td><td>{run_time}</td><td>{run_pace}</td><td>{day_elevation:,.0f} ft</td></tr>"
                            else:
                                week_rows_buffer += f"<tr class='day-row'><td>{target_date_str}</td><td style='color: #ffcc00; font-weight: bold;'>🧘 REST DAY</td><td style='color: #7e8794;'>—</td><td style='color: #7e8794;'>—</td><td style='color: #7e8794;'>—</td><td style='color: #7e8794;'>—</td></tr>"
                        
                        if week_has_days:
                            table_body_html += week_rows_buffer
                            w_hours = week_seconds // 3600
                            w_mins = (week_seconds % 3600) // 60
                            w_time_str = f"{w_hours}h {w_mins}m" if w_hours > 0 else f"{w_mins}m"
                            table_body_html += f"<tr class='weekly-total-row'><td>WEEK {w_idx + 1} TOTALS</td><td>📊 SUMMARY</td><td>{week_dist:.2f} {unit_abbr}</td><td>{w_time_str if week_seconds > 0 else '—'}</td><td>—</td><td>{week_elev:,.0f} ft</td></tr>"
                    
                    m_hours = m_seconds // 3600
                    m_mins = (m_seconds % 3600) // 60
                    table_body_html += f"<tr class='monthly-total-row'><td>{m_name.upper()} TOTALS</td><td>📈 MONTH SUMMARY</td><td>{m_dist:.2f} {unit_abbr}</td><td>{f'{m_hours}h {m_mins}m' if m_seconds > 0 else '—'}</td><td>—</td><td>{m_elev:,.0f} ft</td></tr>"
                
                y_hours = total_seconds // 3600
                y_mins = (total_seconds % 3600) // 60
                table_body_html += f"<tr class='yearly-total-row'><td>🏆 {cal_year} YEAR TOTALS</td><td>🌟 GRAND OVERVIEW</td><td>{total_miles_aggregated:.2f} {unit_abbr}</td><td>{f'{y_hours}h {y_mins}m' if total_seconds > 0 else '—'}</td><td>—</td><td>{total_elevation_aggregated:,.0f} ft</td></tr>"
                
                year_html = f"<table class='spreadsheet-table'><thead><tr><th>Run Date</th><th>Status</th><th>Distance</th><th>Duration</th><th>Average Pace</th><th>Ascent Gain</th></tr></thead><tbody>{table_body_html}</tbody></table>"
                st.markdown(year_html, unsafe_allow_html=True)

            # Spreadsheet View
            elif st.session_state.calendar_display_view == "📊 Spreadsheet View":
                table_body_html = ""
                months_to_loop = range(1, 13) if cal_month_name == "All Months" else [cal_month]
                
                for loop_m in months_to_loop:
                    if cal_month_name == "All Months":
                        table_body_html += f"<tr><td colspan='6' style='background-color: #1a1c23; color: #00ffcc; font-weight: bold; padding: 10px; text-transform: uppercase;'>📅 {month_names[loop_m - 1].upper()} LOGS</td></tr>"
                    cal_matrix = calendar.monthcalendar(cal_year, loop_m)
                    
                    for w_idx, week in enumerate(cal_matrix):
                        week_has_days = False
                        week_dist, week_seconds, week_elev = 0.0, 0, 0.0
                        week_rows_buffer = ""
                        
                        for day in week:
                            if day == 0: continue
                            week_has_days = True
                            target_date_str = f"{cal_year}-{loop_m:02d}-{day:02d}"
                            day_runs = cal_df[cal_df['Formatted_Date'] == target_date_str]

                            if not day_runs.empty:
                                run_row = day_runs.iloc[0]
                                run_dist = run_row['Display_Distance']
                                run_time = run_row.get('Duration', '--:--')
                                
                                # 🧮 UPGRADED LIVE CALCULATOR FIX:
                                raw_p = run_row.get('pace', '—')
                                
                                # Convert duration string "HH:MM:SS" or "MM:SS" into total minutes
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

                                # 1. If the direct pace value is valid, attempt to read it
                                is_invalid_pace = pd.isna(raw_p) or str(raw_p).lower() == "nan" or raw_p == "—"
                                
                                if not is_invalid_pace:
                                    try:
                                        float_p = float(raw_p)
                                        run_pace_decimal = float_p if float_p > 0 else 0.0
                                    except (ValueError, TypeError):
                                        run_pace_decimal = 0.0
                                else:
                                    run_pace_decimal = 0.0

                                # 2. BACKUP CALCULATOR IN ACTION: If missing, calculate it right now from Time & Distance!
                                if run_pace_decimal == 0.0 and run_dist > 0:
                                    total_minutes = duration_str_to_minutes(run_time)
                                    if total_minutes > 0:
                                        run_pace_decimal = total_minutes / run_dist

                                # 3. Convert the finalized decimal into clean, professional MM:SS text layout
                                if run_pace_decimal > 0:
                                    m_part = int(run_pace_decimal)
                                    s_part = int(round((run_pace_decimal - m_part) * 60))
                                    if s_part == 60:
                                        m_part += 1
                                        s_part = 0
                                    run_pace = f"{m_part}:{s_part:02d} min/{unit_abbr.lower()}"
                                else:
                                    run_pace = f"— min/{unit_abbr.lower()}"

                                day_elevation = 0.0
                                if elev_columns:
                                    raw_elev_val = run_row.get(elev_columns[0], "0")
                                    cleaned_run_elev = ''.join(c for c in str(raw_elev_val) if c.isdigit() or c == '.')
                                    parsed_elev = pd.to_numeric(cleaned_run_elev, errors='coerce')
                                    if pd.notna(parsed_elev): day_elevation = parsed_elev

                                week_dist += run_dist
                                week_elev += day_elevation
 
                                if isinstance(run_time, str) and ':' in run_time:
                                    parts = run_time.split(':')
                                    try:
                                        if len(parts) == 3: week_seconds += int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                                        elif len(parts) == 2: week_seconds += int(parts[0]) * 60 + int(parts[1])
                                    except ValueError: pass
                                
                                week_rows_buffer += f"<tr class='day-row'><td><b>{target_date_str}</b></td><td style='color: #00ffff; font-weight: bold;'>🏃 RUN</td><td>{run_dist:.2f} {unit_abbr}</td><td>{run_time}</td><td>{run_pace}</td><td>{day_elevation:,.0f} ft</td></tr>"
                            else:
                                week_rows_buffer += f"<tr class='day-row'><td>{target_date_str}</td><td style='color: #ffcc00; font-weight: bold;'>🧘 REST DAY</td><td style='color: #7e8794;'>—</td><td style='color: #7e8794;'>—</td><td style='color: #7e8794;'>—</td><td style='color: #7e8794;'>—</td></tr>"
                        
                        if week_has_days:
                            table_body_html += week_rows_buffer
                            w_hours = week_seconds // 3600
                            w_mins = (week_seconds % 3600) // 60
                            w_time_str = f"{w_hours}h {w_mins}m" if w_hours > 0 else f"{w_mins}m"
                            table_body_html += f"<tr class='weekly-total-row'><td>WEEK {w_idx + 1} TOTALS</td><td>📊 SUMMARY</td><td>{week_dist:.2f} {unit_abbr}</td><td>{w_time_str if week_seconds > 0 else '—'}</td><td>—</td><td>{week_elev:,.0f} ft</td></tr>"
                
                spreadsheet_html = f"<table class='spreadsheet-table'><thead><tr><th>Calendar Date</th><th>Activity Status</th><th>Distance</th><th>Duration Time</th><th>Overall Pace</th><th>Climbed Elev</th></tr></thead><tbody>{table_body_html}</tbody></table>"
                st.markdown(spreadsheet_html, unsafe_allow_html=True)

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
                                    
                                    if not day_runs.empty:
                                        run_row = day_runs.iloc[0]
                                        run_dist = run_row['Display_Distance']
                                        run_time = run_row.get('Duration', '--:--')
                                        btn_label = f"{day}\n\n{run_dist:.1f}{unit_abbr}\n{run_time}"
                                        
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
                matched_run = matched_runs.iloc[0].to_dict()
                st.markdown(f"### 📊 Run Summary: {active_date}")
                
    
                # Single Run Elevation parsing
                run_elevation = 0.0
                if elev_columns:
                    raw_elev_val = matched_run.get(elev_columns[0], "0")
                    cleaned_run_elev = ''.join(c for c in str(raw_elev_val) if c.isdigit() or c == '.')
                    parsed_elev = pd.to_numeric(cleaned_run_elev, errors='coerce')
                    if pd.notna(parsed_elev): run_elevation = parsed_elev

                if "splits" in matched_run and isinstance(matched_run["splits"], list) and len(matched_run["splits"]) > 0:
                    splits_df = pd.DataFrame(matched_run["splits"])
                    splits_df['Split Mile'] = "M" + splits_df['split_num'].astype(str)
                    splits_df['Pace (Minutes)'] = splits_df['pace'].apply(pace_str_to_minutes)
                    
                    st.caption("⏱️ Lap Split Profiles (Shorter bars are faster)")
                    st.bar_chart(data=splits_df, x='Split Mile', y='Pace (Minutes)', use_container_width=True)
                
                st.metric("Total Distance", f"{matched_run['Display_Distance']:.2f} {unit_abbr}")
                st.metric("Duration", matched_run.get('Duration', 'N/A'))
                if run_elevation > 0:
                    st.metric("Elevation Gain", f"{run_elevation:,.0f} ft")
                    
                # ------------------------------------------------------------------
                # LAUNCH THE DYNAMIC LAP BREAKDOWN (Passes raw dictionaries directly)
                # ------------------------------------------------------------------
                try:
                    if "matched_run" in locals() and matched_run:
                        show_run_lap_breakdown(matched_run, unit_abbr=unit_abbr)
                        # --------------------------------------------------------------
                        # LAUNCH THE INTENSITY OCTAGON VISUALIZATION
                        # --------------------------------------------------------------
                        render_zone_octagon_display(matched_run)
                        # --------------------------------------------------------------
                        
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


def render_progression_nonagon(endurance_lvl, pace_lvl, hill_lvl):
    """
    Builds and returns a 9-slice polar chart representing progression levels.
    Expects levels between 0 and 3 for each attribute.
    """
    num_slices = 9
    
    # Define labels for the 9 slices (3 slices per attribute category)
    labels = [
        "Endurance L1", "Endurance L2", "Endurance L3",
        "Pace L1", "Pace L2", "Pace L3",
        "Hill L1", "Hill L2", "Hill L3"
    ]
    
    # Calculate step fills dynamically based on current levels (max value 3)
    values = [
        min(endurance_lvl, 1), min(max(endurance_lvl - 1, 0), 1), min(max(endurance_lvl - 2, 0), 1),
        min(pace_lvl, 1),      min(max(pace_lvl - 1, 0), 1),      min(max(pace_lvl - 2, 0), 1),
        min(hill_lvl, 1),      min(max(hill_lvl - 1, 0), 1),      min(max(hill_lvl - 2, 0), 1)
    ]
    
    # Scale binary slice availability to uniform map steps
    display_values = [v * 3 for v in values]
    
    # Calculate angles for a closed 9-sided nonagon
    angles = np.linspace(0, 2 * np.pi, num_slices, endpoint=False).tolist()
    
    # Close the polygon loop mathematically
    display_values += display_values[:1]
    angles += angles[:1]
    
    # Instantiate figure canvas object
    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
    
    # Rotate layout so the first vertex is anchored cleanly at the top
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    
    # Apply labels and nonagon spine grid coordinates
    plt.xticks(angles[:-1], labels, color='#333333', size=9)
    ax.set_rlabel_position(0)
    plt.yticks([1, 2, 3], ["L1", "L2", "L3"], color="grey", size=8)
    plt.ylim(0, 3)
    
    # Plot outer border outline and inner area fills
    ax.plot(angles, display_values, color='#2e7d32', linewidth=2, linestyle='solid')
    ax.fill(angles, display_values, color='#81c784', alpha=0.5)
    
    return fig



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
    
    with config_col2:
        unit_system = st.selectbox(
            label="🔄 Select System Unit:",
            options=["Miles (mi)", "Kilometers (km)"],
            index=0
        )
    
    # Conversion multiplier variables
    is_km = unit_system == "Kilometers (km)"
    unit_abbr = "Km" if is_km else "Mi"
    
    # Apply conversions across the primary tracking vectors
    df['Display_Distance'] = df['Distance (Miles)'] * (1.60934 if is_km else 1.0)

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

    # ------------------------------------------
    # COLUMN 1: DAILY RUN LOGS
    # ------------------------------------------
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
            
            st.bar_chart(
                data=daily_plot_df,
                x='Formatted_Date',
                y='Display_Distance',
                use_container_width=True
            )
            st.metric(f"Daily Segment Total ({unit_abbr})", f"{daily_plot_df['Display_Distance'].sum():,.2f} {unit_abbr}")
        else:
            st.caption("No data for current filters.")

    # ------------------------------------------
    # COLUMN 2: MONTHLY TREND AGGREGATION
    # ------------------------------------------
    with col2:
        st.subheader("📅 Monthly Trends")
        
        if not filtered_df.empty:
            monthly_df = filtered_df.groupby(['Month_Period', 'Month_Label'])['Display_Distance'].sum().reset_index()
            monthly_df = monthly_df.sort_values('Month_Period').reset_index(drop=True)
            total_months = len(monthly_df)
            
            min_month_val = 1
            max_month_val = 12
        
            if min_month_val == max_month_val:
                if min_month_val == 12:
                    min_month_val = 11  # Slide minimum down if locked at December
                else:
                    max_month_val = min_month_val + 1  # Pad maximum up by 1 month
        
            # 2. Update your st.slider widget on Line 1853 to look exactly like this:
            month_range = st.slider(
                label="📅 Filter Workout Month Range",
                min_value=int(min_month_val),
                max_value=int(max_month_val),
                value=(int(min_month_val), int(max_month_val)),
                step=1,
                key="month_range_slider"
            )
            
            start_month, end_month = month_range
            monthly_plot_df = monthly_df.iloc[start_month : end_month + 1]
            
            st.bar_chart(
                data=monthly_plot_df,
                x='Month_Label',
                y='Display_Distance',
                use_container_width=True
            )
            st.metric(f"Monthly Segment Total ({unit_abbr})", f"{monthly_plot_df['Display_Distance'].sum():,.2f} {unit_abbr}")
        else:
            st.caption("No data for current filters.")

    # ------------------------------------------
    # COLUMN 3: YEAR-OVER-YEAR HISTORICAL COMPARISON
    # ------------------------------------------
    with col3:
        st.subheader("📈 Annual Totals")
        
        yearly_df = df.groupby('Year')['Display_Distance'].sum().reset_index().sort_values('Year').reset_index(drop=True)
        total_years = len(yearly_df)
        
        if total_years > 0:
            if 'min_year' in locals() or 'max_year' in locals():
                # If your code uses variables named min_year / max_year
                if min_year == max_year or min_year == 0:
                    if min_year == 0 or min_year == 0.0:
                        min_year, max_year = 2022, 2023
                    else:
                        max_year = min_year + 1
            else:
                # If your code uses a pandas DataFrame column to extract values on the fly:
                try:
                    # Check what your min/max extraction variables are named
                    min_year = int(cal_df['Year'].min()) if not cal_df.empty else 2022
                    max_year = int(cal_df['Year'].max()) if not cal_df.empty else 2022
                    if min_year == max_year:
                        max_year = min_year + 1
                except Exception:
                    min_year, max_year = 2022, 2023
        
            # 2. Update your slider on Line 1895 to use these guarded boundaries:
            year_range = st.slider(
                label="📅 Filter Workout Year Range",
                min_value=int(min_year),
                max_value=int(max_year),
                value=(int(min_year), int(max_year)),
                step=1,
                key="year_range_slider"
            )
            
            start_year, end_year = year_range
            yearly_plot_df = yearly_df.iloc[start_year : end_year + 1]
            
            st.bar_chart(
                data=yearly_plot_df,
                x='Year',
                y='Display_Distance',
                use_container_width=True
            )
            st.metric(f"All-Time History Total ({unit_abbr})", f"{df['Display_Distance'].sum():,.2f} {unit_abbr}")
        else:
            st.caption("No dynamic historical year structures found.")







# ==============================================================================
# EXTENSION: ADVANCED DYNAMIC LAP SPLIT PROFILER (REAL DATA SPLITS)
# ==============================================================================
def show_run_lap_breakdown(matched_run_dict, unit_abbr="Mi"):
    """
    Extracts real mile-by-mile split records from the activity logs to generate
    authentic color-gradient variations, cumulative charts, and GAP metrics.
    """
    import pandas as pd
    import streamlit as st
    
    st.markdown("---")
    st.markdown("#### ⏱️ 1-Mile Split & Performance Analysis")
    
    if not matched_run_dict:
        st.info("Select an active run day to view performance split curves.")
        return

    # Extract real nested splits array list from your schema log records
    raw_splits = matched_run_dict.get("splits", [])
    
    lap_records = []
    cumulative_seconds = 0.0
    
    # CASE 1: If real nested splits exist, parse their actual varied pacing records
    if isinstance(raw_splits, list) and len(raw_splits) > 0:
        for idx, split_item in enumerate(raw_splits):
            lap_idx = split_item.get("split_num", idx + 1)
            
            # Extract real split distance and pace values
            try:
                lap_dist = float(split_item.get("distance", 1.0))
            except Exception:
                lap_dist = 1.0
                
            pace_str = str(split_item.get("pace", "08:00"))
            
            # Parse pace time string to integer seconds
            try:
                parts = pace_str.strip().split(':')
                lap_pace_secs = int(parts[0]) * 60 + int(parts[1])
            except Exception:
                lap_pace_secs = 480.0
                
            lap_seconds = lap_dist * lap_pace_secs
            cumulative_seconds += lap_seconds
            
            # Grade Adjusted Pace (GAP) calculation output per specific mile hill profile
            try:
                split_elev = float(split_item.get("elevation_gain", 0.0))
            except Exception:
                split_elev = 0.0
                
            if split_elev > 0 and lap_dist > 0:
                climb_ratio = split_elev / (lap_dist * 5280.0)
                gap_factor = 1.0 + (climb_ratio * 6.0) # Localised hill exertion multiplier
                gap_seconds = lap_pace_secs / gap_factor
                gap_mins = int(gap_seconds) // 60
                gap_secs = int(round(gap_seconds % 60))
                if gap_secs == 60: gap_mins += 1; gap_secs = 0
                gap_time_str = f"{gap_mins:02d}:{gap_secs:02d}"
            else:
                gap_time_str = pace_str

            def format_cumulative_clock(total_secs):
                total_secs_rounded = int(round(total_secs))
                hrs = total_secs_rounded // 3600
                mins = (total_secs_rounded % 3600) // 60
                secs = total_secs_rounded % 60
                return f"{hrs:02d}:{mins:02d}:{secs:02d}" if hrs > 0 else f"{mins:02d}:{secs:02d}"

            lap_records.append({
                "Split": f"Mile {lap_idx}",
                "Distance": f"{lap_dist:.2f} {unit_abbr.lower()}",
                "Pace": pace_str,
                "GAP Pace (Flat-Eq)": gap_time_str,
                "Total Time": format_cumulative_clock(cumulative_seconds),
                "Cumulative Minutes": cumulative_seconds / 60.0,
                "Raw Pace Mins": lap_pace_secs / 60.0
            })
            
    # CASE 2: Fallback to simulated intervals if activity contains no sub-split logs
    else:
        try:
            run_distance = float(matched_run_dict.get('Display_Distance', 0.0))
            average_pace_str = matched_run_dict.get('pace', '08:00')
            
            parts = str(average_pace_str).strip().split(':')
            base_secs = int(parts[0]) * 60 + int(parts[1]) if len(parts) == 2 else 480.0
            
            # Introduce a minor artificial variance curve so colors look authentic even for flat imports
            remaining_dist = run_distance
            sim_lap_idx = 1
            while remaining_dist > 0:
                current_lap_dist = 1.0 if remaining_dist >= 1.0 else remaining_dist
                remaining_dist -= current_lap_dist
                
                # Slight variation math simulation (makes fatigue curve drift realistically)
                variance_multiplier = 0.96 + (sim_lap_idx * 0.02) if run_distance > 1 else 1.0
                lap_pace_secs = base_secs * variance_multiplier
                lap_seconds = current_lap_dist * lap_pace_secs
                cumulative_seconds += lap_seconds
                
                split_mins = int(lap_pace_secs) // 60
                split_secs = int(round(lap_pace_secs % 60))
                if split_secs == 60: split_mins += 1; split_secs = 0
                
                lap_records.append({
                    "Split": f"Mile {sim_lap_idx}" if current_lap_dist == 1.0 else f"Mile {sim_lap_idx} (Final)",
                    "Distance": f"{current_lap_dist:.2f} {unit_abbr.lower()}",
                    "Pace": f"{split_mins:02d}:{split_secs:02d}",
                    "GAP Pace (Flat-Eq)": f"{split_mins:02d}:{split_secs:02d}",
                    "Total Time": f"{int(cumulative_seconds)//3600:02d}:{int(cumulative_seconds%3600)//60:02d}:{int(cumulative_seconds%60):02d}" if cumulative_seconds >= 3600 else f"{int(cumulative_seconds)//60:02d}:{int(cumulative_seconds%60):02d}",
                    "Cumulative Minutes": cumulative_seconds / 60.0,
                    "Raw Pace Mins": lap_pace_secs / 60.0
                })
                sim_lap_idx += 1
        except Exception:
            pass

    if not lap_records:
        st.info("No numerical split vectors available to process.")
        return

    df_splits = pd.DataFrame(lap_records)
    st.caption("🟢 Pace Highlights: Deeper green bars or blocks reflect faster, highly efficient split intervals")
    
    display_columns = ["Split", "Distance", "Pace", "GAP Pace (Flat-Eq)", "Total Time"]

    try:
        # Build a native column configuration map to inject real-time color gauges 
        # and formatting properties onto your datagrid elements
        col_configurations = {
            "Split": st.column_config.TextColumn("Split", help="Interval Identifier Segment"),
            "Distance": st.column_config.TextColumn("Distance"),
            "Pace": st.column_config.TextColumn("Pace"),
            "GAP Pace (Flat-Eq)": st.column_config.TextColumn("GAP Pace (Flat-Eq)"),
            "Total Time": st.column_config.TextColumn("Total Time"),
            
            # This hidden numerical metrics loop injects an automatic, highly visible
            # color progress bar gauge directly alongside your text metrics rows!
            "Raw Pace Mins": st.column_config.ProgressColumn(
                "Pace Velocity Scale",
                help="Visual speed efficiency comparison profile (Shorter/Lower is Faster)",
                format="%.2f min",
                min_value=float(df_splits["Raw Pace Mins"].min() * 0.9),
                max_value=float(df_splits["Raw Pace Mins"].max() * 1.1)
            )
        }
        
        # Display our clean, state-aware data visualization matrix
        st.dataframe(
            df_splits,
            column_order=["Split", "Distance", "Pace", "GAP Pace (Flat-Eq)", "Total Time", "Raw Pace Mins"],
            column_config=col_configurations,
            use_container_width=True,
            hide_index=True
        )
        
    except Exception:
        # Secure fallback block displaying plain configurations if column configurations glitch
        st.dataframe(df_splits[display_columns], use_container_width=True, hide_index=True)

    st.markdown("##### 📈 Cumulative Runtime Build-up (Minutes)")
    chart_data = df_splits[["Split", "Cumulative Minutes"]].copy().set_index("Split")
    st.line_chart(chart_data, use_container_width=True)







# ==============================================================================
# EXTENSION: TRAINING ZONE INTENSITY GRAPHIC (WITH TIME DURATION CODES)
# ==============================================================================
def render_zone_octagon_display(matched_run_dict):
    """
    Simulates training zone distributions based on split velocities or pace logs,
    calculates exact time spent in each zone using the overall run duration,
    and generates a native geometric donut ring.
    """
    import pandas as pd
    import streamlit as st
    import altair as alt

    st.markdown("---")
    st.markdown("#### 🛑 Intensity Zone Distribution")

    if not matched_run_dict:
        st.info("Select a workout day to review cardiovascular intensity zone matrices.")
        return

    # 1. Base Setup and Percentage Allocation
    zones = [
        {"name": "Z1: Recovery", "color": "#00ffcc", "pct": 15},
        {"name": "Z2: Endurance", "color": "#00ccff", "pct": 45},
        {"name": "Z3: Tempo", "color": "#ffcc00", "pct": 20},
        {"name": "Z4: Threshold", "color": "#ff6600", "pct": 15},
        {"name": "Z5: Anaerobic", "color": "#ff3333", "pct": 5}
    ]

    # Parse real splits array to distribute percentages dynamically
    raw_splits = matched_run_dict.get("splits", [])
    if isinstance(raw_splits, list) and len(raw_splits) > 0:
        paces = []
        for s in raw_splits:
            p_str = str(s.get("pace", "08:00"))
            try:
                parts = p_str.split(':')
                if len(parts) == 2: 
                    paces.append(int(parts[0])*60 + int(parts[1]))
            except Exception: 
                pass
        
        if len(paces) > 1:
            slowest = max(paces)
            fastest = min(paces)
            span = max(1, slowest - fastest)
            
            z1, z2, z3, z4, z5 = 0, 0, 0, 0, 0
            for p in paces:
                rel = (slowest - p) / span
                if rel < 0.2: z1 += 1
                elif rel < 0.5: z2 += 1
                elif rel < 0.75: z3 += 1
                elif rel < 0.92: z4 += 1
                else: z5 += 1
            
            total = len(paces)
            p1 = int((z1 / total) * 100)
            p2 = int((z2 / total) * 100)
            p3 = int((z3 / total) * 100)
            p4 = int((z4 / total) * 100)
            p5 = 100 - (p1 + p2 + p3 + p4)
            
            z_vals = [p1, p2, p3, p4, p5]
            for idx, z_item in enumerate(zones):
                z_item["pct"] = max(5, z_vals[idx])

    # 2. NEW LOGIC: Parse run duration into total seconds to calculate exact zone times
    duration_str = str(matched_run_dict.get('Duration', '00:00')).strip()
    total_duration_seconds = 0
    
    try:
        time_parts = duration_str.split(':')
        if len(time_parts) == 2:  # MM:SS format
            total_duration_seconds = int(time_parts[0]) * 60 + int(time_parts[1])
        elif len(time_parts) == 3:  # HH:MM:SS format
            total_duration_seconds = int(time_parts[0]) * 3600 + int(time_parts[1]) * 60 + int(time_parts[2])
    except Exception:
        total_duration_seconds = 2400  # Fallback baseline (40 minutes) if parsing fails

    # Helper function to convert seconds back to a nice time string
    def format_seconds_to_clock(secs):
        hrs = secs // 3600
        mins = (secs % 3600) // 60
        secs = secs % 60
        if hrs > 0:
            return f"{hrs:02d}:{mins:02d}:{secs:02d}"
        return f"{mins:02d}:{secs:02d}"

    # 3. Build Dataset for Charting
    chart_rows = []
    for z in zones:
        chart_rows.append({
            "Zone": z["name"],
            "Percentage": z["pct"]
        })
    df_chart = pd.DataFrame(chart_rows)
    # 4. Render Layout Columns Side-by-Side Natively (UPSCALED CHART SIZING)
    col_g1, col_g2 = st.columns([0.5, 0.5])
    
    with col_g1:
        # Increased innerRadius to 45, width/height to 170 for a significantly larger visual display
        donut_chart = alt.Chart(df_chart).mark_arc(innerRadius=45, stroke="#1e222b", strokeWidth=2).encode(
            theta=alt.Theta(field="Percentage", type="quantitative"),
            color=alt.Color(field="Zone", type="nominal", scale=alt.Scale(
                domain=[z["name"] for z in zones],
                range=[z["color"] for z in zones]
            ), legend=None),
            tooltip=["Zone", "Percentage"]
        ).properties(
            width=170,
            height=170
        )
        
        st.altair_chart(donut_chart, use_container_width=True)
        
    with col_g2:
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        for z in zones:
            zone_color = z["color"]
            zone_name = z["name"]
            zone_pct = z["pct"]
            
            # Calculate exact seconds spent in this zone based on its percentage weight
            zone_seconds = int(round(total_duration_seconds * (zone_pct / 100.0)))
            zone_time_str = format_seconds_to_clock(zone_seconds)
            
            st.markdown(
                f"<span style='color:{zone_color}; font-size:18px;'>■</span> "
                f"**{zone_name}**: `{zone_pct}%` ({zone_time_str})", 
                unsafe_allow_html=True
            )


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

