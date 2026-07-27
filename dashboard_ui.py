# Part 1: source_payload.py (Data Processing & Setup)
import streamlit as st
import pandas as pd
import datetime
import altair as alt
import json
import os
import math

def render_dashboard_overview(player_object=None):
    st.title("🏃‍♂️ Training Ledger Analytics & RPG Progression")
    
    # 1. READ DATA
    df = pd.DataFrame()
    json_path = "save_file.json"
    raw_records = []

    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as file_handle:
                json_data = json.load(file_handle)
            if isinstance(json_data, dict) and "history_logs" in json_data:
                raw_records = [
                    row for row in json_data["history_logs"] 
                    if isinstance(row, dict) and 'Date' in row and 'Distance (Miles)' in row
                ]
        except Exception as file_err:
            st.error(f"Error accessing training files: {file_err}")

    if raw_records:
        try: 
            df = pd.DataFrame(raw_records)
        except Exception as df_err: 
            st.error(f"Error: {df_err}")

    if df.empty:
        st.error("❌ Could not map valid training entries from 'history_logs'.")
        return

    # Standardize column headers and types
    df['Date'] = pd.to_datetime(df['Date'])
    mileage_col = 'Distance (Miles)'
    df[mileage_col] = pd.to_numeric(df[mileage_col], errors='coerce').fillna(0.0)
    df['Year'] = df['Date'].dt.year

    if 'Elevation (ft)' in df.columns:
        df['Elev_Clean'] = df['Elevation (ft)'].astype(str).str.replace('+', '', regex=False)
        df['Elev_Clean'] = df['Elev_Clean'].str.replace('ft', '', regex=False).str.strip()
        df['Elev_Clean'] = pd.to_numeric(df['Elev_Clean'], errors='coerce').fillna(0.0)
    else:
        df['Elev_Clean'] = 0.0

    if 'Duration' in df.columns:
        def duration_to_hours(val):
            try:
                parts = str(val).split(':')
                return int(parts[0]) + int(parts[1])/60.0 + int(parts[2])/3600.0 if len(parts) == 3 else 0.0
            except: 
                return 0.0
        df['Duration_Hours'] = df['Duration'].apply(duration_to_hours)
    else:
        df['Duration_Hours'] = 0.0
