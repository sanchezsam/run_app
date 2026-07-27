# -*- coding: utf-8 -*-
# PART 1 OF 2: PERFORMANCE OVERVIEW COCKPIT & LONG-TAIL HISTORICAL TIME-SERIES RANGE CONTROLS
import streamlit as st
import pandas as pd
import altair as alt
import re
from datetime import datetime, timedelta

def render_dashboard_overview(player):
    st.markdown('## 🏠 Performance Dashboard Overview')
    st.markdown('Simultaneous multi-scale analysis showing daily, weekly, and monthly training volume with expanded side-by-side charts.')
    st.markdown('---')
    
    # SYSTEM TIME CONTROLS: Anchored relative to active calendar timeline (July 23, 2026)
    today_dt = datetime(2026, 7, 23)
    
    # 1. READ PASS: EXTRACT ALL HISTORICAL TRACKING RECORDS
    chart_runs = []
    historical_logs = getattr(player, 'history_logs', [])
    
    for log in historical_logs:
        log_str = str(log)
        if 'miles' in log_str.lower() and 'slept' not in log_str.lower():
            try:
                date_match = re.search(r'\[([0-9-]+)\]', log_str)
                dist_match = re.search(r'(?:Run|run|ran|distance):?\s*([0-9.]+)', log_str, re.IGNORECASE)
                if not dist_match: dist_match = re.search(r'([0-9.]+)\s*(?:miles|mi)', log_str, re.IGNORECASE)
                pace_match = re.search(r'Pace:\s*([0-9.]+)', log_str, re.IGNORECASE)
                ele_match = re.search(r'Elevation\s*Climbed:\s*\+?([0-9.]+)', log_str, re.IGNORECASE)
                
                if dist_match and date_match:
                    dt_obj = datetime.strptime(date_match.group(1)[:10], '%Y-%m-%d')
                    chart_runs.append({
                        'Date': dt_obj,
                        'Distance': float(dist_match.group(1)),
                        'Pace': float(pace_match.group(1)) if pace_match else 8.50,
                        'Elevation': float(ele_match.group(1)) if ele_match else 0.0
                    })
            except Exception: pass

    if not chart_runs:
        st.info("🏁 No recorded workout telemetry discovered yet. Ingest GPX track files to activate your visual metrics!")
        return

    df_master = pd.DataFrame(chart_runs).sort_values(by='Date')
    
    # Scrape the absolute earliest run on file to act as the deep historical slider limit
    earliest_ever_date = df_master['Date'].min().date()
    
    # Setup initial handle target view envelopes relative to today's date
    start_of_week = today_dt - timedelta(days=today_dt.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    current_year_val = today_dt.year
    current_month_val = today_dt.month
    
    start_of_month = datetime(current_year_val, current_month_val, 1)
    if current_month_val == 12:
        end_of_month = datetime(current_year_val + 1, 1, 1) - timedelta(days=1)
    else:
        end_of_month = datetime(current_year_val, current_month_val + 1, 1) - timedelta(days=1)
        
    start_of_year = datetime(current_year_val, 1, 1)
    end_of_year = datetime(current_year_val, 12, 31)
    
    if earliest_ever_date > start_of_week.date(): earliest_ever_date = start_of_week.date()
# PART 2 OF 2: EXPANDED SIDE-BY-SIDE GRAPH CONTRACTIONS WITH TOP-OF-BAR NUMERICAL TOTALS
    col_daily, col_weekly, col_monthly = st.columns(3)

    # --- COLUMN 1: DAILY TELEMETRY VIEW WITH EXPANDED VERTICAL HEIGHT --- [C1]
    with col_daily:
        st.markdown(f"##### 📅 Daily Volume Range")
        
        w_start, w_end = st.slider(
            "Shift Historical Week Window:",
            min_value=earliest_ever_date,
            max_value=end_of_week.date(),
            value=(start_of_week.date(), end_of_week.date()),
            format="MM/DD/YY",
            key="slider_dashboard_daily_week_deep"
        )
        
        df_week = df_master[(df_master['Date'].dt.date >= w_start) & (df_master['Date'].dt.date <= w_end)].copy()
        
        if not df_week.empty:
            df_week['Day_Label'] = df_week['Date'].apply(lambda d: f"{d.strftime('%a').upper()}-{d.month}/{d.day}")
            df_week = df_week.sort_values(by='Date')
            custom_label_sorting_order = df_week['Day_Label'].tolist()
            
            bars = alt.Chart(df_week).mark_bar(color='#10b981', opacity=0.85).encode(
                x=alt.X('Day_Label:N', title='Day & Date (DAY-M/D)', sort=custom_label_sorting_order, axis=alt.Axis(labelAngle=-45)),
                y=alt.Y('Distance:Q', title='Miles'),
                tooltip=[alt.Tooltip('Date:T', format='%Y-%m-%d'), 'Distance', 'Pace']
            )
            
            text = bars.mark_text(align='center', baseline='bottom', dy=-4, color='#111827', fontWeight='bold').encode(
                text=alt.Text('Distance:Q', format='.1f')
            )
            
            # HEIGHT MODIFICATION FIXED: Scaled height parameter container block up to 230px [C1]
            st.altair_chart(alt.layer(bars, text).properties(height=230), use_container_width=True)
        else:
            st.info("ℹ️ No entries inside this filtered week window.")

    # --- COLUMN 2: WEEKLY AGGREGATION VIEW WITH EXPANDED VERTICAL HEIGHT --- [C1]
    with col_weekly:
        st.markdown(f"##### 📈 Weekly Cumulative Volume")
        
        m_start, m_end = st.slider(
            "Shift Historical Month Window:",
            min_value=earliest_ever_date,
            max_value=end_of_month.date(),
            value=(start_of_month.date(), end_of_month.date()),
            format="MM/DD/YY",
            key="slider_dashboard_weekly_month_deep"
        )
        
        df_month = df_master[(df_master['Date'].dt.date >= m_start) & (df_master['Date'].dt.date <= m_end)].copy()
        
        if not df_month.empty:
            df_month['Week Label'] = df_month['Date'].dt.strftime('%b Wk %U')
            df_month_grouped = df_month.groupby('Week Label', as_index=False)['Distance'].sum()
            
            bars = alt.Chart(df_month_grouped).mark_bar(color='#3b82f6', opacity=0.85).encode(
                x=alt.X('Week Label:N', title='Weeks Timeline', sort='x'),
                y=alt.Y('Distance:Q', title='Total Miles'),
                tooltip=['Week Label', 'Distance']
            )
            
            text = bars.mark_text(align='center', baseline='bottom', dy=-4, color='#111827', fontWeight='bold').encode(
                text=alt.Text('Distance:Q', format='.1f')
            )
            
            # HEIGHT MODIFICATION FIXED: Scaled height parameter container block up to 230px [C1]
            st.altair_chart(alt.layer(bars, text).properties(height=230), use_container_width=True)
        else:
            st.info("ℹ️ No entries inside this filtered month window.")

    # --- COLUMN 3: MONTHLY AGGREGATION VIEW WITH EXPANDED VERTICAL HEIGHT --- [C1]
    with col_monthly:
        st.markdown(f"##### 📊 Monthly Macro Standings")
        
        y_start, y_end = st.slider(
            "Shift Historical Year Window:",
            min_value=earliest_ever_date,
            max_value=end_of_year.date(),
            value=(start_of_year.date(), end_of_year.date()),
            format="YYYY/MM",
            key="slider_dashboard_monthly_year_deep"
        )
        
        df_year = df_master[(df_master['Date'].dt.date >= y_start) & (df_master['Date'].dt.date <= y_end)].copy()
        
        if not df_year.empty:
            df_year['Month Label'] = df_year['Date'].dt.strftime('%b %y')
            df_year_grouped = df_year.groupby('Month Label', as_index=False)['Distance'].sum()
            
            bars = alt.Chart(df_year_grouped).mark_bar(color='#f59e0b', opacity=0.85).encode(
                x=alt.X('Month Label:N', title='Months Timeline', sort='x'),
                y=alt.Y('Distance:Q', title='Total Miles'),
                tooltip=['Month Label', 'Distance']
            )
            
            text = bars.mark_text(align='center', baseline='bottom', dy=-4, color='#111827', fontWeight='bold').encode(
                text=alt.Text('Distance:Q', format='.1f')
            )
            
            # HEIGHT MODIFICATION FIXED: Scaled height parameter container block up to 230px [C1]
            st.altair_chart(alt.layer(bars, text).properties(height=230), use_container_width=True)
        else:
            st.info("ℹ️ No entries inside this filtered year window.")

