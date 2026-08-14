import streamlit as st
import pandas as pd
import json
import os
import calendar
from datetime import datetime, timedelta
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
# PATCH EXTENSION: RUN LAP METRICS WORKSPACE
# ==========================================
def show_run_lap_breakdown(run_distance, average_pace_str):
    """
    Calculates 1-mile splits and renders them in a neat Streamlit table.
    Bound contextually to the right of the calendar view under the summary card.
    Formats Cumulative Time to HH:MM:SS if duration exceeds 60 minutes.
    """
    import pandas as pd
    import streamlit as st
    
    st.markdown("---")
    st.markdown("#### ⏱ Incremental Lap Split Analysis")
    
    if run_distance <= 0 or not average_pace_str or average_pace_str == "—":
        st.info("No distance or pace metrics available to generate split profiles.")
        return

    try:
        parts = str(average_pace_str).strip().split(':')
        pace_seconds = int(parts) * 60 + int(parts) if len(parts) == 2 else float(average_pace_str) * 60
    except Exception:
        st.error("Unable to parse activity pace metrics configuration.")
        return

    lap_records = []
    cumulative_seconds = 0.0
    remaining_distance = run_distance
    lap_index = 1

    while remaining_distance > 0:
        if remaining_distance >= 1.0:
            current_lap_dist = 1.0
            remaining_distance -= 1.0
        else:
            current_lap_dist = remaining_distance
            remaining_distance = 0.0

        lap_seconds = current_lap_dist * pace_seconds
        cumulative_seconds += lap_seconds

        # Standard lap split parsing (always MM:SS since a single mile is under an hour)
        split_mins = int(lap_seconds) // 60
        split_secs = int(round(lap_seconds % 60))
        if split_secs == 60:
            split_mins += 1
            split_secs = 0
        split_time_str = f"{split_mins:02d}:{split_secs:02d}"

        # Dynamic overall runtime helper formatting logic
        def format_cumulative_time(total_secs):
            total_secs_rounded = int(round(total_secs))
            hrs = total_secs_rounded // 3600
            mins = (total_secs_rounded % 3600) // 60
            secs = total_secs_rounded % 60
            
            # Smart clock toggle switch based on 1-hour marker limits
            if hrs > 0:
                return f"{hrs:02d}:{mins:02d}:{secs:02d}"
            else:
                return f"{mins:02d}:{secs:02d}"

        lap_records.append({
            "Lap #": f"Lap {lap_index}" if current_lap_dist == 1.0 else f"Lap {lap_index} (Final)",
            "Distance Included": f"{current_lap_dist:.2f} mi",
            "Lap Split Time": split_time_str,
            "Cumulative Run Time": format_cumulative_time(cumulative_seconds)
        })
        lap_index += 1

    st.dataframe(pd.DataFrame(lap_records), use_container_width=True, hide_index=True)


def render_dashboard_overview(player):
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

    show_cal(player=None, external_df=df, unit_abbr=unit_abbr)

def show_cal(player=None, external_df=None, unit_abbr="Mi"):
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
        cal_year = st.selectbox("Select Display Year:", years_available, key="grid_year_dropdown")
    with sel_col2:
        is_year_view = st.session_state.calendar_display_view == "📆 Full Year View"
        month_options = ["All Months"] + month_names
        if st.session_state.grid_month_dropdown not in month_options:
            st.session_state.grid_month_dropdown = month_options[1]
        cal_month_name = st.selectbox(label="Select Display Month:", options=month_options, key="grid_month_dropdown", disabled=is_year_view)

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

            nav_col1, nav_col2, nav_col3 = st.columns([0.15, 0.7, 0.15])
            with nav_col1:
                if has_prev: st.button("◀", key="prev_navigation_btn", use_container_width=True, on_click=handle_navigation_callback, args=(prev_year, cal_month_name))
            with nav_col2:
                st.markdown(f"<h3 style='text-align: center; color: white; margin-top: 5px; margin-bottom: 5px; letter-spacing: 1px;'>{current_header_title}</h3>", unsafe_allow_html=True)
            with nav_col3:
                if has_next: st.button("▶", key="next_navigation_btn", use_container_width=True, on_click=handle_navigation_callback, args=(next_year, cal_month_name))

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
                                run_pace = f"{run_row.get('pace', '—')} min/{unit_abbr.lower()}"
                                
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
                                run_pace = f"{run_row.get('pace', '—')} min/{unit_abbr.lower()}"
                                
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
# PATCH EXTENSION: RUN LAP METRICS WORKSPACE
# ==========================================
def show_run_lap_breakdown(run_distance, average_pace_str):
    """
    Calculates 1-mile splits and renders them in a neat Streamlit table.
    Bound contextually to the right of the calendar view under the summary card.
    Formats Cumulative Time to HH:MM:SS if duration exceeds 60 minutes.
    """
    import pandas as pd
    import streamlit as st
    
    st.markdown("---")
    st.markdown("#### ⏱ Incremental Lap Split Analysis")
    
    if run_distance <= 0 or not average_pace_str or average_pace_str == "—":
        st.info("No distance or pace metrics available to generate split profiles.")
        return

    try:
        parts = str(average_pace_str).strip().split(':')
        pace_seconds = int(parts) * 60 + int(parts) if len(parts) == 2 else float(average_pace_str) * 60
    except Exception:
        st.error("Unable to parse activity pace metrics configuration.")
        return

    lap_records = []
    cumulative_seconds = 0.0
    remaining_distance = run_distance
    lap_index = 1

    while remaining_distance > 0:
        if remaining_distance >= 1.0:
            current_lap_dist = 1.0
            remaining_distance -= 1.0
        else:
            current_lap_dist = remaining_distance
            remaining_distance = 0.0

        lap_seconds = current_lap_dist * pace_seconds
        cumulative_seconds += lap_seconds

        # Standard lap split parsing (always MM:SS since a single mile is under an hour)
        split_mins = int(lap_seconds) // 60
        split_secs = int(round(lap_seconds % 60))
        if split_secs == 60:
            split_mins += 1
            split_secs = 0
        split_time_str = f"{split_mins:02d}:{split_secs:02d}"

        # Dynamic overall runtime helper formatting logic
        def format_cumulative_time(total_secs):
            total_secs_rounded = int(round(total_secs))
            hrs = total_secs_rounded // 3600
            mins = (total_secs_rounded % 3600) // 60
            secs = total_secs_rounded % 60
            
            # Smart clock toggle switch based on 1-hour marker limits
            if hrs > 0:
                return f"{hrs:02d}:{mins:02d}:{secs:02d}"
            else:
                return f"{mins:02d}:{secs:02d}"

        lap_records.append({
            "Lap #": f"Lap {lap_index}" if current_lap_dist == 1.0 else f"Lap {lap_index} (Final)",
            "Distance Included": f"{current_lap_dist:.2f} mi",
            "Lap Split Time": split_time_str,
            "Cumulative Run Time": format_cumulative_time(cumulative_seconds)
        })
        lap_index += 1

    st.dataframe(pd.DataFrame(lap_records), use_container_width=True, hide_index=True)


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