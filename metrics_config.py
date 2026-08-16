# metrics_config.py

FINAL_METRIC_CONFIG = {
    "single_run_patches": {
        "pillar_1_velocity": {
            "name": "Cruising Speed Nodes",
            "metric_key": "average_pace_seconds",  # Hooks into raw pace conversion math
            "is_inverted": True,                    # Lower numbers (faster paces) are better
            "tiers": [
                {"id": "rabbit", "name": "Rabbit Cruise Node", "icon": "🐇", "min_val": 446, "max_val": 495, "desc": "7:26 to 8:15 min/mi"},
                {"id": "deer", "name": "Deer Sprint Node", "icon": "🦌", "min_val": 346, "max_val": 445, "desc": "5:46 to 7:25 min/mi"},
                {"id": "cheetah", "name": "Cheetah Overdrive Core", "icon": "🐆", "min_val": 0, "max_val": 345, "desc": "5:45 min/mi or faster"}
            ]
        },
        "pillar_2_elevation": {
            "name": "Incline Adaptations",
            "metric_key": "total_elevation_gain_ft",
            "is_inverted": False,
            "tiers": [
                {"id": "marmot", "name": "Marmot Traction Unit", "icon": "🐿️", "min_val": 350, "max_val": 749, "desc": "350 to 749 ft climb"},
                {"id": "bighorn", "name": "Bighorn Torque Module", "icon": "🐏", "min_val": 750, "max_val": 1444, "desc": "750 to 1,444 ft climb"},
                {"id": "mountain_goat", "name": "Mountain Goat Apex Shield", "icon": "🐐", "min_val": 1445, "max_val": 99999, "desc": "1,445+ ft climb"}
            ]
        },
        "pillar_3_strategy": {
            "name": "Energy Management Units",
            "metric_key": "final_mile_kick_percent",
            "is_inverted": False,
            "tiers": [
                {"id": "second_wind", "name": "Second Wind System", "icon": "⏱️", "min_val": 2.5, "max_val": 5.4, "desc": "2.5% to 5.4% faster close"},
                {"id": "split_striker", "name": "Split Striker Module", "icon": "⏲️", "min_val": 5.5, "max_val": 9.9, "desc": "5.5% to 9.9% faster close"},
                {"id": "overdrive", "name": "Overdrive Finisher Core", "icon": "💥", "min_val": 10.0, "max_val": 100.0, "desc": "10.0%+ faster close"}
            ]
        },
        "pillar_4_volume": {
            "name": "Volume & Range Extenders",
            "metric_key": "total_distance_miles",
            "is_inverted": False,
            "tiers": [
                {"id": "stride_tracker", "name": "Stride Tracker Array", "icon": "👣", "min_val": 6.2, "max_val": 9.9, "desc": "6.2 to 9.9 miles"},
                {"id": "horizon_mapper", "name": "Horizon Mapper Processor", "icon": "🗺️", "min_val": 10.0, "max_val": 14.9, "desc": "10.0 to 14.9 miles"},
                {"id": "endurance_laurel", "name": "Endurance Laurel Shield", "icon": "📜", "min_val": 15.0, "max_val": 999.0, "desc": "15.0+ miles"}
            ]
        },
        "pillar_5_consistency": {
            "name": "Chrono-Discipline Matrix",
            "metric_key": "split_variance_seconds",  # Drops warm-up split automatically
            "is_inverted": True,
            "requires_min_distance": 3.0,
            "tiers": [
                {"id": "rhythm_sync", "name": "Rhythm Sync Engine", "icon": "🔰", "min_val": 6.6, "max_val": 11.0, "desc": "Splits vary < 11.0s"},
                {"id": "chrono_dial", "name": "Chrono Dial Unit", "icon": "🕰️", "min_val": 3.9, "max_val": 6.5, "desc": "Splits vary < 6.5s"},
                {"id": "metronome", "name": "Metronome Core Module", "icon": "🎯", "min_val": 0.0, "max_val": 3.8, "desc": "Splits vary < 3.8s"}
            ]
        },
        "pillar_6_cardiac": {
            "name": "Cardiac Efficiency Matrix",
            "metric_key": "aerobic_decoupling_percent",
            "is_inverted": True,
            "tiers": [
                {"id": "steady_engine", "name": "Steady Engine Patch", "icon": "💓", "min_val": 3.0, "max_val": 5.0, "desc": "Drift under 5.0%"},
                {"id": "iron_valve", "name": "Iron Valve Patch", "icon": "🩺", "min_val": 1.5, "max_val": 2.9, "desc": "Drift under 3.0%"},
                {"id": "cardio_cyborg", "name": "Cardio Cyborg Patch", "icon": "🫀", "min_val": 0.0, "max_val": 1.4, "desc": "Drift under 1.5%"}
            ]
        },
        "pillar_7_weather": {
            "name": "Thermo-Grit Matrix",
            "metric_key": "ambient_temp_f",
            "is_special_eval": True,  # Signals parser to check double-bounded climate fields
            "tiers": [
                {"id": "thermal_adaptor", "name": "Thermal Adaptor Patch", "icon": "🌡️", "desc": "Over 85°F or under 35°F"},
                {"id": "extreme_grit", "name": "Heatwave / Frostbite Patch", "icon": "🔥", "desc": "Over 95°F or under 20°F"},
                {"id": "elemental_sovereign", "name": "Elemental Sovereign Patch", "icon": "⛈️", "desc": "Over 100°F or under 10°F"}
            ]
        },
        "pillar_8_recovery": {
            "name": "Recovery Zone Discipline",
            "metric_key": "zone_1_2_duration_percent",
            "is_inverted": False,
            "tiers": [
                {"id": "controlled_stride", "name": "Controlled Stride Patch", "icon": "🛡️", "min_val": 75.0, "max_val": 89.9, "desc": "75%+ in Zone 1/2"},
                {"id": "aerobic_anchor", "name": "Aerobic Anchor Patch", "icon": "⚓", "min_val": 90.0, "max_val": 99.9, "desc": "90%+ in Zone 1/2"},
                {"id": "zen_master", "name": "Zen Master Patch", "icon": "🧘", "min_val": 100.0, "max_val": 100.0, "desc": "100% in Zone 1/2"}
            ]
        }
    },
    "trophy_cabinet": {
        "shelf_a_mileage": {
            "name": "Cumulative Mileage Shelf",
            "metric_key": "lifetime_distance_miles",
            "loop_increment": 500,
            "trophies": [
                {"id": "silver_globe", "threshold": 500, "name": "Silver Globe Trophy", "icon": "🥈"},
                {"id": "gold_monolith", "threshold": 1000, "name": "Gold Monolith Trophy", "icon": "🥇"},
                {"id": "platinum_crown", "threshold": 1500, "name": "Platinum Crown Trophy", "icon": "👑"},
                {"id": "diamond_apex", "threshold": 2000, "name": "Diamond Apex Trophy", "icon": "💎"}
            ]
        },
        "shelf_b_elevation": {
            "name": "Cumulative Elevation Shelf",
            "metric_key": "lifetime_elevation_ft",
            "loop_increment": 25000,
            "trophies": [
                {"id": "bronze_ridge", "threshold": 25000, "name": "Bronze Ridge Chalice", "icon": "🏆"},
                {"id": "silver_ascent", "threshold": 50000, "name": "Silver Ascent Shield", "icon": "🛡️"},
                {"id": "gold_alpine", "threshold": 75000, "name": "Gold Alpine Monolith", "icon": "🏔️"},
                {"id": "diamond_sky", "threshold": 100000, "name": "Diamond Sky Crown", "icon": "👑"}
            ]
        },
        "shelf_c_calories": {
            "name": "The Burn Menu Shelf",
            "metric_key": "lifetime_calories_burned",
            "loop_increment": 25000,
            "trophies": [
                {"id": "taco_platter", "threshold": 10000, "name": "The 10k Taco Platter Trophy", "icon": "🌮"},
                {"id": "ice_cream_sundae", "threshold": 25000, "name": "The 25k Ice Cream Sundae Trophy", "icon": "🍦"},
                {"id": "double_burger", "threshold": 50000, "name": "The 50k Double-Burger & Fries Trophy", "icon": "🍔"},
                {"id": "pizza_party", "threshold": 100000, "name": "The 100k Extra-Large Pizza Party Trophy", "icon": "🍕"}
            ]
        }
    }
}
# ==============================================================================
# 💎 TROPHY SHOWROOM CONFIGURATION MAPS & REWARDS MATRIX
# ==============================================================================