# Part 2: source_payload.py (Filter System and Main Grid Interface)
    # 2. FILTER INTERFACE BY YEAR
    year_options = sorted(list(df['Year'].unique()), reverse=True)
    if not year_options: 
        year_options = [datetime.datetime.now().year]

    if "selected_year_filter" not in st.session_state:
        st.session_state["selected_year_filter"] = year_options[0]

    try: 
        radio_index = year_options.index(st.session_state["selected_year_filter"])
    except ValueError: 
        radio_index = 0

    selected_year = st.radio(
        "Select Filter Training Season:", options=year_options, index=radio_index, horizontal=True, key="year_radio_widget"
    )
    st.session_state["selected_year_filter"] = selected_year
    year_df = df[df['Year'] == st.session_state["selected_year_filter"]].copy()
    st.markdown("---")

    month_order = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    year_df['Month'] = year_df['Date'].dt.strftime('%B')
    monthly_grouped = year_df.groupby('Month')[mileage_col].sum().reindex(month_order).fillna(0.0).reset_index()

    # 3. SIDE-BY-SIDE GRID GRAPH LAYOUT
    col1, col2, col3 = st.columns(3)
    
    with col2:
        st.subheader(f"Monthly Distance ({st.session_state['selected_year_filter']})")
        click_selector_month = alt.selection_point(fields=['Month'], name='select_month')
        color_condition_month = alt.condition(click_selector_month, alt.value("#2ca02c"), alt.value("#a1d99b"))
        
        monthly_chart = alt.Chart(monthly_grouped).mark_bar().encode(
            x=alt.X('Month:N', sort=month_order, title="Month"), y=alt.Y(f'{mileage_col}:Q', title="Miles Run"),
            color=color_condition_month, tooltip=['Month', alt.Tooltip(f'{mileage_col}:Q', format='.2f')]
        ).add_params(click_selector_month).properties(height=300)
        selected_month_data = st.altair_chart(monthly_chart, use_container_width=True, on_select="rerun")
        
    active_month = None
    if selected_month_data and 'selection' in selected_month_data and 'select_month' in selected_month_data['selection']:
        points_m = selected_month_data['selection']['select_month']
        if isinstance(points_m, list) and len(points_m) > 0: 
            active_month = points_m[0].get('Month')
        elif isinstance(points_m, dict): 
            active_month = points_m.get('Month')

    with col1:
        if active_month:
            st.subheader(f"Weekly Totals ({active_month})")
            filtered_df = year_df[year_df['Month'] == active_month].copy()
        else:
            st.subheader(f"Weekly Totals (Full Year)")
            filtered_df = year_df.copy()
            
        try:
            year_start_date = pd.to_datetime(f"{st.session_state['selected_year_filter']}-01-01")
            days_elapsed = (filtered_df['Date'] - year_start_date).dt.days
            filtered_df['Week Number'] = (days_elapsed // 7 + 1)
            
            if active_month:
                sample_dates = pd.date_range(start=f"{st.session_state['selected_year_filter']}-{active_month}-01", end=f"{st.session_state['selected_year_filter']}-{active_month}-28", freq='D')
                target_weeks = sorted(list(set([((d - year_start_date).days // 7 + 1) for d in sample_dates])))
                full_year_weeks = [w for w in target_weeks if 1 <= w <= 53]
            else:
                full_year_weeks = list(range(1, 53))
                
            base_weekly_template = pd.DataFrame({'Week Number': full_year_weeks, mileage_col: 0.0})
            
            if not filtered_df.empty:
                real_weekly_totals = filtered_df.groupby('Week Number')[mileage_col].sum().reset_index()
                combined_weekly = pd.merge(base_weekly_template, real_weekly_totals, on='Week Number', how='left', suffixes=('_base', '_real'))
                combined_weekly[mileage_col] = combined_weekly[mileage_col + '_real'].fillna(0.0)
            else:
                combined_weekly = base_weekly_template

            combined_weekly['Week Label'] = combined_weekly['Week Number'].astype(str)
            weekly_altair_chart = alt.Chart(combined_weekly).mark_bar(color="#4c78a8").encode(
                x=alt.X('Week Label:N', sort=combined_weekly['Week Number'].tolist(), title="Week Number"),
                y=alt.Y(f'{mileage_col}:Q', title="Miles Run", scale=alt.Scale(domainMin=0)),
                tooltip=['Week Label', alt.Tooltip(f'{mileage_col}:Q', format='.2f')]
            ).properties(height=300)
            st.altair_chart(weekly_altair_chart, use_container_width=True)
        except Exception as weekly_err: 
            st.error(f"Error: {weekly_err}")

    with col3:
        st.subheader("All-Time Season Totals")
        df['Year_Label'] = df['Year'].astype(str)
        yearly_grouped = df.groupby('Year_Label')[mileage_col].sum().reset_index()
        
        click_selector_year = alt.selection_point(fields=['Year_Label'], name='select_year')
        color_condition_year = alt.condition(alt.datum.Year_Label == str(st.session_state["selected_year_filter"]), alt.value("#ff7f0e"), alt.value("#1f77b4"))
        
        yearly_chart = alt.Chart(yearly_grouped).mark_bar().encode(
            x=alt.X('Year_Label:N', title="Year"), y=alt.Y(f'{mileage_col}:Q', title="Total Miles"),
            color=color_condition_year, tooltip=['Year_Label', alt.Tooltip(f'{mileage_col}:Q', format='.2f')]
        ).add_params(click_selector_year).properties(height=300)
        selected_year_data = st.altair_chart(yearly_chart, use_container_width=True, on_select="rerun")
# Part 3: source_payload.py (Moving Window Metrics & Dynamic Progression)
    # 4. METRIC CORES
    st.markdown(" ")
    col1_sum, col2_sum, col3_sum = st.columns(3)
    def format_hours(total_hours):
        return f"{int(total_hours)}h {int((total_hours - int(total_hours)) * 60)}m"

    with col1_sum:
        sub_target = year_df[year_df['Month'] == active_month] if active_month else year_df
        label_prefix = active_month if active_month else f"Full Year {st.session_state['selected_year_filter']}"
        st.metric(label=f"📊 {label_prefix} Distance", value=f"{sub_target[mileage_col].sum():,.2f} mi")
        st.write(f"⏱️ **Duration:** {format_hours(sub_target['Duration_Hours'].sum())}")
        st.write(f"🏔️ **Elevation:** +{sub_target['Elev_Clean'].sum():,.1f} ft")
    with col2_sum:
        st.metric(label=f"📅 {st.session_state['selected_year_filter']} Season Distance", value=f"{year_df[mileage_col].sum():,.2f} mi")
        st.write(f"⏱️ **Duration:** {format_hours(year_df['Duration_Hours'].sum())}")
        st.write(f"🏔️ **Elevation:** +{year_df['Elev_Clean'].sum():,.1f} ft")
    with col3_sum:
        st.metric(label="🏆 Grand Total Distance", value=f"{df[mileage_col].sum():,.2f} mi")
        st.write(f"⏱️ **Duration:** {format_hours(df['Duration_Hours'].sum())}")
        st.write(f"🏔️ **Elevation:** +{df['Elev_Clean'].sum():,.1f} ft")

    # 5. HIGH-IMPACT XP WINDOW PROCESSING
    st.markdown("---")
    st.header("⚔️ Character Attribute Mastery Levels (Impact-Decay Active)")

    try:
        timeline_df = df.sort_values('Date').copy()
        timeline_df['End_Pts'] = (timeline_df[mileage_col] * 10) + timeline_df[mileage_col].apply(lambda m: 50 if m >= 10.0 else 0)
        timeline_df['Pace_Pts'] = timeline_df['pace'].apply(lambda p: int((11.0 - p) * 20) if p < 11.0 else 0) + timeline_df['pace'].apply(lambda p: 100 if p < 7.0 else 0)
        timeline_df['Elev_Pts'] = (timeline_df['Elev_Clean'] / 2) + timeline_df['Elev_Clean'].apply(lambda e: 75 if e >= 500.0 else 0)

        timeline_df = timeline_df.set_index('Date')

        # Acute Load (Last 30 Days) vs Chronic Baseline (Last 90 Days)
        timeline_df['Acute_End'] = timeline_df['End_Pts'].rolling('30D', min_periods=1).sum()
        timeline_df['Chronic_End'] = timeline_df['End_Pts'].rolling('90D', min_periods=1).mean() * 30.0

        timeline_df['Acute_Pace'] = timeline_df['Pace_Pts'].rolling('30D', min_periods=1).sum()
        timeline_df['Chronic_Pace'] = timeline_df['Pace_Pts'].rolling('90D', min_periods=1).mean() * 30.0

        timeline_df['Acute_Elev'] = timeline_df['Elev_Pts'].rolling('30D', min_periods=1).sum()
        timeline_df['Chronic_Elev'] = timeline_df['Elev_Pts'].rolling('90D', min_periods=1).mean() * 30.0

        latest_row = timeline_df.iloc[-1]

        def get_impact_stats(acute, chronic, factor):
            ratio = acute / chronic if chronic > 0 else 1.0
            base_xp = acute
            # Compounding penalty if ratio < 1.0, bonus multiplier if ratio > 1.0
            modified_xp = max(0, int(base_xp * (ratio ** 2)))
            
            lvl = int(math.floor(math.sqrt(modified_xp / factor))) + 1
            pts_current = int(((lvl - 1) ** 2) * factor)
            pts_next = int((lvl ** 2) * factor)
            prog = min(1.0, max(0.0, (modified_xp - pts_current) / float(pts_next - pts_current))) if pts_next > pts_current else 0.0
            return lvl, prog, modified_xp, ratio

        e_lvl, e_prog, e_xp, e_ratio = get_impact_stats(latest_row['Acute_End'], latest_row['Chronic_End'], 100)
        p_lvl, p_prog, p_xp, p_ratio = get_impact_stats(latest_row['Acute_Pace'], latest_row['Chronic_Pace'], 150)
        h_lvl, h_prog, h_xp, h_ratio = get_impact_stats(latest_row['Acute_Elev'], latest_row['Chronic_Elev'], 120)

        col_st1, col_st2, col_st3 = st.columns(3)
        with col_st1:
            st.subheader(f"🏃‍♂️ Endurance (Lv. {e_lvl})")
            st.progress(e_prog)
            st.caption(f"XP: **{e_xp:,}** | Modifier: **{e_ratio:.2f}x**")
        with col_st2:
            st.subheader(f"⚡ Agility Pace (Lv. {p_lvl})")
            st.progress(p_prog)
            st.caption(f"XP: **{p_xp:,}** | Modifier: **{p_ratio:.2f}x**")
        with col_st3:
            st.subheader(f"🏔️ Hill Force (Lv. {h_lvl})")
            st.progress(h_prog)
            st.caption(f"XP: **{h_xp:,}** | Modifier: **{h_ratio:.2f}x**")

        # 6. HISTORICAL WORKLOAD BALANCE GRAPH (Flipped: Acute - Chronic)
        st.markdown("---")
        st.subheader("📉 Historical Workload Variance Balance")
        st.caption("Green bars above 0 indicate volume surge milestones (like Aug & Sept 2025). Red bars below 0 isolate detraining dips (like June & July 2025).")
        
        monthly_series = timeline_df.resample('ME')[mileage_col].sum().reset_index()
        monthly_series['Acute_Fatigue'] = monthly_series[mileage_col]
        monthly_series['Chronic_Fitness'] = monthly_series[mileage_col].rolling(window=3, min_periods=1).mean()
        monthly_series['Variance_Status'] = monthly_series['Acute_Fatigue'] - monthly_series['Chronic_Fitness']
        monthly_series['Month_Label'] = monthly_series['Date'].dt.strftime('%b %Y')

        load_chart = alt.Chart(monthly_series).mark_bar().encode(
            x=alt.X('Month_Label:N', sort=monthly_series['Date'].tolist(), title="Training Month"),
            y=alt.Y('Variance_Status:Q', title="Fitness Balance Variance"),
            color=alt.condition(alt.datum.Variance_Status >= 0, alt.value("#2ca02c"), alt.value("#d62728")),
            tooltip=['Month_Label', alt.Tooltip(mileage_col, title="Total Miles")]
        ).properties(height=300)
        st.altair_chart(load_chart, use_container_width=True)

        # 7. CHRONOLOGICAL XP TIMELINE (Impact-Adjusted)
        st.markdown("---")
        st.subheader("📈 Chronological Skill XP Progression Timeline (Impact-Adjusted)")
        
        history_df = timeline_df.reset_index()
        history_df['Hist_End_XP'] = history_df.apply(lambda r: max(0, int(r['Acute_End'] * ((r['Acute_End']/r['Chronic_End'])**2))) if r['Chronic_End'] > 0 else int(r['Acute_End']), axis=1)
        history_df['Hist_Pace_XP'] = history_df.apply(lambda r: max(0, int(r['Acute_Pace'] * ((r['Acute_Pace']/r['Chronic_Pace'])**2))) if r['Chronic_Pace'] > 0 else int(r['Acute_Pace']), axis=1)
        history_df['Hist_Elev_XP'] = history_df.apply(lambda r: max(0, int(r['Acute_Elev'] * ((r['Acute_Elev']/r['Chronic_Elev'])**2))) if r['Chronic_Elev'] > 0 else int(r['Acute_Elev']), axis=1)

        melted_timeline = history_df.melt(id_vars=['Date'], value_vars=['Hist_End_XP', 'Hist_Pace_XP', 'Hist_Elev_XP'], var_name='Skill Attribute', value_name='Total XP')
        melted_timeline['Skill Attribute'] = melted_timeline['Skill Attribute'].map({'Hist_End_XP': 'Endurance XP', 'Hist_Pace_XP': 'Agility Pace XP', 'Hist_Elev_XP': 'Hill Force XP'})

        progression_chart = alt.Chart(melted_timeline).mark_line(strokeWidth=2.5).encode(
            x=alt.X('Date:T', title="Timeline"), y=alt.Y('Total XP:Q', title="Active Skill XP"),
            color=alt.Color('Skill Attribute:N', scale=alt.Scale(range=["#4c78a8", "#2ca02c", "#ff7f0e"])),
            tooltip=['Date:T', 'Skill Attribute:N', 'Total XP:Q']
        ).properties(height=350).interactive()
        st.altair_chart(progression_chart, use_container_width=True)

    except Exception as stat_err:
        st.info(f"Log runs to initialize character skill tracking curves: {stat_err}")

    # Year Selector Click Handler
    if selected_year_data and 'selection' in selected_year_data and 'select_year' in selected_year_data['selection']:
        points_y = selected_year_data['selection']['select_year']
        target_item = None
        if isinstance(points_y, list) and len(points_y) > 0: 
            target_item = points_y[0]
        elif isinstance(points_y, dict): 
            target_item = points_y
            
        if target_item and target_item.get('Year_Label') is not None:
            clicked_year = int(target_item.get('Year_Label'))
            if clicked_year != st.session_state["selected_year_filter"]:
                st.session_state["selected_year_filter"] = clicked_year
                st.rerun()

