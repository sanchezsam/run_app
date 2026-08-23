# -*- coding: utf-8 -*-
"""
ATHLETIC PRO SHOP & EQUIPMENT CONFIGURATION REGISTRY (pro_shop_config.py)
Centrally manages unlockable user interface skins, performance gear attributes,
and custom colorway mystery box rewards. All automotive phrasing completely removed.
"""

# =========================================================================
# ⚙️ PRO SHOP GLOBAL ECONOMY MASTER BALANCING CONTROL PANEL
# Adjust any value here to instantly re-scale shop pricing and requirements structures.
# =========================================================================
SHOP_ECONOMY_CONFIG = {
    # 🏃‍♂️ XP Progression Anchors
    "xp_per_mile": 0.8,
    "xp_per_100ft_climb": 0.5,
    
    # ❤️ Heart Rate Intensity Multipliers
    "hr_zone_1_2_multiplier": 1.00,  
    "hr_zone_3_multiplier":   1.15,  
    "hr_zone_4_5_multiplier": 1.30,  
    
    # 🪙 Currency Scaling Factors
    "gold_per_xp_ratio": 1.60,       
    
    # ❄️🔥 Weather Grit Environment Gates
    "weather_grit_bonus_gold": 15,
    "weather_freezing_threshold_f": 32.0,
    "weather_heatwave_threshold_f": 90.0,

    # 🏋️‍♂️ GLOBAL GEAR OPTIMIZATION COST SCALARS (RANK 1 TO 10 PROGRESSION)
    "gear_rank_progression_scalar": 0.5, 
    
    # 🎨 Cosmetic Color Palette Shop Costs
    "color_tier_costs": {
        "Common": 15,       
        "Rare": 125,        
        "Epic": 250,        
        "Legendary": 500    
    },

    # 🎭 RE-BALANCED ACCENT THEME SKIN UNLOCK THRESHOLDS
    # Keeps rewards perfectly achievable within your new exponential leveling scales.
    "skin_milestones": {
        "Common_Tier": 1,      # Unlocked right at character initialization
        "Division_Tier": 4,    # Unlocked midway through your training progression
        "Prestige_Tier": 9     # Max Level 9 Endgame achievement milestone reward
    }
}

# ==============================================================================
# 🏪 PRO SHOP & AVATAR LOCKER CONFIGURATION MATRICES (DYNAMIC SYNCHRONIZED)
# ==============================================================================
# The rendering pipeline hooks into this registry dynamically based on your athlete level.
PRO_SHOP_SKINS_REGISTRY = [
    {
        "unlock_level": SHOP_ECONOMY_CONFIG["skin_milestones"]["Common_Tier"],
        "skin_id": "theme_pacer_green",
        "title": "🔰 Standard Pacer Green",
        "badge": "🟢 JUNIOR_PACER",
        "accent_color": "#2ecc71",
        "sidebar_bg": "rgba(46, 204, 113, 0.02)",
        "perk_desc": "Default UI skin issued to all tier contenders upon log creation."
    },
    {
        "unlock_level": SHOP_ECONOMY_CONFIG["skin_milestones"]["Division_Tier"],
        "skin_id": "theme_collegiate_blue",
        "title": "⚡ Collegiate Division Blue",
        "badge": "🦅 ALL_AMERICAN",
        "accent_color": "#3498db",
        "sidebar_bg": "rgba(52, 152, 219, 0.05)",
        "perk_desc": "Unlocks custom collegiate profile trims and sleek performance cards."
    },
    {
        "unlock_level": SHOP_ECONOMY_CONFIG["skin_milestones"]["Prestige_Tier"],
        "skin_id": "theme_prestige_gold",
        "title": "🏆 Premium Olympian Gold",
        "badge": "👑 ELITE_OLYMPIAN",
        "accent_color": "#f1c40f",
        "sidebar_bg": "rgba(241, 196, 15, 0.06)",
        "perk_desc": "High prestige aesthetic shift providing elite medal presentation decks."
    }
]

