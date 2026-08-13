import streamlit as st
import pandas as pd
import json
import os
import calendar
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import io

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
# Modify these HEX codes anytime to dynamically switch the dashboard theme!
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

def generate_pdf_report(target_df, title_text, unit_abbr, total_miles, total_time, total_elev, view_mode="📅 Grid View", cal_month_name="January", cal_year=2026, cal_df=None):
    """
    Generates a structured, printable PDF document of the currently filtered timeline data.
    If view_mode is '📅 Grid View', it dynamically builds a visual monthly calendar layout.
    Otherwise, it renders an alternating spreadsheet table with intermediate weekly summaries.
    """
    if not REPORTLAB_AVAILABLE:
        return None

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=40, bottomMargin=40)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle', parent=styles['Heading1'], fontSize=18, spaceAfter=4, textColor=colors.HexColor('#1a334d')
    )
    meta_style = ParagraphStyle(
        'DocMeta', parent=styles['Normal'], fontSize=9, spaceAfter=12, textColor=colors.HexColor('#5c6370')
    )
    
    # Header Elements
    story.append(Paragraph(f"<b>Running Performance Log Report</b>", title_style))
    story.append(Paragraph(f"Scope: {title_text} | Exported on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", meta_style))
    story.append(Spacer(1, 8))
    
    # Analyze Data Columns Structure
    elev_cols = [col for col in target_df.columns if 'elev' in col.lower()]
    month_names = list(calendar.month_name)[1:]

    # ==========================================
    # PDF INTERACTIVE CALENDAR GRID ENGINE
    # ==========================================
    if view_mode == "📅 Grid View":
        months_to_loop = range(1, 13) if cal_month_name == "All Months" else [month_names.index(cal_month_name) + 1]
        
        for loop_m in months_to_loop:
            m_name = month_names[loop_m - 1]
            story.append(Paragraph(f"<b>📅 {m_name.upper()} {cal_year}</b>", styles['Heading2']))
            story.append(Spacer(1, 4))
            
            # Inject localized Monthly Inline Summaries for All Months loop
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
            
            # Paragraph Styles mirroring GUI typography palettes
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

    # ==========================================
    # PDF ALTERNATING SPREADSHEET ENGINE
    # ==========================================
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
# ADVANCED VISUALIZATION BUILDERS
# ==========================================
def render_progression_nonagon(endurance_lvl, pace_lvl, hill_lvl):
    """
    Builds and returns a 9-slice polar chart representing progression levels.
    Expects levels between 0 and 3 for each attribute.
    """
    num_slices = 9
    labels = [
        "Endurance L1", "Endurance L2", "Endurance L3",
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
    
    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    
    plt.xticks(angles[:-1], labels, color='#e0e0e0', size=9)
    ax.set_rlabel_position(0)
    plt.yticks([1, 2, 3], ["L1", "L2", "L3"], color="grey", size=8)
    plt.ylim(0, 3)
    
    ax.plot(angles, display_values, color=THEME_CONFIG["NONAGON_LINE"], linewidth=2, linestyle='solid')
    ax.fill(angles, display_values, color=THEME_CONFIG["NONAGON_FILL"], alpha=0.3)
    
    fig.patch.set_facecolor('none')
    ax.set_facecolor('none')
    ax.spines['polar'].set_color('#3e4452')
    ax.grid(color='#3e4452', linestyle='--')
    
    return fig

# ==========================================
# MAIN INTERACTIVE UI DASHBOARD ELEMENT
# ==========================================
def render_dashboard_overview(player):
    """
    Renders an interactive running dashboard featuring:
    - Side-by-side Dual Slider charts (Daily, Monthly, Annual)
    - Miles vs Kilometers unit toggling
    - Custom monthly inline calendar matrix table with selectable activity squares
    """
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
            
            st.bar_chart(
                data=daily_plot_df,
                x='Formatted_Date',
                y='Display_Distance',
                use_container_width=True
            )
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
            st.bar_chart(
                data=monthly_plot_df,
                x='Month_Label',
                y='Display_Distance',
                use_container_width=True
            )
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
            st.bar_chart(
                data=yearly_plot_df,
                x='Year',
                y='Display_Distance',
                use_container_width=True
            )
            st.metric(f"All-Time History Total ({unit_abbr})", f"{yearly_plot_df['Display_Distance'].sum():,.2f} {unit_abbr}")
        else:
            st.caption("No dynamic historical year structures found.")

    show_cal(player=None, external_df=df, unit_abbr=unit_abbr)

def show_cal(player=None, external_df=None, unit_abbr="Mi"):
    """
    Renders an interactive monthly or yearly training performance log structure.
    Supports Grid view (Single Month or All Months), Monthly Spreadsheet view, and Full Year Spreadsheet timelines.
    """
    if "selected_activity_date" not in st.session_state:
        st.session_state.selected_activity_date = None

    if external_df is not None:
        df = external_df
    else:
        raw_activities = []
        if player and hasattr(player, 'history_logs') and player.history_logs:
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
        except Exception:
            pass

    # ==========================================
    # SYNCHRONIZED STATE INITIALIZATION
    # ==========================================
    if "grid_year_dropdown" not in st.session_state:
        st.session_state.grid_year_dropdown = active_year_default
    if "grid_month_dropdown" not in st.session_state:
        st.session_state.grid_month_dropdown = month_names[max(0, min(active_month_default_idx, 11))]
    if "calendar_display_view" not in st.session_state:
        st.session_state.calendar_display_view = "📅 Grid View"

    # View Selector Radio Strip
    st.radio(
        label="Layout Perspective Selector Switch:",
        options=["📅 Grid View", "📊 Spreadsheet View", "📆 Full Year View"],
        key="calendar_display_view",
        horizontal=True
    )
    st.write("")

    sel_col1, sel_col2 = st.columns(2)
    with sel_col1:
        if st.session_state.grid_year_dropdown not in years_available:
            st.session_state.grid_year_dropdown = years_available[0] if years_available else active_year_default
        cal_year = st.selectbox("Select Display Year:", years_available, key="grid_year_dropdown")
    with sel_col2:
        is_year_view = st.session_state.calendar_display_view == "📆 Full Year View"
        
        # Keep month choices structurally identical across all perspectives to completely fix Streamlit's implicit index reset bugs
        month_options = ["All Months"] + month_names
        
        if st.session_state.grid_month_dropdown not in month_options:
            st.session_state.grid_month_dropdown = month_options[1]
            
        cal_month_name = st.selectbox(
            label="Select Display Month:",
            options=month_options,
            key="grid_month_dropdown",
            disabled=is_year_view
        )

    if cal_month_name == "All Months":
        cal_month = 1
    else:
        cal_month = month_names.index(cal_month_name) + 1

    # Define Navigation Offsets based on Selected Horizon Mode
    if is_year_view or cal_month_name == "All Months":
        prev_year, prev_month_idx = cal_year - 1, 0
        next_year, next_month_idx = cal_year + 1, 0
    else:
        if cal_month == 1:
            prev_month, prev_year = 12, cal_year - 1
        else:
            prev_month, prev_year = cal_month - 1, cal_year
        if cal_month == 12:
            next_month, next_year = 1, cal_year + 1
        else:
            next_month, next_year = cal_month + 1, cal_year
        prev_month_idx, next_month_idx = prev_month - 1, next_month - 1

    min_date = cal_df['Date'].min()
    max_date = cal_df['Date'].max()

    if is_year_view or cal_month_name == "All Months":
        has_prev = (prev_year >= min_date.year) if pd.notna(min_date) else False
        has_next = (next_year <= max_date.year) if pd.notna(max_date) else False
    else:
        has_prev = (prev_year > min_date.year) or (prev_year == min_date.year and prev_month >= min_date.month) if pd.notna(min_date) else False
        has_next = (next_year < max_date.year) or (next_year == max_date.year and next_month <= max_date.month) if pd.notna(max_date) else False

    def handle_navigation_callback(target_year, target_month_name):
        st.session_state.grid_year_dropdown = target_year
        st.session_state.grid_month_dropdown = target_month_name

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
                transition: all 0.2s ease !important;
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
                box-shadow: 0px 0px 8px rgba(0, 255, 254, 0.2) !important;
            }}

            div[data-testid="stVerticalBlock"]:has(.run-odd-marker) div[data-testid="stButton"] button {{
                background-color: {THEME_CONFIG["RUN_ODD_BG"]} !important;
                color: {THEME_CONFIG["RUN_DAY_TEXT"]} !important;
                border: 2px solid {THEME_CONFIG["RUN_DAY_BORDER"]} !important;
                font-weight: bold !important;
                box-shadow: 0px 0px 8px rgba(0, 255, 254, 0.2) !important;
            }}
            
            div[data-testid="stColumn"] div[data-testid="stButton"] button:hover {{
                transform: translateY(-2px) !important;
                cursor: pointer;
            }}

            .spreadsheet-table {{
                width: 100%;
                border-collapse: collapse;
                color: #ffffff;
                margin-top: 10px;
                font-size: 11.5px;
                font-family: monospace;
            }}
            .spreadsheet-table th {{
                background-color: #2c313c !important;
                color: #00ffcc !important;
                text-align: left;
                padding: 10px;
                font-weight: bold;
                text-transform: uppercase;
                border-bottom: 2px solid #3e4452;
            }}
            .spreadsheet-table td {{
                padding: 8px 10px;
                border-bottom: 1px solid #232731;
                vertical-align: middle;
            }}
            .spreadsheet-table tr.day-row:nth-child(even) {{
                background-color: #1e222b !important;
            }}
            .spreadsheet-table tr.day-row:nth-child(odd) {{
                background-color: #242935 !important;
            }}
            .spreadsheet-table tr.weekly-total-row {{
                background-color: #0f3930 !important;
                color: #00ffcc !important;
                font-weight: bold !important;
                border-top: 2px solid #00ffcc !important;
                border-bottom: 2px solid #00ffcc !important;
            }}
            .spreadsheet-table tr.monthly-total-row {{
                background-color: #1a334d !important;
                color: #00ffff !important;
                font-weight: bold !important;
                border-top: 2px solid #00ffff !important;
                border-bottom: 2px solid #00ffff !important;
            }}
            .spreadsheet-table tr.yearly-total-row {{
                background-color: #332300 !important;
                color: #ffcc00 !important;
                font-weight: bold !important;
                border-top: 3px solid #ffcc00 !important;
                border-bottom: 3px solid #ffcc00 !important;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )
        
        with st.container():
            st.markdown("<div class='calendar-bg-trigger'></div>", unsafe_allow_html=True)
            
            # ==========================================
            # DYNAMIC FILTER AGGREGATION LOOKUPS
            # ==========================================
            if is_year_view or cal_month_name == "All Months":
                target_df = cal_df[cal_df['Year_Int'] == cal_year]
                current_header_title = f"Full Year Timeline: {cal_year}"
                nav_target_month = cal_month_name
            else:
                target_df = cal_df[(cal_df['Year_Int'] == cal_year) & (cal_df['Month_Int'] == cal_month)]
                current_header_title = f"{month_names[cal_month - 1]} {cal_year}"
                nav_target_month = month_names[prev_month_idx]
                
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
                        if len(parts) == 3:
                            total_seconds += int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                        elif len(parts) == 2:
                            total_seconds += int(parts[0]) * 60 + int(parts[1])
                    except ValueError:
                        pass
                        
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
            
            # ==========================================
            # REPORT EXPORT UTILITY BAR
            # ==========================================
            if REPORTLAB_AVAILABLE:
                pdf_data_stream = generate_pdf_report(
                    target_df, current_header_title, unit_abbr, 
                    total_miles_aggregated, total_time_str, total_elevation_aggregated,
                    view_mode=st.session_state.calendar_display_view,
                    cal_month_name=cal_month_name,
                    cal_year=cal_year,
                    cal_df=cal_df
                )
                if pdf_data_stream:
                    st.download_button(
                        label="📄 Export Data to PDF Report",
                        data=pdf_data_stream,
                        file_name=f"running_report_{cal_year}_{cal_month_name.replace(' ', '_')}.pdf",
                        mime="application/pdf"
                    )
            else:
                st.info("💡 To enable document exports, please execute `pip install reportlab` in your local environment setup.")

            # ==========================================
            # CALENDAR TABLE CONTROL NAVIGATION STRIP
            # ==========================================
            nav_col1, nav_col2, nav_col3 = st.columns([0.15, 0.7, 0.15])
            with nav_col1:
                if has_prev:
                    st.button(
                        "◀", 
                        key="prev_navigation_btn", 
                        use_container_width=True,
                        on_click=handle_navigation_callback,
                        args=(prev_year, cal_month_name)
                    )
                else:
                    st.write("")
                    
            with nav_col2:
                st.markdown(f"<h3 style='text-align: center; color: white; margin-top: 5px; margin-bottom: 5px; letter-spacing: 1px;'>{current_header_title}</h3>", unsafe_allow_html=True)
                
            with nav_col3:
                if has_next:
                    st.button(
                        "▶", 
                        key="next_navigation_btn", 
                        use_container_width=True,
                        on_click=handle_navigation_callback,
                        args=(next_year, cal_month_name)
                    )
                else:
                    st.write("")

            # ==========================================
            # FULL YEAR PERSPECTIVE RENDERING PATTERN
            # ==========================================
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
                        week_dist = 0.0
                        week_seconds = 0
                        week_elev = 0.0
                        week_rows_buffer = ""
                        
                        for day in week:
                            if day == 0:
                                continue
                            week_has_days = True
                            target_date_str = f"{cal_year}-{m_idx:02d}-{day:02d}"
                            day_runs = cal_df[cal_df['Formatted_Date'] == target_date_str]
                            
                            if not day_runs.empty:
                                run_row = day_runs.iloc[0]
                                run_dist = run_row['Display_Distance']
                                run_time = run_row.get('Duration', '--:--')
                                run_pace = f"{run_row.get('pace', '—')} min/{unit_abbr.lower()}"
                                
                                day_elevation = 0.0
                                if run_elev_cols := [c for c in m_df.columns if 'elev' in c.lower()]:
                                    raw_elev_val = run_row.get(run_elev_cols[0], "0")
                                    cleaned_run_elev = ''.join(c for c in str(raw_elev_val) if c.isdigit() or c == '.')
                                    parsed_elev = pd.to_numeric(cleaned_run_elev, errors='coerce')
                                    if pd.notna(parsed_elev):
                                        day_elevation = parsed_elev
                                    
                                week_dist += run_dist
                                m_dist += run_dist
                                week_elev += day_elevation
                                m_elev += day_elevation
                                
                                if isinstance(run_time, str) and ':' in run_time:
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
                                        
                                week_rows_buffer += f"<tr class='day-row'><td><b>{target_date_str}</b></td><td style='color: #00ffff; font-weight: bold;'>🏃 RUN</td><td>{run_dist:.2f} {unit_abbr}</td><td>{run_time}</td><td>{run_pace}</td><td>{day_elevation:,.0f} ft</td></tr>"
                            else:
                                week_rows_buffer += f"<tr class='day-row'><td>{target_date_str}</td><td style='color: #ffcc00; font-weight: bold;'>🧘 REST DAY</td><td style='color: #7e8794;'>—</td><td style='color: #7e8794;'>—</td><td style='color: #7e8794;'>—</td><td style='color: #7e8794;'>—</td></tr>"
                        
                        if week_has_days:
                            table_body_html += week_rows_buffer
                            
                            w_hours = week_seconds // 3600
                            w_mins = (week_seconds % 3600) // 60
                            w_time_str = f"{w_hours}h {w_mins}m" if w_hours > 0 else f"{w_mins}m"
                            if week_seconds == 0:
                                w_time_str = "—"
                                
                            table_body_html += f"<tr class='weekly-total-row'><td>WEEK {w_idx + 1} TOTALS</td><td>📊 SUMMARY</td><td>{week_dist:.2f} {unit_abbr}</td><td>{w_time_str}</td><td>—</td><td>{week_elev:,.0f} ft</td></tr>"
                    
                    m_hours = m_seconds // 3600
                    m_mins = (m_seconds % 3600) // 60
                    m_time_str = f"{m_hours}h {m_mins}m" if m_hours > 0 else f"{m_mins}m"
                    if m_seconds == 0:
                        m_time_str = "—"
                        
                    table_body_html += f"<tr class='monthly-total-row'><td>{m_name.upper()} TOTALS</td><td>📈 MONTH SUMMARY</td><td>{m_dist:.2f} {unit_abbr}</td><td>{m_time_str}</td><td>—</td><td>{m_elev:,.0f} ft</td></tr>"
                
                y_hours = total_seconds // 3600
                y_mins = (total_seconds % 3600) // 60
                y_time_str = f"{y_hours}h {y_mins}m" if y_hours > 0 else f"{y_mins}m"
                if total_seconds == 0:
                    y_time_str = "—"
                table_body_html += f"<tr class='yearly-total-row'><td>🏆 {cal_year} YEAR TOTALS</td><td>🌟 GRAND OVERVIEW</td><td>{total_miles_aggregated:.2f} {unit_abbr}</td><td>{y_time_str}</td><td>—</td><td>{total_elevation_aggregated:,.0f} ft</td></tr>"
                
                year_html = f"<table class='spreadsheet-table'><thead><tr><th>Run Date</th><th>Status</th><th>Distance</th><th>Duration</th><th>Average Pace</th><th>Ascent Gain</th></tr></thead><tbody>{table_body_html}</tbody></table>"
                st.markdown(year_html, unsafe_allow_html=True)

            # ==========================================
            # MONTHLY SPREADSHEET perspective LAYER
            # ==========================================
            elif st.session_state.calendar_display_view == "📊 Spreadsheet View":
                table_body_html = ""
                months_to_loop = range(1, 13) if cal_month_name == "All Months" else [cal_month]
                
                for loop_m in months_to_loop:
                    if cal_month_name == "All Months":
                        table_body_html += f"<tr><td colspan='6' style='background-color: #1a1c23; color: #00ffcc; font-weight: bold; padding: 10px; text-transform: uppercase;'>📅 {month_names[loop_m - 1].upper()} LOGS</td></tr>"
                        
                    cal_matrix = calendar.monthcalendar(cal_year, loop_m)
                    
                    for w_idx, week in enumerate(cal_matrix):
                        week_has_days = False
                        week_dist = 0.0
                        week_seconds = 0
                        week_elev = 0.0
                        week_rows_buffer = ""
                        
                        for day in week:
                            if day == 0:
                                continue
                            week_has_days = True
                            target_date_str = f"{cal_year}-{loop_m:02d}-{day:02d}"
                            day_runs = cal_df[cal_df['Formatted_Date'] == target_date_str]
                            
                            if not day_runs.empty:
                                run_row = day_runs.iloc[0]
                                run_dist = run_row['Display_Distance']
                                run_time = run_row.get('Duration', '--:--')
                                run_pace = f"{run_row.get('pace', '—')} min/{unit_abbr.lower()}"
                                
                                day_elevation = 0.0
                                if elev_columns:
                                    raw_elev_val = run_row.get(elev_columns[0], "0")
                                    cleaned_run_elev = ''.join(c for c in str(raw_elev_val) if c.isdigit() or c == '.')
                                    parsed_elev = pd.to_numeric(cleaned_run_elev, errors='coerce')
                                    if pd.notna(parsed_elev):
                                        day_elevation = parsed_elev
                                    
                                week_dist += run_dist
                                week_elev += day_elevation
                                
                                if isinstance(run_time, str) and ':' in run_time:
                                    parts = run_time.split(':')
                                    try:
                                        if len(parts) == 3:
                                            week_seconds += int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                                        elif len(parts) == 2:
                                            week_seconds += int(parts[0]) * 60 + int(parts[1])
                                    except ValueError:
                                        pass
                                
                                week_rows_buffer += f"<tr class='day-row'><td><b>{target_date_str}</b></td><td style='color: #00ffff; font-weight: bold;'>🏃 RUN</td><td>{run_dist:.2f} {unit_abbr}</td><td>{run_time}</td><td>{run_pace}</td><td>{day_elevation:,.0f} ft</td></tr>"
                            else:
                                week_rows_buffer += f"<tr class='day-row'><td>{target_date_str}</td><td style='color: #ffcc00; font-weight: bold;'>🧘 REST DAY</td><td style='color: #7e8794;'>—</td><td style='color: #7e8794;'>—</td><td style='color: #7e8794;'>—</td><td style='color: #7e8794;'>—</td></tr>"
                        
                        if week_has_days:
                            table_body_html += week_rows_buffer
                            
                            w_hours = week_seconds // 3600
                            w_mins = (week_seconds % 3600) // 60
                            w_time_str = f"{w_hours}h {w_mins}m" if w_hours > 0 else f"{w_mins}m"
                            if week_seconds == 0:
                                w_time_str = "—"
                                
                            table_body_html += f"<tr class='weekly-total-row'><td>WEEK {w_idx + 1} TOTALS</td><td>📊 SUMMARY</td><td>{week_dist:.2f} {unit_abbr}</td><td>{w_time_str}</td><td>—</td><td>{week_elev:,.0f} ft</td></tr>"
                
                spreadsheet_html = f"<table class='spreadsheet-table'><thead><tr><th>Calendar Date</th><th>Activity Status</th><th>Distance</th><th>Duration Time</th><th>Overall Pace</th><th>Climbed Elev</th></tr></thead><tbody>{table_body_html}</tbody></table>"
                st.markdown(spreadsheet_html, unsafe_allow_html=True)

            # ==========================================
            # LAYOUT CONTEXT PIPING FOR CLASSIC GRID MODE
            # ==========================================
            else:
                months_to_loop = range(1, 13) if cal_month_name == "All Months" else [cal_month]
                
                for loop_m in months_to_loop:
                    if cal_month_name == "All Months":
                        st.markdown(f"<h4 style='color: #00ffcc; border-bottom: 1px solid #3e4452; padding-top: 20px; padding-bottom: 5px; margin-bottom: 8px;'>🗓️ {month_names[loop_m - 1]}</h4>", unsafe_allow_html=True)
                        
                        # Generate Month-Specific Aggregation Strip for the full year grid loop
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
                                    if len(parts) == 3:
                                        m_seconds += int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                                    elif len(parts) == 2:
                                        m_seconds += int(parts[0]) * 60 + int(parts[1])
                                except ValueError:
                                    pass
                                    
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

    with main_layout_col2:
        if st.session_state.selected_activity_date:
            active_date = st.session_state.selected_activity_date
            matched_runs = df[df['Formatted_Date'] == active_date]
            
            if not matched_runs.empty:
                matched_run = matched_runs.iloc[0].to_dict()
                st.markdown(f"### 📊 Run Summary: {active_date}")
                
                if "splits" in matched_run and isinstance(matched_run["splits"], list) and len(matched_run["splits"]) > 0:
                    splits_df = pd.DataFrame(matched_run["splits"])
                    splits_df['Split Mile'] = "M" + splits_df['split_num'].astype(str)
                    splits_df['Pace (Minutes)'] = splits_df['pace'].apply(pace_str_to_minutes)
                    
                    st.caption("⏱️ Lap Split Profiles (Shorter bars are faster)")
                    st.bar_chart(data=splits_df, x='Split Mile', y='Pace (Minutes)', use_container_width=True)
                    
                    fastest_idx = splits_df['Pace (Minutes)'].idxmin()
                    slowest_idx = splits_df['Pace (Minutes)'].idxmax()
                    
                    st.success(f"⚡ **Fastest Lap:** {splits_df.loc[fastest_idx, 'Split Mile']} ({splits_df.loc[fastest_idx, 'pace']})")
                    st.error(f"🐢 **Slowest Lap:** {splits_df.loc[slowest_idx, 'split_num']} ({splits_df.loc[slowest_idx, 'pace']})")
                    st.write("---")
                else:
                    st.info("No split milestones parsed for this workout data.")
                
                st.metric("Total Distance", f"{matched_run['Display_Distance']:.2f} {unit_abbr}")
                st.metric("Duration", matched_run.get('Duration', 'N/A'))
                if 'pace' in matched_run:
                    st.metric("Average Overall Pace", f"{matched_run['pace']} min/{unit_abbr.lower()}")
                    
                # Run Specific Elevation Gain Calculation Layer
                run_elev_cols = [col for col in matched_runs.columns if 'elev' in col.lower()]
                if run_elev_cols:
                    raw_elev_val = matched_run.get(run_elev_cols[0], "0")
                    cleaned_run_elev = ''.join(c for c in str(raw_elev_val) if c.isdigit() or c == '.')
                    single_run_elevation = pd.to_numeric(cleaned_run_elev, errors='coerce')
                    if pd.notna(single_run_elevation):
                        st.metric("Elevation Gain", f"{single_run_elevation:,.0f} ft")
                    else:
                        st.metric("Elevation Gain", "0 ft")
                else:
                    st.metric("Elevation Gain", "N/A")
            else:
                st.caption("Select a run date inside the grid to load data.")
        else:
            st.info("👈 Click any item inside the calendar workspace to inspect individual activity split profiles.")


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
            
            st.bar_chart(
                data=yearly_plot_df,
                x='Year',
                y='Display_Distance',
                use_container_width=True
            )
            st.metric(f"All-Time History Total ({unit_abbr})", f"{df['Display_Distance'].sum():,.2f} {unit_abbr}")
        else:
            st.caption("No dynamic historical year structures found.")
