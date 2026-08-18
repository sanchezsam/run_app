# -*- coding: utf-8 -*-
# ==============================================================================
# 🏪 PRO SHOP & AVATAR GARAGE CONFIGURATION MATRICES
# ==============================================================================
# Add or modify unlockable themes, user interface aesthetics, and badge perks.
# The rendering pipeline hooks into this registry dynamically based on your athlete level.

PRO_SHOP_SKINS_REGISTRY = [
    {
        "unlock_level": 1,
        "skin_id": "theme_pacer_green",
        "title": "🔰 Standard Pacer Green",
        "badge": "🟢 JUNIOR_PACER",
        "accent_color": "#2ecc71",
        "sidebar_bg": "rgba(46, 204, 113, 0.02)",
        "perk_desc": "Default UI skin issued to all tier contenders upon log creation."
    },
    {
        "unlock_level": 5,
        "skin_id": "theme_collegiate_blue",
        "title": "⚡ Collegiate Division Blue",
        "badge": "🦅 ALL_AMERICAN",
        "accent_color": "#3498db",
        "sidebar_bg": "rgba(52, 152, 219, 0.05)",
        "perk_desc": "Unlocks custom collegiate profile trims and sleek performance cards."
    },
    {
        "unlock_level": 10,
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
    'Nike Vaporfly 4%': {'cost': 120, 'cat': 'Footwear', 'weather': 'All-Weather', 'desc': 'Carbon-plated shoe. Massive Sprint Velocity physics bonus.'},
    'adidas UltraBoost': {'cost': 95, 'cat': 'Footwear', 'weather': 'All-Weather', 'desc': 'Premium cushioning foam. Absorbs high track mileage.'},
    'Hoka One One Speedgoat': {'cost': 110, 'cat': 'Footwear', 'weather': 'All-Weather', 'desc': 'Maximalist trail tread. Best for mountain torque.'},
    'ASICS Metaspeed Sky+': {'cost': 145, 'cat': 'Footwear', 'weather': 'All-Weather', 'desc': 'Elongated stride efficiency. Elite scaling for high-velocity drivers.'},
    
    # --- SUNGLASSES ---
    'Oakley Speed Jacket Sunglasses': {'cost': 45, 'cat': 'Sunglasses', 'weather': 'All-Weather', 'desc': 'Aerodynamic shatterproof frames. Maximizes tracking accuracy.'},
    '100% Speedcraft Shaded Shields': {'cost': 55, 'cat': 'Sunglasses', 'weather': 'All-Weather', 'desc': 'Expanded peripheral vision. High-impact arcade neon visibility lenses.'},
    'Goodr No Bounce Optics': {'cost': 20, 'cat': 'Sunglasses', 'weather': 'All-Weather', 'desc': 'Lightweight textured frame grip. Eliminates slipping during sprint cadence loops.'},
    
    # --- HEAD GEAR ---
    'Arcade Neon Headband': {'cost': 20, 'cat': 'Head Gear', 'weather': 'All-Weather', 'desc': 'Retro sweat protection. Adds style and focus multipliers.'},
    'Ciele Athletics GOCap': {'cost': 25, 'cat': 'Head Gear', 'weather': 'All-Weather', 'desc': 'Lightweight collapsible mesh race cap. Deflects extreme canyon sun glare.'},
    'Buff Merino Thermal Wrap': {'cost': 22, 'cat': 'Head Gear', 'weather': 'Winter Jacket (Cold)', 'desc': 'Insulates head and neck vitals. Solid for high altitude winter stages.'},
    
    # --- SINGLETS ---
    'Elite Aero-Grid Singlet': {'cost': 40, 'cat': 'Singlets', 'weather': 'All-Weather', 'desc': 'Weightless track singlet. Decreases wind drag factors.'},
    'Nike Dri-FIT ADV Aeroswift': {'cost': 70, 'cat': 'Singlets', 'weather': 'All-Weather', 'desc': 'Engineered precision breathability zones. Minimizes heat build-up blockades.'},
    
    # --- JACKETS ---
    'Patagonia Houdini Windbreaker': {'cost': 75, 'cat': 'Jackets', 'weather': 'Windbreaker (Windy)', 'desc': 'Featherlight ripstop shell. Completely negates wind resistance penalties.'},
    'Arc\'teryx Norvan Gore-Tex Jacket': {'cost': 150, 'cat': 'Jackets', 'weather': 'Rain Jacket (Wet)', 'desc': 'Fully seam-sealed waterproof barrier. Prevents tracking friction in severe storms.'},
    'The North Face Summit Winter Parka': {'cost': 195, 'cat': 'Jackets', 'weather': 'Winter Jacket (Cold)', 'desc': 'Advanced down insulation pack. Sustains core temperatures during alpine winter stages.'},
    'Gore-Tex Windstopper Shell': {'cost': 85, 'cat': 'Jackets', 'weather': 'Winter Jacket (Cold)', 'desc': 'Hardcore weather shield. Insulates core vitals across alpine storms.'},

    # --- SHORTS ---
    'Split Training Track Shorts': {'cost': 35, 'cat': 'Shorts', 'weather': 'All-Weather', 'desc': 'Classic maximum range of motion splits. Improves cadence loops.'},
    'Salomon S/Lab Ultra Skirt-Short': {'cost': 95, 'cat': 'Shorts', 'weather': 'Rain Jacket (Wet)', 'desc': 'Elite long-range trail armor. Specialized for rugged canyon operations.'},
    
    # --- PANTS ---
    'Nike Phenom Elite Wind Pants': {'cost': 70, 'cat': 'Pants', 'weather': 'Windbreaker (Windy)', 'desc': 'Tapered aerodynamic track pants. Stabilizes leg stride cycles during heavy gusts.'},
    'adidas Terrex Waterproof Pants': {'cost': 110, 'cat': 'Pants', 'weather': 'Rain Jacket (Wet)', 'desc': 'Hydrophobic storm weave. Deflects mud and water log drag multipliers.'},
    'Under Armour ColdGear Infrared Tights': {'cost': 85, 'cat': 'Pants', 'weather': 'Winter Jacket (Cold)', 'desc': 'Thermo-conductive inner lining that absorbs and retains lower body muscle heat.'},
    'Compression Racing Tights': {'cost': 55, 'cat': 'Pants', 'weather': 'Winter Jacket (Cold)', 'desc': 'Streamlined thermal tights optimizing lower body blood flow.'},

    # --- WATCHES ---
    'Garmin Forerunner Pro': {'cost': 85, 'cat': 'Watches', 'weather': 'All-Weather', 'desc': 'Surgical track splitting. Smooths out raw pacing lines.'},
    'Coros Pace Performance Matrix': {'cost': 70, 'cat': 'Watches', 'weather': 'All-Weather', 'desc': 'Weightless satellite capture engine. Elite driver telemetry sync.'},
    'Apple Watch Ultra Matrix': {'cost': 160, 'cat': 'Watches', 'weather': 'All-Weather', 'desc': 'Titanium diving cockpit hull. Dual-frequency precision tracking.'}
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
        "icon": "👟",
        "desc": "Guarantees a permanent drop or rank tune to an entry-level asset.",
        "odds": "🟢 100% Entry Tier Item Drop"
    },
    {
        "id": "sb_performance",
        "name": "Performance Track Chest",
        "cost": 90,
        "icon": "⚡",
        "desc": "Blends high probability low-tier items with professional caliber unlocks.",
        "odds": "🟢 Entry Tier: 85% | 🟡 Professional Tier: 15%"
    },
    {
        "id": "sb_champ",
        "name": "Championship Grand Chest",
        "cost": 180,
        "icon": "👑",
        "desc": "High prestige loot table prioritizing high cost elite telemetry equipment blocks.",
        "odds": "🟢 Entry: 50% | 🟡 Professional: 35% | 🔴 Elite Tier: 15%"
    },
    {
        "id": "sb_focus",
        "name": "🎯 Slot Focus Chest",
        "cost": 120,
        "icon": "🎯",
        "desc": "Focuses all drop probabilities strictly into the single gear class selected below.",
        "odds": "⭐ 100% Targeted Equipment Category Focus Mapping"
    },
    {
        "id": "sb_catchup",
        "name": "🩹 Trailing Catch-Up Chest",
        "cost": 140,
        "icon": "🩹",
        "desc": "Scans your locker asset array and targets whichever acquired item has the lowest rank setup.",
        "odds": "🩹 100% Core Focus on Under-Leveled Assets"
    },
    {
        "id": "sb_proto",
        "name": "🧪 Prototype Lab Chest",
        "cost": 175,
        "icon": "🧪",
        "desc": "High-risk experimental hardware design test chest.",
        "odds": "💥 Misfit Failure: 40% | 🟡 Standard Calibration (+1 Rank): 45% | 🎰 Quantum Breakthrough (+4 Ranks!): 15%"
    },
    {
        "id": "sb_palette",
        "name": "🎨 Paint Palette Box",
        "cost": 30,
        "icon": "🎨",
        "desc": "Rolls a random item and custom spray paint coloring. If you already own that exact color combo, it results in a complete miss with no reward.",
        "odds": "🌈 100% Random Colorway Combo Profile Roll (Duplicates yield nothing)"
    }
]