# ==============================================================================
# 🛍️ MASTER EQUIPMENT REPOSITORY CATALOG
# ==============================================================================
gear_catalog = {
    # --- FOOTWEAR ---
    'Nike Vaporfly 4%': {
        'cost': 120, 'cat': 'Footwear', 'weather': 'All-Weather', 'icon': '👟',
        'img_path': 'images/pro_shop/nike_vaporfly_4%.png',
        'desc': 'Carbon-plated shoe. Massive Sprint Velocity physics bonus.'
    },
    'adidas UltraBoost': {
        'cost': 95, 'cat': 'Footwear', 'weather': 'All-Weather', 'icon': '👟',
        'img_path': 'images/pro_shop/adidas_ultraboost.png',
        'desc': 'Premium cushioning foam. Absorbs high track mileage.'
    },
    'Hoka One One Speedgoat': {
        'cost': 110, 'cat': 'Footwear', 'weather': 'All-Weather', 'icon': '🥾',
        'img_path': 'images/pro_shop/hoka_one_one_speedgoat.png',
        'desc': 'Maximalist trail tread. Best for mountain traction and vertical power.'
    },
    'ASICS Metaspeed Sky+': {
        'cost': 145, 'cat': 'Footwear', 'weather': 'All-Weather', 'icon': '🚀',
        'img_path': 'images/pro_shop/asics_metaspeed_sky+.png',
        'desc': 'Elongated stride efficiency. Elite scaling for high-velocity runners.'
    },
    
    # --- SUNGLASSES ---
    'Oakley Speed Jacket Sunglasses': {
        'cost': 45, 'cat': 'Sunglasses', 'weather': 'All-Weather', 'icon': '🕶️',
        'img_path': 'images/pro_shop/oakley_speed_jacket_sunglasses.png',
        'desc': 'Aerodynamic shatterproof frames. Maximizes tracking accuracy.'
    },
    '100% Speedcraft Shaded Shields': {
        'cost': 55, 'cat': 'Sunglasses', 'weather': 'All-Weather', 'icon': '😎',
        'img_path': 'images/pro_shop/100%_speedcraft_shaded_shields.png',
        'desc': 'Expanded peripheral vision. High-impact arcade neon visibility lenses.'
    },
    'Goodr No Bounce Optics': {
        'cost': 20, 'cat': 'Sunglasses', 'weather': 'All-Weather', 'icon': '🕶️',
        'img_path': 'images/pro_shop/goodr_no_bounce_optics.png',
        'desc': 'Lightweight textured frame grip. Eliminates slipping during sprint cadence loops.'
    },
    
    # --- HEAD GEAR ---
    'Arcade Neon Headband': {
        'cost': 20, 'cat': 'Head Gear', 'weather': 'All-Weather', 'icon': '🔲',
        'img_path': 'images/pro_shop/arcade_neon_headband.png',
        'desc': 'Retro sweat protection. Adds style and focus multipliers.'
    },
    'Ciele Athletics GOCap': {
        'cost': 25, 'cat': 'Head Gear', 'weather': 'All-Weather', 'icon': '🧢',
        'img_path': 'images/pro_shop/ciele_athletics_gocap.png',
        'desc': 'Lightweight collapsible mesh race cap. Deflects extreme canyon sun glare.'
    },
    'Buff Merino Thermal Wrap': {
        'cost': 22, 'cat': 'Head Gear', 'weather': 'Winter Jacket (Cold)', 'icon': '🧣',
        'img_path': 'images/pro_shop/buff_merino_thermal_wrap.png',
        'desc': 'Insulates head and neck vitals. Solid for high altitude winter stages.'
    },
    
    # --- SINGLETS ---
    'Elite Aero-Grid Singlet': {
        'cost': 40, 'cat': 'Singlets', 'weather': 'All-Weather', 'icon': '🎽',
        'img_path': 'images/pro_shop/elite_aero_grid_singlet.png',
        'desc': 'Weightless track singlet. Decreases wind drag factors.'
    },
    'Nike Dri-FIT ADV Aeroswift': {
        'cost': 70, 'cat': 'Singlets', 'weather': 'All-Weather', 'icon': '🔥',
        'img_path': 'images/pro_shop/nike_dri_fit_adv_aeroswift.png',
        'desc': 'Engineered precision breathability zones. Minimizes heat build-up blockades.'
    },
    
    # --- JACKETS ---
    'Patagonia Houdini Windbreaker': {
        'cost': 75, 'cat': 'Jackets', 'weather': 'Windbreaker (Windy)', 'icon': '🧥',
        'img_path': 'images/pro_shop/patagonia_houdini_windbreaker.png',
        'desc': 'Featherlight ripstop shell. Completely negates wind resistance penalties.'
    },
    'Arc\'teryx Norvan Gore-Tex Jacket': {
        'cost': 150, 'cat': 'Jackets', 'weather': 'Rain Jacket (Wet)', 'icon': '🧥',
        'img_path': 'images/pro_shop/arctyx_norvan_gore_tex_jacket.png',
        'desc': 'Fully seam-sealed waterproof barrier. Prevents tracking friction in severe storms.'
    },
    'The North Face Summit Winter Parka': {
        'cost': 195, 'cat': 'Jackets', 'weather': 'Winter Jacket (Cold)', 'icon': '🧥',
        'img_path': 'images/pro_shop/the_north_face_summit_winter_parka.png',
        'desc': 'Advanced down insulation pack. Sustains core temperatures during alpine winter stages.'
    },
    'Gore-Tex Windstopper Shell': {
        'cost': 85, 'cat': 'Jackets', 'weather': 'Winter Jacket (Cold)', 'icon': '🧥',
        'img_path': 'images/pro_shop/gore_tex_windstopper_shell.png',
        'desc': 'Hardcore weather shield. Insulates core vitals across alpine storms.'
    },

    # --- SHORTS ---
    'Split Training Track Shorts': {
        'cost': 35, 'cat': 'Shorts', 'weather': 'All-Weather', 'icon': '🩳',
        'img_path': 'images/pro_shop/split_training_track_shorts.png',
        'desc': 'Classic maximum range of motion splits. Improves cadence loops.'
    },
    'Salomon S/Lab Ultra Skirt-Short': {
        'cost': 95, 'cat': 'Shorts', 'weather': 'Rain Jacket (Wet)', 'icon': '🎒',
        'img_path': 'images/pro_shop/salomon_slab_ultra_skirt_short.png',
        'desc': 'Elite long-range trail armor. Specialized for rugged canyon operations.'
    },
    
    # --- PANTS ---
    'Nike Phenom Elite Wind Pants': {
        'cost': 70, 'cat': 'Pants', 'weather': 'Windbreaker (Windy)', 'icon': '👖',
        'img_path': 'images/pro_shop/nike_phenom_elite_wind_pants.png',
        'desc': 'Tapered aerodynamic track pants. Stabilizes leg stride cycles during heavy gusts.'
    },
    'adidas Terrex Waterproof Pants': {
        'cost': 110, 'cat': 'Pants', 'weather': 'Rain Jacket (Wet)', 'icon': '👖',
        'img_path': 'images/pro_shop/adidas_terrex_waterproof_pants.png',
        'desc': 'Hydrophobic storm weave. Deflects mud and water log drag multipliers.'
    },
    'Under Armour ColdGear Infrared Tights': {
        'cost': 85, 'cat': 'Pants', 'weather': 'Winter Jacket (Cold)', 'icon': '👖',
        'img_path': 'images/pro_shop/under_armour_coldgear_infrared_tights.png',
        'desc': 'Thermo-conductive inner lining that absorbs and retains lower body muscle heat.'
    },
    'Compression Racing Tights': {
        'cost': 55, 'cat': 'Pants', 'weather': 'Winter Jacket (Cold)', 'icon': '👖',
        'img_path': 'images/pro_shop/compression_racing_tights.png',
        'desc': 'Streamlined thermal tights optimizing lower body blood flow.'
    },

    # --- WATCHES ---
    'Garmin Forerunner Pro': {
        'cost': 85, 'cat': 'Watches', 'weather': 'All-Weather', 'icon': '⌚',
        'img_path': 'images/pro_shop/garmin_forerunner_pro.png',
        'desc': 'Surgical track splitting. Smooths out raw pacing lines.'
    },
    'Coros Pace Performance Matrix': {
        'cost': 70, 'cat': 'Watches', 'weather': 'All-Weather', 'icon': '⏱️',
        'img_path': 'images/pro_shop/coros_pace_performance_matrix.png',
        'desc': 'Weightless satellite capture engine. Elite runner telemetry sync.'
    },
    'Apple Watch Ultra Matrix': {
        'cost': 160, 'cat': 'Watches', 'weather': 'All-Weather', 'icon': '⌚',
        'img_path': 'images/pro_shop/apple_watch_ultra_matrix.png',
        'desc': 'Titanium diving watch casing. Dual-frequency precision tracking.'
    }
}