# 1. High-Fidelity RPG Style Gem Tier Registry
GEM_TIER_REGISTRY = {
    "emerald":  {"label": "❇️ Emerald",  "color": "#2ecc71", "bg": "rgba(46, 204, 113, 0.01)", "xp": 50},
    "sapphire": {"label": "🔹 Sapphire", "color": "#3498db", "bg": "rgba(52, 152, 219, 0.01)", "xp": 150},
    "amethyst": {"label": "🔮 Amethyst", "color": "#9b59b6", "bg": "rgba(155, 89, 182, 0.01)", "xp": 400},
    "diamond":  {"label": "💎 Diamond",  "color": "#f1c40f", "bg": "rgba(241, 196, 15, 0.02)", "xp": 1000}
}

# 2. Authentic 9-Tier Athletic Division Rank Settings
ATHLETIC_TIERS = [
    {"max_lvl": 3,  "title": "🔰 Junior Varsity Pacer"},
    {"max_lvl": 6,  "title": "🏃‍♂️ Varsity Captain"},
    {"max_lvl": 9,  "title": "⚡ Collegiate Division II Contender"},
    {"max_lvl": 12, "title": "🏟️ Collegiate Division I All-American"},
    {"max_lvl": 15, "title": "👟 Post-Collegiate Elite / Club Racer"},
    {"max_lvl": 18, "title": "🇺🇸 USATF Sub-National Competitor"},
    {"max_lvl": 21, "title": "🦅 USATF National Qualifier"},
    {"max_lvl": 24, "title": "🌍 World Athletics International Pro"},
    {"max_lvl": 99, "title": "👑 World Athletics Olympian Tier"}
]

