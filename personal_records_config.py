# ==============================================================================
# 🎯 DYNAMIC PERSONAL RECORDS CONFIGURATION REGISTRY
# ==============================================================================
# Add, remove, or modify personal record structures here. The UI loop and engine 
# will adapt automatically without requiring any source code modifications.

PERSONAL_RECORDS_REGISTRY = [
    {
        "id": "longest_run",
        "title": "🏃‍♂️ LONGEST RUN",
        "border_color": "#f1c40f",        # Yellow accent highlight
        "data_column": "Display_Distance", # Matches your uploaded log columns
        "metric_suffix": "Mi",
        "fallback_value": "0.00 Mi",
        "fallback_date": "No Logs Uploaded",
        "calculation_type": "max"          # Grabs the highest recorded volume line
    },
    {
        "id": "fastest_mile",
        "title": "⚡ FASTEST MILE",
        "border_color": "#9b59b6",        # Purple accent highlight
        "data_column": "Avg_Pace",         # Tracks speed pace columns
        "metric_suffix": "/mi",
        "fallback_value": "5:42 /mi",      # Centralized data-driven fallback standard
        "fallback_date": "2025-10-12",
        "calculation_type": "min_pace"     # Evaluates the lowest numerical pace score
    },
    {
        "id": "peak_annual_volume",
        "title": "📅 PEAK VOLUME YEAR",
        "border_color": "#3498db",        # Blue accent highlight
        "data_column": "Display_Distance",
        "metric_suffix": "Mi",
        "fallback_value": "0.0 Mi",
        "fallback_date": "Year: No Data",
        "calculation_type": "peak_year"    # Summarizes rolling annual calendar groups
    },
    {
        "id": "fastest_5k",
        "title": "🏁 COURSE PR (5K)",
        "border_color": "#2ecc71",        # Green accent highlight
        "data_column": "Five_K_Time",      # Map to custom 5K field when available
        "metric_suffix": "",
        "fallback_value": "19:48",         # Centralized data-driven fallback standard
        "fallback_date": "2026-03-20",
        "calculation_type": "min"          # Looks for best timing splits
    }
]

# ==============================================================================
# 🏛️ MOUNTED DISPLAY CABINET CABINET HARDWARE REGISTRY
# ==============================================================================
# Define the visual styles, unlock badges, descriptions, and point weight tiers 
# for every milestone item rendered on the UI main page shelf.

DISPLAY_REWARDS_REGISTRY = [
    {
        "code": "weekly_miles_50",
        "title": "👑 Golden Century Club Medal",
        "icon": "🏅",
        "tier": "gold",
        "desc": "Awarded to endurance runners compiling over 50 miles in a single active week loop."
    },
    {
        "code": "weekly_miles_20",
        "title": "⚡ Silver Split Tier Star",
        "icon": "⭐",
        "tier": "sapphire",
        "desc": "Earned by hitting an intense, high-tempo 20-mile accumulation sequence."
    },
    {
        "code": "patch_cold_warrior",
        "title": "❄️ Sub-Freezing Frost Patch",
        "icon": "🛡️",
        "tier": "emerald",
        "desc": "Mounted automatically when training volume logs are validated below 32 degrees Fahrenheit."
    },
    {
        "code": "patch_streak_master",
        "title": "🔥 Overdrive Consistency Armor",
        "icon": "⚡",
        "tier": "gold",
        "desc": "Unlocked upon logging consecutive workout tracks without allowing your safety window to expire."
    }
]

