import streamlit as st
import pandas as pd
import json
import os
import calendar
from datetime import datetime


import numpy as np
import matplotlib.pyplot as plt




def show_cal(player):

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
            
    # Conversion multiplier variables
    is_km = "Kilometers (km)"
    unit_abbr = "Km" if is_km else "Mi"
    # Apply conversions across the primary tracking vectors
    df['Display_Distance'] = df['Distance (Miles)'] * (1.60934 if is_km else 1.0)


        # ==========================================
    # GENERATE CUSTOM CALENDAR WITH BORDERS & SIDE INFO
    # ==========================================
    st.write("---")
    st.subheader("📅 Training Calendar")

    qp = st.query_params
    if "cal_select" in qp:
        st.session_state.selected_activity_date = qp["cal_select"]

    cal_df = df.copy()
    cal_df['Year_Int'] = cal_df['Date'].dt.year
    cal_df['Month_Int'] = cal_df['Date'].dt.month
    years_available = sorted(cal_df['Year_Int'].unique(), reverse=True)
    month_names = list(calendar.month_name)[1:]

    # CRITICAL SECURITY FIX: Explicitly unpack index [0] to extract a single numeric year integer value instead of the list object
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

    sel_col1, sel_col2 = st.columns(2)
    with sel_col1:
        y_index = years_available.index(active_year_default) if active_year_default in years_available else 0
        cal_year = st.selectbox("Year Filter:", years_available, index=y_index)
    with sel_col2:
        cal_month_name = st.selectbox("Month Filter:", month_names, index=max(0, min(active_month_default_idx, 11)))

    cal_month = month_names.index(cal_month_name) + 1

    main_layout_col1, main_layout_col2 = st.columns([1.3, 0.7])

    with main_layout_col1:
        html_bits = []
        html_bits.append("<style>")
        html_bits.append(".calendar-container { border: 2px solid #888888; border-radius: 8px; padding: 12px; background-color: #2D3136; font-family: inherit; }")
        html_bits.append(".calendar-grid { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 6px; text-align: center; }")
        html_bits.append(".day-header { font-weight: bold; font-size: 14px; color: #FFFFFF; padding-bottom: 6px; border-bottom: 2px solid #00FFCC; }")
        html_bits.append(".cal-cell { border-radius: 4px; padding: 6px 2px; min-height: 58px; font-size: 12px; display: flex; flex-direction: column; justify-content: space-between; align-items: center; border: 1px solid #555555; box-sizing: border-box; }")
        html_bits.append(".even-day { background-color: #4E545C; color: #FFFFFF !important; }")
        html_bits.append(".odd-day { background-color: #636B75; color: #FFFFFF !important; }")
        html_bits.append(".active-run-link { text-decoration: none !important; color: #00FFFF !important; font-weight: bold; width: 100%; height: 100%; display: flex; flex-direction: column; justify-content: space-between; }")
        html_bits.append(".active-run-cell { border: 2px solid #00FFFF; background-color: #1A3D38 !important; box-shadow: 0px 0px 8px rgba(0, 255, 255, 0.4); }")
        html_bits.append(".empty-cell { background: transparent; border: none; min-height: 58px; }")
        html_bits.append(".metric-text { font-size: 11px; color: #E0E0E0; font-weight: bold; margin-top: 2px; }")
        html_bits.append("</style>")
        html_bits.append("<div class='calendar-container'><div class='calendar-grid'>")

        days_headers = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for day_name in days_headers:
            html_bits.append(f"<div class='day-header'>{day_name}</div>")

        cal_matrix = calendar.monthcalendar(cal_year, cal_month)

        for week in cal_matrix:
            for idx, day in enumerate(week):
                if day == 0:
                    html_bits.append("<div class='empty-cell'></div>")
                else:
                    target_date_str = f"{cal_year}-{cal_month:02d}-{day:02d}"
                    day_runs = cal_df[cal_df['Formatted_Date'] == target_date_str]
                    color_class = "even-day" if day % 2 == 0 else "odd-day"

                    if not day_runs.empty:
                        run_row = day_runs.iloc[0]
                        run_dist = run_row['Display_Distance']
                        run_time = run_row.get('Duration', '--:--')

                        html_bits.append(f"<div class='cal-cell active-run-cell'><a class='active-run-link' href='?cal_select={target_date_str}' target='_self'><div>{day}</div><div class='metric-text'>{run_dist:.1f}{unit_abbr}</div><div class='metric-text'>{run_time}</div></a></div>")
                    else:
                        html_bits.append(f"<div class='cal-cell {color_class}'><span style='font-weight: 500;'>{day}</span><span style='color: transparent; font-size:9px;'>-</span><span style='color: transparent; font-size:9px;'>-</span></div>")

        html_bits.append("</div></div>")

        full_html = "".join(html_bits)
        st.markdown(full_html, unsafe_allow_html=True)

    # ==========================================
    # RIGHT SIDE COLUMN: RUN SUMMARY WITH GRAPH ABOVE STATS
    # ==========================================
    with main_layout_col2:
        if st.session_state.selected_activity_date:
            active_date = st.session_state.selected_activity_date
            matched_runs = df[df['Formatted_Date'] == active_date]

            if not matched_runs.empty:
                matched_run = matched_runs.iloc[0].to_dict()
                st.markdown(f"### 📊 Run Summary: {active_date}")

                # A. BAR CHART PLOTTED FIRST (ABOVE DATA MATRIX)
                if "splits" in matched_run and isinstance(matched_run["splits"], list) and len(matched_run["splits"]) > 0:
                    splits_df = pd.DataFrame(matched_run["splits"])
                    splits_df['Split Mile'] = "M" + splits_df['split_num'].astype(str)
                    splits_df['Pace (Minutes)'] = splits_df['pace'].apply(pace_str_to_minutes)

                    st.caption("⏱️ Lap Split Profiles (Shorter bars are faster)")
                    st.bar_chart(data=splits_df, x='Split Mile', y='Pace (Minutes)', use_container_width=True)

                    fastest_idx = splits_df['Pace (Minutes)'].idxmin()
                    slowest_idx = splits_df['Pace (Minutes)'].idxmax()

                    st.success(f"⚡ **Fastest Lap:** {splits_df.loc[fastest_idx, 'Split Mile']} ({splits_df.loc[fastest_idx, 'pace']})")
                    st.error(f"🐢 **Slowest Lap:** {splits_df.loc[slowest_idx, 'Split Mile']} ({splits_df.loc[slowest_idx, 'pace']})")
                    st.write("---")
                else:
                    st.info("No split milestones parsed for this workout data.")

                # B. TOTAL DISTANCE, DURATION, AND PACE CARD BLOCK UNDERNEATH
                st.metric("Total Distance", f"{matched_run['Display_Distance']:.2f} {unit_abbr}")
                st.metric("Duration", matched_run.get('Duration', 'N/A'))
                if 'pace' in matched_run:
                    st.metric("Average Overall Pace", f"{matched_run['pace']} min/{unit_abbr.lower()}")
            else:
                st.caption("Select a run date inside the grid to load data.")
        else:
            st.info("👈 Click any bright teal calendar square showing run text data to inspect lap metrics.")







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
#    # ==========================================
#    # GENERATE CUSTOM CALENDAR WITH BORDERS & SIDE INFO
#    # ==========================================
#    st.write("---")
#    st.subheader("📅 Training Calendar")
#    
#    qp = st.query_params
#    if "cal_select" in qp:
#        st.session_state.selected_activity_date = qp["cal_select"]
#
#    cal_df = df.copy()
#    cal_df['Year_Int'] = cal_df['Date'].dt.year
#    cal_df['Month_Int'] = cal_df['Date'].dt.month
#    years_available = sorted(cal_df['Year_Int'].unique(), reverse=True)
#    month_names = list(calendar.month_name)[1:]
#
#    # CRITICAL SECURITY FIX: Explicitly unpack index [0] to extract a single numeric year integer value instead of the list object
#    active_year_default = years_available[0] if years_available else datetime.now().year
#    raw_month_max = cal_df[cal_df['Year_Int'] == active_year_default]['Month_Int'].max()
#    active_month_default_idx = int(raw_month_max) - 1 if pd.notna(raw_month_max) else 0
#
#    if st.session_state.selected_activity_date:
#        try:
#            parsed_dt = datetime.strptime(st.session_state.selected_activity_date, '%Y-%m-%d')
#            if parsed_dt.year in years_available:
#                active_year_default = parsed_dt.year
#                active_month_default_idx = parsed_dt.month - 1
#        except Exception:
#            pass
#
#    sel_col1, sel_col2 = st.columns(2)
#    with sel_col1:
#        y_index = years_available.index(active_year_default) if active_year_default in years_available else 0
#        cal_year = st.selectbox("Year Filter:", years_available, index=y_index)
#    with sel_col2:
#        cal_month_name = st.selectbox("Month Filter:", month_names, index=max(0, min(active_month_default_idx, 11)))
#    
#    cal_month = month_names.index(cal_month_name) + 1
#
#    main_layout_col1, main_layout_col2 = st.columns([1.3, 0.7])
#
#    with main_layout_col1:
#        html_bits = []
#        html_bits.append("<style>")
#        html_bits.append(".calendar-container { border: 2px solid #888888; border-radius: 8px; padding: 12px; background-color: #2D3136; font-family: inherit; }")
#        html_bits.append(".calendar-grid { display: grid; grid-template-columns: repeat(7, minmax(0, 1fr)); gap: 6px; text-align: center; }")
#        html_bits.append(".day-header { font-weight: bold; font-size: 14px; color: #FFFFFF; padding-bottom: 6px; border-bottom: 2px solid #00FFCC; }")
#        html_bits.append(".cal-cell { border-radius: 4px; padding: 6px 2px; min-height: 58px; font-size: 12px; display: flex; flex-direction: column; justify-content: space-between; align-items: center; border: 1px solid #555555; box-sizing: border-box; }")
#        html_bits.append(".even-day { background-color: #4E545C; color: #FFFFFF !important; }")
#        html_bits.append(".odd-day { background-color: #636B75; color: #FFFFFF !important; }")
#        html_bits.append(".active-run-link { text-decoration: none !important; color: #00FFFF !important; font-weight: bold; width: 100%; height: 100%; display: flex; flex-direction: column; justify-content: space-between; }")
#        html_bits.append(".active-run-cell { border: 2px solid #00FFFF; background-color: #1A3D38 !important; box-shadow: 0px 0px 8px rgba(0, 255, 255, 0.4); }")
#        html_bits.append(".empty-cell { background: transparent; border: none; min-height: 58px; }")
#        html_bits.append(".metric-text { font-size: 11px; color: #E0E0E0; font-weight: bold; margin-top: 2px; }")
#        html_bits.append("</style>")
#        html_bits.append("<div class='calendar-container'><div class='calendar-grid'>")
#
#        days_headers = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
#        for day_name in days_headers:
#            html_bits.append(f"<div class='day-header'>{day_name}</div>")
#
#        cal_matrix = calendar.monthcalendar(cal_year, cal_month)
#        
#        for week in cal_matrix:
#            for idx, day in enumerate(week):
#                if day == 0:
#                    html_bits.append("<div class='empty-cell'></div>")
#                else:
#                    target_date_str = f"{cal_year}-{cal_month:02d}-{day:02d}"
#                    day_runs = cal_df[cal_df['Formatted_Date'] == target_date_str]
#                    color_class = "even-day" if day % 2 == 0 else "odd-day"
#                    
#                    if not day_runs.empty:
#                        run_row = day_runs.iloc[0]
#                        run_dist = run_row['Display_Distance']
#                        run_time = run_row.get('Duration', '--:--')
#                        
#                        html_bits.append(f"<div class='cal-cell active-run-cell'><a class='active-run-link' href='?cal_select={target_date_str}' target='_self'><div>{day}</div><div class='metric-text'>{run_dist:.1f}{unit_abbr}</div><div class='metric-text'>{run_time}</div></a></div>")
#                    else:
#                        html_bits.append(f"<div class='cal-cell {color_class}'><span style='font-weight: 500;'>{day}</span><span style='color: transparent; font-size:9px;'>-</span><span style='color: transparent; font-size:9px;'>-</span></div>")
#                        
#        html_bits.append("</div></div>")
#        
#        full_html = "".join(html_bits)
#        st.markdown(full_html, unsafe_allow_html=True)
#
#    # ==========================================
#    # RIGHT SIDE COLUMN: RUN SUMMARY WITH GRAPH ABOVE STATS
#    # ==========================================
#    with main_layout_col2:
#        if st.session_state.selected_activity_date:
#            active_date = st.session_state.selected_activity_date
#            matched_runs = df[df['Formatted_Date'] == active_date]
#            
#            if not matched_runs.empty:
#                matched_run = matched_runs.iloc[0].to_dict()
#                st.markdown(f"### 📊 Run Summary: {active_date}")
#                
#                # A. BAR CHART PLOTTED FIRST (ABOVE DATA MATRIX)
#                if "splits" in matched_run and isinstance(matched_run["splits"], list) and len(matched_run["splits"]) > 0:
#                    splits_df = pd.DataFrame(matched_run["splits"])
#                    splits_df['Split Mile'] = "M" + splits_df['split_num'].astype(str)
#                    splits_df['Pace (Minutes)'] = splits_df['pace'].apply(pace_str_to_minutes)
#                    
#                    st.caption("⏱️ Lap Split Profiles (Shorter bars are faster)")
#                    st.bar_chart(data=splits_df, x='Split Mile', y='Pace (Minutes)', use_container_width=True)
#                    
#                    fastest_idx = splits_df['Pace (Minutes)'].idxmin()
#                    slowest_idx = splits_df['Pace (Minutes)'].idxmax()
#                    
#                    st.success(f"⚡ **Fastest Lap:** {splits_df.loc[fastest_idx, 'Split Mile']} ({splits_df.loc[fastest_idx, 'pace']})")
#                    st.error(f"🐢 **Slowest Lap:** {splits_df.loc[slowest_idx, 'Split Mile']} ({splits_df.loc[slowest_idx, 'pace']})")
#                    st.write("---")
#                else:
#                    st.info("No split milestones parsed for this workout data.")
#
#                # B. TOTAL DISTANCE, DURATION, AND PACE CARD BLOCK UNDERNEATH
#                st.metric("Total Distance", f"{matched_run['Display_Distance']:.2f} {unit_abbr}")
#                st.metric("Duration", matched_run.get('Duration', 'N/A'))
#                if 'pace' in matched_run:
#                    st.metric("Average Overall Pace", f"{matched_run['pace']} min/{unit_abbr.lower()}")
#            else:
#                st.caption("Select a run date inside the grid to load data.")
#        else:
#            st.info("👈 Click any bright teal calendar square showing run text data to inspect lap metrics.")
#