# Constants for loss-aversion streak tracking and leveling thresholds
DEFENSE_WINDOW_DAYS = 7
XP_PER_LEVEL_THRESHOLD = 3000

# 3. Weekly Mileage Threshold Milestones
WEEKLY_MILEAGE_REWARDS = [
    {"miles": 40, "title": "Yellow Ribbon", "icon": "🎗️", "tier": "emerald", "desc": "Completed a 40-mile training week block."},
    {"miles": 45, "title": "Red Ribbon", "icon": "🎀", "tier": "emerald", "desc": "Completed a 45-mile training week block."},
    {"miles": 50, "title": "Blue Ribbon", "icon": "🎗️", "tier": "emerald", "desc": "Completed a 50-mile training week block."},
    {"miles": 55, "title": "Bronze Medal", "icon": "🥉", "tier": "sapphire", "desc": "Breached a 55-mile high-volume week."},
    {"miles": 60, "title": "Silver Medal", "icon": "🥈", "tier": "sapphire", "desc": "Breached a 60-mile high-volume week."},
    {"miles": 65, "title": "Gold Medal", "icon": "🥇", "tier": "sapphire", "desc": "Breached a 65-mile high-volume week."},
    {"miles": 70, "title": "Bronze Trophy", "icon": "🥉", "tier": "amethyst", "desc": "Secured a 70-mile elite tier calendar week."},
    {"miles": 75, "title": "Silver Trophy", "icon": "🥈", "tier": "amethyst", "desc": "Secured a 75-mile elite tier calendar week."},
    {"miles": 80, "title": "Gold Trophy", "icon": "🏆", "tier": "amethyst", "desc": "Secured an 80-mile elite tier calendar week."},
    {"miles": 85, "title": "Platinum Trophy", "icon": "👑", "tier": "diamond", "desc": "Earned the prestigious 85-mile crown award."},
    {"miles": 90, "title": "Sapphire & Silver Buckle", "icon": "🤠", "tier": "diamond", "desc": "Ultimate endurance milestone: 90 weekly miles."},
    {"miles": 95, "title": "Ruby & Gold Buckle", "icon": "🔱", "tier": "diamond", "desc": "Ultimate endurance milestone: 95 weekly miles."},
    {"miles": 100, "title": "Diamond & Platinum Buckle", "icon": "💎", "tier": "diamond", "desc": "Century Tier Legend: Completed a 100-mile week."}
]

