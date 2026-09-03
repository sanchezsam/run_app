# =========================================================================
# 🧬 CHARACTER_ECONOMY_CONFIG: BACKEND REWARD & TRAINING STRESS CONTROL PANEL
# Centralizes all physical volume, elevation, and cardiovascular intensity formulas.
# =========================================================================
#
# 📐 TRAINING REWARD EQUATIONS UNDER THE HOOD:
# -------------------------------------------------------------------------
# 1. Workload Base XP = (Distance * xp_per_mile) + ((Elevation / 100) * xp_per_100ft_climb)
# 2. Total Run XP     = int(Workload Base XP * Heart Rate Zone Multiplier)
# 3. Base Run Gold    = int(Total Run XP * gold_per_xp_ratio) + weather_grit_bonus_gold
#
# =========================================================================


# 🧬 HEART RATE INTENSITY MASTER BALANCING CONTROL PANEL

# 🧬 UPDATE THIS BLOCK IN character_economy_config.py
HR_ZONE_CONFIG = {
    "zones": [
        {"max": 0,   "color": "#4A5568", "label": "No Data",           "text_color": "#FFFFFF"},
        {"max": 115, "color": "#A0AEC0", "label": "Zone 1 (Recovery)",  "text_color": "#1A202C"},
        # 🚨 SHIFTED DOWN: Changing 135 to 130 means 134 will now safely cross into Zone 3 Tempo!
        {"max": 130, "color": "#38A169", "label": "Zone 2 (Aerobic)",   "text_color": "#FFFFFF"},
        {"max": 150, "color": "#ECC94B", "label": "Zone 3 (Tempo)",     "text_color": "#1A202C"},
        {"max": 170, "color": "#ED8936", "label": "Zone 4 (Threshold)", "text_color": "#FFFFFF"},
        {"max": 999, "color": "#E53E3E", "label": "Zone 5 (Anaerobic)", "text_color": "#FFFFFF"}
    ]
}


CHARACTER_XP_CONFIG = {
    # 🏃‍♂️ Volume & Mechanical Progression Anchors
    "xp_per_mile": 0.8,
    "xp_per_100ft_climb": 0.5,
    
    # ❤️ Cardiovascular Intensity Multipliers
    "hr_zone_1_2_multiplier": 1.00,  # HR < 140 (Recovery Pace)
    "hr_zone_3_multiplier":   1.15,  # HR 140-155 (Aerobic Tempo / Marathon)
    "hr_zone_4_5_multiplier": 1.30,  # HR > 155 (Lactate Threshold / Anaerobic Vo2)
    
    # 🪙 Dynamic Ingestion Conversion Gates
    "gold_per_xp_ratio": 1.60,       # 160% Conversion (250 XP -> 400 Gold Baseline)
    
    # ❄️🔥 Weather Grit Environment Bonuses
    "weather_grit_bonus_gold": 15,
    "weather_freezing_threshold_f": 32.0,
    "weather_heatwave_threshold_f": 90.0,

    # ⏳ PHYSIOLOGICAL TIME-DECAY MATRIX CONSTANTS
    # Defines the specific attribute penalties applied based on days away from active training.
    "decay_tiers": {
        "peak_window_days": 5,
        "minor_decay_days": 14,
        "medium_decay_days": 30,
        "severe_decay_days": 90,
        
        # Penalty Subtractions (Stamina, Speed, Climbing)
        "tier_1_penalties": (0.0, 0.0, 0.0),    # Inactive <= 5 days
        "tier_2_penalties": (1.0, 2.0, 0.0),    # Inactive <= 14 days
        "tier_3_penalties": (2.5, 4.0, 1.0),    # Inactive <= 30 days
        "tier_4_penalties": (4.0, 6.0, 3.5),    # Inactive <= 90 days
        "tier_5_penalties": (8.0, 8.0, 8.0)     # Inactive > 90 days (Chronic)
    },

    # 📈 CONTINUOUS WORKLOAD PERFORMANCE DEFICIT SCALARS
    # Scales trait attrition smoothly based on your exact volume retention curve.
    "continuous_workload_taper": {
        "peak_monthly_target_miles": 400.0,  # Forces dynamic, continuous scaling adjustments
        "max_atrophy_penalty_cap":    5.0,    # Max level points lost if monthly volume hits 0
        "speed_decay_sensitivity":    1.2     # Speed/Nitro drops 20% faster than base endurance
    }
}
# =========================================================================
