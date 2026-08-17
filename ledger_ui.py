# -*- coding: utf-8 -*-
# PART 1 OF 2: LEDGER INITIALIZATION, LOG CONVERTERS & SIDE-BY-SIDE WEEKLY PACING GRAPHS
import time
import random
import streamlit as st
import pandas as pd
import altair as alt
import re
from datetime import datetime, timedelta

def render_training_ledger(player):
    st.markdown('## 📅 Training Activity Ledger')
    st.caption("Review, edit, and audit your deep workout log entries sorted chronologically inside historical timeline summaries:")
    st.markdown("---")
    
    # SYSTEM TIME CONTROLS: Hardcoded relative to active calendar timeline (July 23, 2026)
    today_dt = datetime(2026, 7, 23)
    
    run_list = []
    historical_logs = getattr(player, 'history_logs', [])
    
        # =========================================================================
    # REPLACED PARSER ENGINE INITIALIZATION IN PART 1 OF ledger_ui.py
    # =========================================================================
    run_list = []
    historical_logs = getattr(player, 'history_logs', [])
    
    # Track unique combinations of (Date, Distance) to filter out ghost duplicates
    processed_fingerprints = set()
    
    # FIRST PASS: Read all advanced structured dictionaries to prioritize high-fidelity data
    for log in historical_logs:
        if isinstance(log, dict) and ("text_payload" in log or "text_payload" in log):
            try:
                date_str = log.get("Date", log.get("Activity Date"))
                raw_dist = float(log.get("Distance (Miles)", log.get("dist", 0.0)))
                p_val = log.get("Pace_Val", log.get("pace", 0.0))
                if isinstance(p_val, str): 
                    p_val = float(p_val.replace(" min/mi", "").strip())
                
                raw_ele = str(log.get("Elevation (ft)", log.get("ele", "0")))
                elev_val = float(''.join(c for c in raw_ele if c.isdigit() or c=='.') or 0.0)
                dt_val = datetime.strptime(str(date_str)[:10], '%Y-%m-%d')
                
                run_list.append({
                    'Activity Date': date_str,
                    'Distance (Miles)': raw_dist,
                    'Duration': log.get("Duration", log.get("duration", "00:00:00")),
                    'Pace_Val': float(p_val),
                    'Pace (min/mi)': f"{float(p_val):.2f} min/mi" if float(p_val) > 0 else "0.00 min/mi",
                    'Elevation_Val': elev_val,
                    'Elevation (ft)': f"+{int(elev_val)} ft" if "ft" not in raw_ele else raw_ele,
                    'DateObj': dt_val,
                    'splits': log.get("splits", [])
                })
                
                # Register this authentic activity signature fingerprint
                # We round distance slightly to catch floating-point variations (e.g., 26.69 vs 26.7)
                fingerprint = (str(date_str)[:10], round(raw_dist, 1))
                processed_fingerprints.add(fingerprint)
                
            except Exception: pass
            
    # SECOND PASS: Load legacy plain text lines, skipping them if a structured version already exists
    for log in historical_logs:
        if not isinstance(log, dict):
            log_str = str(log)
            if 'miles' in log_str.lower() and 'slept' not in log_str.lower():
                try:
                    date_match = re.search(r'\[([0-9-]+)\]', log_str)
                    dt_val = datetime.strptime(date_match.group(1)[:10], '%Y-%m-%d') if date_match else today_dt
                    date_key = dt_val.strftime('%Y-%m-%d')
                    
                    d_match = re.search(r'(?:Run|run|ran|distance):?\s*([0-9.]+)', log_str, re.IGNORECASE)
                    if not d_match: d_match = re.search(r'([0-9.]+)\s*(?:miles|mi)', log_str, re.IGNORECASE)
                    
                    if d_match:
                        legacy_dist = float(d_match.group(1))
                        legacy_fingerprint = (date_key, round(legacy_dist, 1))
                        
                        # GUARD CLAUSE: Skip loading this string line if we already possess the rich file data
                        if legacy_fingerprint in processed_fingerprints:
                            continue
                            
                        t_match = re.search(r'Duration:\s*([0-9:]+)', log_str, re.IGNORECASE)
                        p_match = re.search(r'Pace:\s*([0-9.]+)', log_str, re.IGNORECASE)
                        e_match = re.search(r'Elevation\s*Climbed:\s*\+?([0-9.]+)', log_str, re.IGNORECASE)
                        
                        run_list.append({
                            'Activity Date': date_key,
                            'Distance (Miles)': legacy_dist,
                            'Duration': t_match.group(1) if t_match else '00:45:00',
                            'Pace_Val': float(p_match.group(1)) if p_match else 8.50,
                            'Pace (min/mi)': f"{float(p_match.group(1)):.2f} min/mi" if p_match else '8.50 min/mi',
                            'Elevation_Val': float(e_match.group(1)) if e_match else 0.0,
                            'Elevation (ft)': f"+{int(float(e_match.group(1)))} ft" if e_match else '+0 ft',
                            'DateObj': dt_val,
                            'splits': None
                        })
                except Exception: pass
 



 
    # --- CALCULATE, GROUP & RENDER MULTI-PERIOD SUMMARIES INSIDE 3 DESIGNATED TABS --- [C3]
    if run_list:
        df_summary = pd.DataFrame(run_list)
        # ===================================================
        # REPLACE THE CRASHING CODE BLOCK IN ledger_ui.py
        # ===================================================
        
        # 1. Build a clean, flat standard Python list containing all split data structures
        splits_column_list = []
        
        for log in player.history_logs:
            # Check if this item is a structured dict object that holds mile splits
            if isinstance(log, dict) and 'splits' in log and log['splits']:
                splits_column_list.append(log['splits'])
            else:
                # Pass None for legacy text log items (GPX/TCX) so the array length matches perfectly
                splits_column_list.append(None)
        
        # 2. Convert the list into a specialized Python Object Series and map it to your DataFrame in a single step
        # This prevents Pandas from doing horizontal alignment checks and forces cells to hold the lists
        df_summary['splits'] = pd.Series(splits_column_list, dtype='object')







        df_summary['Year_Label'] = df_summary['DateObj'].dt.strftime('%Y')
        df_summary['Month_Label'] = df_summary['DateObj'].dt.strftime('%B %Y')
        df_summary['Month_Sort'] = df_summary['DateObj'].dt.strftime('%Y-%m')
        
        df_summary['ISO_Year'] = df_summary['DateObj'].dt.isocalendar().year
        df_summary['ISO_Wk_Num'] = df_summary['DateObj'].dt.isocalendar().week
        df_summary['Week_Group_Label'] = df_summary.apply(lambda r: f"{r['ISO_Year']}-Wk {r['ISO_Wk_Num']:02d}", axis=1)
        
        st.markdown(f"### 🏆 Career Milestones Historical Summary Matrix")
        
        tab_multi_week, tab_multi_month, tab_multi_year = st.tabs([
            "📈 Historical Weekly Reports", "📊 Historical Monthly Groupings", "👑 Historical Yearly Standings"
        ])
        
        with tab_multi_week:
            st.caption("Aggregated cumulative volume parameters, data charts, and dynamic sheets for every separate week:")
            
            # =========================================================================
            # DUAL-AXIS TIMELINE PROGRESSION ANALTICS CHART INJECTION
            # =========================================================================
            if not df_summary.empty:
                st.markdown("#### 📊 Chronological Weekly Performance Analytics Timeline")
                
                # Group data to calculate clean weekly sums and averages for the graph
                df_weekly_metrics = df_summary.groupby('Week_Group_Label').agg(
                    Total_Distance=('Distance (Miles)', 'sum'),
                    Average_Pace=('Pace_Val', 'mean'),
                    Run_Count=('Distance (Miles)', 'count')
                ).reset_index().sort_values(by='Week_Group_Label')
                
                # Base chart layer mapped to your calculated weekly timeline dimensions
                base_weekly_chart = alt.Chart(df_weekly_metrics).encode(
                    x=alt.X('Week_Group_Label:N', title='Historical Calendar Weeks (ISO Timeline)', sort='ascending')
                )
                
                # 1. Primary Left Axis Layer: Emerald Green area graph representing distance volume
                weekly_distance_area = base_weekly_chart.mark_area(
                    color='#10b981', 
                    opacity=0.4,
                    line={'color': '#10b981', 'width': 2}
                ).encode(
                    y=alt.Y('Total_Distance:Q', title='Weekly Total Distance (Miles)')
                )
                
                # 2. Secondary Right Axis Layer: Deep Sapphire blue line representing pacing efficiency 
                weekly_pace_line = base_weekly_chart.mark_line(
                    color='#3b82f6', 
                    strokeWidth=3,
                    point=alt.OverlayMarkDef(color='#111827', size=40, filled=True)
                ).encode(
                    y=alt.Y('Average_Pace:Q', title='Weekly Average Pace (min/mi)', scale=alt.Scale(zero=False))
                )
                
                # Layer the dual axes together and pass container layouts to Streamlit
                combined_weekly_graph = alt.layer(
                    weekly_distance_area, 
                    weekly_pace_line
                ).resolve_scale(
                    y='independent'
                ).properties(
                    height=280,
                    title="Odometer Volume (Green) vs. Average Pacing Speed (Blue) Progression"
                )
                
                st.altair_chart(combined_weekly_graph, use_container_width=True)
                st.markdown("---")
            
            unique_weeks_grouped = sorted(df_summary['Week_Group_Label'].unique(), reverse=True)
            
            # ===================================================
            # UPDATE THE INNER LOOP BLOCK INSIDE ledger_ui.py
            # ===================================================
            
            # 1. Update your loop header statement to capture an enumeration index:
            for wk_idx, wk_label in enumerate(unique_weeks_grouped):
                df_wk_chunk = df_summary[df_summary['Week_Group_Label'] == wk_label].sort_values(by='Activity Date')
                
                first_date_val = df_wk_chunk['DateObj'].min()
                last_date_val = df_wk_chunk['DateObj'].max()
                date_span_string = f"{first_date_val.strftime('%b %d')} - {last_date_val.strftime('%b %d, %Y')}"
                
                with st.expander(f"📆 Weekly Report & Sheet — {wk_label} ({date_span_string} | {len(df_wk_chunk)} Runs)"):
                    # =========================================================================
                    # NEW: FOCUS 7-DAY DAILY VOLUME BAR CHART FOR THIS SPECIFIC WEEK
                    # =========================================================================
                    if not df_wk_chunk.empty:
                        # Group rows by explicit calendar date to handle multiple same-day runs cleanly
                        df_daily_volume = df_wk_chunk.groupby('Activity Date').agg(
                            Daily_Distance=('Distance (Miles)', 'sum')
                        ).reset_index().sort_values(by='Activity Date')
                        
                        # Generate an enlarged vertical emerald bar chart for clearer tracking visibility
                        daily_volume_chart = alt.Chart(df_daily_volume).mark_bar(
                            color='#10b981',
                            cornerRadiusTopLeft=4,
                            cornerRadiusTopRight=4,
                            size=30 # Slightly wider columns to fit the taller scale canvas layout
                        ).encode(
                            x=alt.X('Activity Date:N', title='Calendar Workout Dates (Max 7 Days)', axis=alt.Axis(labelAngle=0)),
                            y=alt.Y('Daily_Distance:Q', title='Logged Distance (Miles)', scale=alt.Scale(padding=15)),
                            tooltip=[
                                alt.Tooltip('Activity Date:N', title='Date'),
                                alt.Tooltip('Daily_Distance:Q', title='Total Distance (Mi)', format='.2f')
                            ]
                        ).properties(
                            height=260, # Increased from 160 to 260 for a larger vertical scale canvas footprint
                            title=f"📅 Daily Mileage Distribution Breakdown"
                        )
                        
                        st.altair_chart(daily_volume_chart, use_container_width=True)
                        st.markdown("<p style='margin-bottom:12px; border-bottom: 1px solid #f3f4f6;'></p>", unsafe_allow_html=True)
                    
                    # =========================================================================
                    # CONSOLIDATED DROPDOWN TIMELINE CONTROLS FOR MULTI-WEEK EXPANDERS
                    # =========================================================================
                    # =========================================================================
                    # CONSOLIDATED DATA VIEW: REPLACED ST.DATA_EDITOR WITH ROW-BY-ROW TABLES
                    # =========================================================================
                    st.markdown("<p style='margin-top:15px; margin-bottom:5px;'></p>", unsafe_allow_html=True)
                    
                    if 'splits' not in df_wk_chunk.columns:
                        df_wk_chunk['splits'] = None

                    # Loop through each individual activity inside this week chunk DataFrame
                    for idx, row in df_wk_chunk.iterrows():
                        act_date = row['Activity Date']
                        act_dist = float(row['Distance (Miles)'])
                        act_dur = str(row['Duration'])
                        act_ele = row['Elevation (ft)']
                        act_name = row.get('Activity Name', '🏃‍♂️ Run')
                        
                        # --- LIVE MATH PACING ENGINE ---
                        # Calculate pace dynamically using the true duration string and distance on screen
                        calculated_pace_val = 0.0
                        if act_dist > 0.1 and ":" in act_dur:
                            try:
                                dur_parts = act_dur.split(":")
                                if len(dur_parts) == 3:
                                    total_minutes = (int(dur_parts[0]) * 60.0) + int(dur_parts[1]) + (int(dur_parts[2]) / 60.0)
                                elif len(dur_parts) == 2:
                                    total_minutes = int(dur_parts[0]) + (int(dur_parts[1]) / 60.0)
                                
                                calculated_pace_val = total_minutes / act_dist
                            except Exception:
                                calculated_pace_val = 0.0
                                
                        # Fallback wrapper check to capture pre-formatted keys if math is skipped
                        if calculated_pace_val == 0.0:
                            raw_p = row.get('Pace_Val', row.get('pace', 0.0))
                            if isinstance(raw_p, str):
                                raw_p = float(raw_p.replace(" min/mi", "").strip())
                            calculated_pace_val = float(raw_p)

                        # 1. Print the clean historic activity summary row text record
                        st.markdown(
                            f"📋 **{act_name}** — `[{act_date}]` — `{act_dist:.2f} Mi` | "
                            f"Time: `{act_dur}` | `{calculated_pace_val:.2f} min/mi` Pace | `{act_ele}` Climbing"
                        )
                        
                        # 2. Extract split data directly from save_file.json
                        splits_data = row['splits']
                        
                        # 3. Render a dropdown expander ONLY if valid splits telemetry exists
                        if isinstance(splits_data, list) and len(splits_data) > 0:
                            # Stable per-row key so the toggle keeps its state across reruns
                            unique_exp_key = f"exp_splits_{wk_idx}_{wk_label}_{idx}"
                            
                            # Streamlit forbids expanders inside expanders, so toggle the table instead
                            if st.checkbox("⏱️ View Mile Splits Breakdown", key=unique_exp_key):
                                df_splits_display = pd.DataFrame(splits_data)
                                df_splits_display.columns = ["Split #", "Distance (Mi)", "Split Time", "Pace (/mi)"]
                                st.dataframe(df_splits_display, use_container_width=True, hide_index=True)
                        
                        # Soft visual divider line between separate workouts
                        st.markdown("<p style='margin-top:2px; margin-bottom:8px; border-bottom: 1px dashed #e2e8f0;'></p>", unsafe_allow_html=True)
                        
                    st.markdown("<p style='margin-bottom:10px;'></p>", unsafe_allow_html=True)