# 4. Weekly Elevation Climb Threshold Milestones
WEEKLY_ELEVATION_REWARDS = [
    {"climb_ft": 1000, "title": "Hill Hopper Ribbon", "icon": "🔰", "tier": "emerald", "desc": "Accumulated 1,000 feet of vertical climb in a single week."},
    {"climb_ft": 2000, "title": "Ridge Climber Ribbon", "icon": "🎗️", "tier": "emerald", "desc": "Accumulated 2,000 feet of vertical climb in a single week."},
    {"climb_ft": 3000, "title": "Summit Scout Ribbon", "icon": "🎀", "tier": "emerald", "desc": "Accumulated 3,000 feet of vertical climb in a single week."},
    {"climb_ft": 4000, "title": "Vert-Seeker Medal", "icon": "🥉", "tier": "sapphire", "desc": "Breached 4,000 vertical feet in a high-elevation training week."},
    {"climb_ft": 5000, "title": "Alpine Finisher Medal", "icon": "🥈", "tier": "sapphire", "desc": "Breached 5,000 vertical feet in a high-elevation training week."},
    {"climb_ft": 6000, "title": "High-Pass Master Medal", "icon": "🥇", "tier": "sapphire", "desc": "Breached 6,000 vertical feet in a high-elevation training week."},
    {"climb_ft": 7000, "title": "Mountain Lion Trophy", "icon": "🥉", "tier": "amethyst", "desc": "Secured 7,000 feet of pure vertical gain inside a calendar week."},
    {"climb_ft": 8000, "title": "Skyrunner Trophy", "icon": "🥈", "tier": "amethyst", "desc": "Secured 8,000 feet of pure vertical gain inside a calendar week."},
    {"climb_ft": 9000, "title": "Cloud-Splitter Trophy", "icon": "🏆", "tier": "amethyst", "desc": "Secured 9,000 feet of pure vertical gain inside a calendar week."},
    {"climb_ft": 10000, "title": "Peak Crown Trophy", "icon": "👑", "tier": "diamond", "desc": "Earned the elite 10,000ft single-week vertical crown award."},
    {"climb_ft": 12000, "title": "Sapphire Peak Buckle", "icon": "🤠", "tier": "diamond", "desc": "Extreme mountaineering milestone: 12,000 weekly vertical feet."},
    {"climb_ft": 14000, "title": "Ruby Ridge Buckle", "icon": "🔱", "tier": "diamond", "desc": "Extreme mountaineering milestone: 14,000 weekly vertical feet."},
    {"climb_ft": 15000, "title": "Stratosphere Buckle", "icon": "💎", "tier": "diamond", "desc": "Vertical Legend: Cleared 15,000 feet of elevation gain in one week."}
]

# 5. Elite Lifelong Coveted Targets
COVETED_TARGETS = {
    "coveted_boston_qual": {
        "title": "The Blue Ribbon Unicorn",
        "icon": "🦄",
        "tier": "diamond",
        "distance_required": 26.22,
        "pace_target_seconds": 435, # 7:15 /mi pace rule target
        "desc": "Achieve a verified Boston Marathon qualifying pace profile standard."
    },
    "coveted_sub_four": {
        "title": "The Sub-4 Sovereign",
        "icon": "🌌",
        "tier": "diamond",
        "distance_required": 1.0,
        "pace_target_seconds": 240, # 4:00 /mi speed trial target
        "desc": "Break the historic 4-minute mile speed barrier on a verified course split."
    },
    "coveted_century_mount": {
        "title": "The Century Mount",
        "icon": "⛰️",
        "tier": "diamond",
        "distance_required": 62.14, # 100 Kilometers in miles
        "desc": "Log a single, continuous ultra-endurance training run exceeding 100K."
    },
    "coveted_immortal_streak": {
        "title": "The Immortal Streak",
        "icon": "♾️",
        "tier": "diamond",
        "streak_days_required": 365,
        "desc": "Maintain your active training log daily for a full calendar year loop."
    }
}