# ==============================================================================
# 🎰 MYSTERY CHEST LOOT SYSTEM BLUEPRINTS
# ==============================================================================
# Declares cost requirements, iconography, description summaries, and loot table metadata
# hooks processed by the automated random unboxing engine loops.

shop_boxes = [
    {
        "id": "sb_apparel",
        "name": "Apparel Mystery Chest",
        "cost": 40,
        "icon": "箱",
        "img_path": "images/pro_shop/box_apparel.png",
        "desc": "Guarantees a permanent drop or rank upgrade to an entry-level asset.",
        "odds": "🟢 100% Entry Tier Item Drop"
    },
    {
        "id": "sb_performance",
        "name": "Performance Track Chest",
        "cost": 90,
        "icon": "⚡",
        "img_path": "images/pro_shop/box_performance.png",
        "desc": "Blends high probability low-tier items with professional caliber unlocks.",
        "odds": "🟢 Entry Tier: 85% | 🟡 Professional Tier: 15%"
    },
    {
        "id": "sb_champ",
        "name": "Championship Grand Chest",
        "cost": 180,
        "icon": "👑",
        "img_path": "images/pro_shop/box_champ.png",
        "desc": "High prestige loot table prioritizing high cost elite telemetry equipment blocks.",
        "odds": "🟢 Entry: 50% | 🟡 Professional: 35% | 🔴 Elite Tier: 15%"
    },
    {
        "id": "sb_focus",
        "name": "🎯 Slot Focus Chest",
        "cost": 120,
        "icon": "🎯",
        "img_path": "images/pro_shop/box_focus.png",
        "desc": "Focuses all drop probabilities strictly into the single gear class selected below.",
        "odds": "⭐ 100% Targeted Equipment Category Focus Mapping"
    },
    {
        "id": "sb_catchup",
        "name": "🩹 Trailing Catch-Up Chest",
        "cost": 140,
        "icon": "🩹",
        "img_path": "images/pro_shop/box_catchup.png",
        "desc": "Scans your locker asset array and targets whichever acquired item has the lowest optimization rank.",
        "odds": "🩹 100% Core Focus on Under-Leveled Assets"
    },
    {
        "id": "sb_proto",
        "name": "🧪 Prototype Lab Chest",
        "cost": 175,
        "icon": "🧪",
        "img_path": "images/pro_shop/box_proto.png",
        "desc": "High-risk experimental apparel gear design test chest.",
        "odds": "💥 Misfit Failure: 40% | 🟡 Standard Calibration (+1 Rank): 45% | 🎰 Quantum Breakthrough (+4 Ranks!): 15%"
    },
    {
        "id": "sb_palette",
        "name": "🎨 Paint Palette Box",
        "cost": 30,
        "icon": "🎨",
        "img_path": "images/pro_shop/box_palette.png",
        "desc": "Rolls a random item and premium custom colorway styling. If you already own that exact color combo, it results in a complete miss with no reward.",
        "odds": "🌈 100% Random Colorway Combo Profile Roll (Duplicates yield nothing)"
    }
]

