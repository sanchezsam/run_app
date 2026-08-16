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