# PART 2 OF 2: EXPANDABLE HISTORICAL MONTHLY/YEARLY VISUAL MODULE VIEWS AND WRAP CONTROLLERS
        with tab_multi_month:
            st.caption("Aggregated cumulative volume parameters and dynamic trend graphs mapped for every separate month:")
            unique_months_grouped = df_summary[['Month_Sort', 'Month_Label']].drop_duplicates().sort_values(by='Month_Sort', ascending=False).values
            
            for m_sort, m_title in unique_months_grouped:
                df_m_chunk = df_summary[df_summary['Month_Label'] == m_title].sort_values(by='Activity Date')
                
                with st.expander(f"📉 Cumulative Standings Summary — {m_title} ({len(df_m_chunk)} Runs)"):
                    m_total_dist = df_m_chunk['Distance (Miles)'].sum()
                    m_avg_pace = df_m_chunk['Pace_Val'].mean()
                    m_total_elev = df_m_chunk['Elevation_Val'].sum()
                    m_fastest_pr = df_m_chunk['Pace_Val'].min()
                    
                    mc1, mc2, mc3, mc4 = st.columns(4)
                    with mc1: st.metric("Odometer Volume", f"{m_total_dist:.2f} Mi")
                    with mc2: st.metric("Average Split Pace", f"{m_avg_pace:.2f} min/mi")
                    with mc3: st.metric("Vertical Ascent", f"+{int(m_total_elev):,} Ft")
                    with mc4: st.metric("Fastest PR Split", f"{m_fastest_pr:.2f} min/mi")
                    
                    g_col1, g_col2 = st.columns(2)
                    with g_col1:
                        st.caption("🟢 Mileage Volume Timeline")
                        m_bars_dist = alt.Chart(df_m_chunk).mark_bar(color='#10b981', opacity=0.85).encode(
                            x=alt.X('Activity Date:O', title='Date'), y=alt.Y('Distance (Miles):Q', title='Miles')
                        )
                        m_text_dist = m_bars_dist.mark_text(align='center', baseline='bottom', dy=-4, color='#111827', fontWeight='bold').encode(
                            text=alt.Text('Distance (Miles):Q', format='.1f')
                        )
                        st.altair_chart(alt.layer(m_bars_dist, m_text_dist).properties(height=200), use_container_width=True)
                    with g_col2:
                        st.caption("🔵 Average Pacing Split Timeline")
                        m_bars_pace = alt.Chart(df_m_chunk).mark_bar(color='#3b82f6', opacity=0.85).encode(
                            x=alt.X('Activity Date:O', title='Date'), y=alt.Y('Pace_Val:Q', title='min/mi', scale=alt.Scale(zero=False))
                        )
                        m_text_pace = m_bars_pace.mark_text(align='center', baseline='bottom', dy=-4, color='#111827', fontWeight='bold').encode(
                            text=alt.Text('Pace_Val:Q', format='.1f')
                        )
                        st.altair_chart(alt.layer(m_bars_pace, m_text_pace).properties(height=200), use_container_width=True)

        with tab_multi_year:
            st.caption("Aggregated cumulative volume parameters and dynamic annual charts mapped for every separate year:")
            unique_years_list = sorted(df_summary['Year_Label'].unique(), reverse=True)
            
            for yr_title in unique_years_list:
                df_y_chunk = df_summary[df_summary['Year_Label'] == yr_title].copy()
                
                with st.expander(f"👑 Grand Championship Achievements — Year {yr_title} ({len(df_y_chunk)} Total Runs)"):
                    y_total_dist = df_y_chunk['Distance (Miles)'].sum()
                    y_avg_pace = df_y_chunk['Pace_Val'].mean()
                    y_total_elev = df_y_chunk['Elevation_Val'].sum()
                    y_fastest_pr = df_y_chunk['Pace_Val'].min()
                    
                    yc1, yc2, yc3, yc4 = st.columns(4)
                    with yc1: st.metric("Annual Distance Sum", f"{y_total_dist:.2f} Mi")
                    with yc2: st.metric("Annual Mean Pace", f"{y_avg_pace:.2f} min/mi")
                    with yc3: st.metric("Annual Climbing Power", f"+{int(y_total_elev):,} Ft")
                    with yc4: st.metric("Annual Speedway PR", f"{y_fastest_pr:.2f} min/mi")
                    
                    df_y_chunk['Month Name'] = df_y_chunk['DateObj'].dt.strftime('%b')
                    month_order_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                    df_y_grouped = df_y_chunk.groupby('Month Name', as_index=False).agg({'Distance (Miles)': 'sum', 'Pace_Val': 'mean'})
                    
                    yg_col1, yc_col2 = st.columns(2)
                    with yg_col1:
                        st.caption("🟢 Monthly Accumulated Volume")
                        y_bars_dist = alt.Chart(df_y_grouped).mark_bar(color='#10b981', opacity=0.85).encode(
                            x=alt.X('Month Name:N', title='Month', sort=month_order_list), y=alt.Y('Distance (Miles):Q', title='Miles')
                        )
                        y_text_dist = y_bars_dist.mark_text(align='center', baseline='bottom', dy=-4, color='#111827', fontWeight='bold').encode(
                            text=alt.Text('Distance (Miles):Q', format='.1f')
                        )
                        st.altair_chart(alt.layer(y_bars_dist, y_text_dist).properties(height=200), use_container_width=True)
                    with yc_col2:
                        st.caption("🔵 Monthly Average Pace Trend")
                        y_bars_pace = alt.Chart(df_y_grouped).mark_bar(color='#3b82f6', opacity=0.85).encode(
                            x=alt.X('Month Name:N', title='Month', sort=month_order_list), y=alt.Y('Pace_Val:Q', title='min/mi', scale=alt.Scale(zero=False))
                        )
                        y_text_pace = y_bars_pace.mark_text(align='center', baseline='bottom', dy=-4, color='#111827', fontWeight='bold').encode(
                            text=alt.Text('Pace_Val:Q', format='.1f')
                        )
                        st.altair_chart(alt.layer(y_bars_pace, y_text_pace).properties(height=200), use_container_width=True)
                        
        st.markdown("---")
        st.info("💡 *Tip: To edit raw values or delete entries, expand any specific calendar segment row above inside the Weekly Reports sub-tab panel.*")
    else:
        st.info('No recorded activity blocks discovered inside database layers. Ingest GPX track profiles to populate your calendar.')

