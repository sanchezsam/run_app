import os

target_file = "ledger_ui.py"

if not os.path.exists(target_file):
    print(f"❌ Error: Could not locate '{target_file}' in this folder.")
    exit(1)

with open(target_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Landmark comment defining our nested 7-day bar chart block inside your ledger script
old_chart_block = """                        # Generate a clean vertical emerald bar chart capped naturally at a max of 7 rows
                        daily_volume_chart = alt.Chart(df_daily_volume).mark_bar(
                            color='#10b981',
                            cornerRadiusTopLeft=4,
                            cornerRadiusTopRight=4,
                            size=25 # Uniform bar width distribution 
                        ).encode(
                            x=alt.X('Activity Date:N', title='Calendar Workout Dates (Max 7 Days)', axis=alt.Axis(labelAngle=0)),
                            y=alt.Y('Daily_Distance:Q', title='Logged Distance (Miles)'),
                            tooltip=[
                                alt.Tooltip('Activity Date:N', title='Date'),
                                alt.Tooltip('Daily_Distance:Q', title='Total Distance (Mi)', format='.2f')
                            ]
                        ).properties(
                            height=160,
                            title=f"📅 Daily Mileage Distribution Breakdown"
                        )"""

if old_chart_block not in content:
    print("❌ Error: Could not find the original daily_volume_chart code block inside 'ledger_ui.py'.")
    print("Ensure you haven't manually modified its spacing or parameters prior to running this patch.")
    exit(1)

# Definition of your newly scaled, high-fidelity canvas block replacement
repaired_chart_block = """                        # Generate an enlarged vertical emerald bar chart for clearer tracking visibility
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
                        )"""

# Swap out the chart properties cleanly using explicit text replacement
final_file_output = content.replace(old_chart_block, repaired_chart_block)

with open(target_file, 'w', encoding='utf-8') as f:
    f.write(final_file_output)

print("✅ SUCCESS: 'ledger_ui.py' has been successfully patched!")
print("📊 Your daily training bar graphs have been expanded to a large-scale, high-fidelity format.")

