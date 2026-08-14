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

