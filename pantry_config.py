# -*- coding: utf-8 -*-

TROPHY_TIERS = [
    {'tier_idx': 0, 'name': 'Bronze Trophy', 'suffix': '🥉', 'level': 1},
    {'tier_idx': 1, 'name': 'Silver Trophy', 'suffix': '🥈', 'level': 2},
    {'tier_idx': 2, 'name': 'Gold Trophy', 'suffix': '🥇', 'level': 3},
    {'tier_idx': 3, 'name': 'Platinum Trophy', 'suffix': '💎', 'level': 4},
    {'tier_idx': 4, 'name': 'Coveted Belt', 'suffix': '🏆 Belt', 'level': 5}
]

PANTRY_MENU = {
    '🥟 Chinese Cuisine': {
        'flag': '🇨🇳',
        'items': [
            {'id': 'dumpling', 'name': 'Dumpling', 'portion': '1 Steamed Pork Piece', 'cost': 60, 'emoji': '🥟', 'thresholds': [5, 10, 15, 20, 25]},
            {'id': 'takeout_box', 'name': 'Takeout Box Lo Mein', 'portion': '1 Tofu Entree', 'cost': 650, 'emoji': '🥡', 'thresholds': [5, 10, 15, 20, 25]},
            {'id': 'ramen_bowl', 'name': 'Ramen Noodle Bowl', 'portion': '1 Restaurant Serving with Broth', 'cost': 850, 'emoji': '🍜', 'thresholds': [5, 10, 15, 20, 25]},
            {'id': 'rice_bowl', 'name': 'Rice Bowl', 'portion': '1 Cup Cooked Rice', 'cost': 215, 'emoji': '🍚', 'thresholds': [5, 10, 15, 20, 25]},
            {'id': 'fortune_cookie', 'name': 'Fortune Cookie', 'portion': '1 Piece', 'cost': 35, 'emoji': '🥠', 'thresholds': [3, 6, 12, 18, 24]},
            {'id': 'bubble_tea', 'name': 'Bubble Tea Boba', 'portion': '16oz Sweetened Cream', 'cost': 450, 'emoji': '🧋', 'thresholds': [3, 6, 12, 18, 24]},
            {'id': 'chopsticks', 'name': 'Chopsticks', 'portion': 'Utility Item', 'cost': 5, 'emoji': '🥢', 'thresholds': [3, 6, 12, 18, 24]}        ]
    },
    '🌮 Mexican Cuisine': {
        'flag': '🇲🇽',
        'items': [
            {'id': 'taco', 'name': 'Taco', 'portion': '1 Corn Tortilla Beef/Chicken', 'cost': 220, 'emoji': '🌮', 'thresholds': [5, 10, 15, 20, 25]},
            {'id': 'burrito', 'name': 'Burrito', 'portion': '1 Large Bean & Beef Wrap', 'cost': 700, 'emoji': '🌯', 'thresholds': [5, 10, 15, 20, 25]},
            {'id': 'tamale', 'name': 'Tamale', 'portion': '1 Pork Steamed Husk Corn', 'cost': 310, 'emoji': '🫔', 'thresholds': [5, 10, 15, 20, 25]},
            {'id': 'avocado', 'name': 'Avocado', 'portion': '1 Whole Medium Avocado', 'cost': 320, 'emoji': '🥑', 'thresholds': [3, 6, 12, 18, 24]},
            {'id': 'mexican_coke', 'name': 'Mexican Coke', 'portion': '1 Glass Bottle 12oz', 'cost': 150, 'emoji': '🥤', 'thresholds': [3, 6, 12, 18, 24]},
            {'id': 'horchata', 'name': 'Horchata', 'portion': '32oz Rice Milk Drink', 'cost': 440, 'emoji': '🍹', 'thresholds': [3, 6, 12, 18, 24]}        ]
    },
    '🍕 Italian Cuisine': {
        'flag': '🇮🇹',
        'items': [
            {'id': 'pizza_slice', 'name': 'Pizza Slice', 'portion': '1 Crust Pepperoni', 'cost': 320, 'emoji': '🍕', 'thresholds': [5, 10, 15, 20, 25]},
            {'id': 'spaghetti', 'name': 'Spaghetti Pasta', 'portion': '1 Cup Cooked Marinara', 'cost': 300, 'emoji': '🍝', 'thresholds': [3, 6, 12, 18, 24]},
            {'id': 'green_salad', 'name': 'Green Salad', 'portion': '1 Bowl Cream Dressing', 'cost': 250, 'emoji': '🥗', 'thresholds': [3, 6, 12, 18, 24]},
            {'id': 'cheese_block', 'name': 'Cheese Block', 'portion': '1.5 oz Cheddar Cheese', 'cost': 170, 'emoji': '🧀', 'thresholds': [3, 6, 12, 18, 24]}        ]
    },
    '🍔 American Diner Cuisine': {
        'flag': '🇺🇸',
        'items': [
            {'id': 'hamburger', 'name': 'Hamburger', 'portion': 'Single Patty with Cheese', 'cost': 550, 'emoji': '🍔', 'thresholds': [5, 10, 15, 20, 25]},
            {'id': 'steak_cut', 'name': 'Steak Cut Meat', 'portion': '6 oz Cooked Sirloin', 'cost': 480, 'emoji': '🥩', 'thresholds': [5, 10, 15, 20, 25]},
            {'id': 'french_fries', 'name': 'French Fries', 'portion': '1 Medium Fry Basket', 'cost': 400, 'emoji': '🍟', 'thresholds': [3, 6, 12, 18, 24]},
            {'id': 'hot_dog', 'name': 'Hot Dog', 'portion': '1 Ballpark Beef Frank', 'cost': 350, 'emoji': '🌭', 'thresholds': [3, 6, 12, 18, 24]},
            {'id': 'chocolate_milkshake', 'name': 'Thick Chocolate Milkshake', 'portion': '1 Large 16oz Diner Glass', 'cost': 650, 'emoji': '🥤', 'thresholds': [3, 6, 12, 18, 24]}        ]
    },
    '🧁 Coveted Desserts': {
        'flag': '🍨',
        'items': [
            {'id': 'ice_cream', 'name': 'Ice Cream Cone', 'portion': 'Double Waffle Cone', 'cost': 450, 'emoji': '🍦', 'thresholds': [4, 8, 12, 16, 20]},
            {'id': 'cake_slice', 'name': 'Slice of Cake', 'portion': 'Fudge Chocolate Cake', 'cost': 520, 'emoji': '🍰', 'thresholds': [4, 8, 12, 16, 20]},
            {'id': 'donut', 'name': 'Glazed Donut', 'portion': '1 Large Bakery Donut', 'cost': 380, 'emoji': '🍩', 'thresholds': [4, 8, 12, 16, 20]},
            {'id': 'cookie', 'name': 'Soft-Baked Cookie', 'portion': '1 Chocolate Chip Bakery Item', 'cost': 290, 'emoji': '🍪', 'thresholds': [4, 8, 12, 16, 20]}        ]
    }
}
# Append this directly to your pantry_config.py file:
VAULT_BOX_REGISTRY = {
    "core": [
        {"id": "box_bronze", "name": "Bronze Box", "cost": 150, "icon": "📦", "type": "core", "desc": "100% chance to drop Low-Value items (costing ≤ 250 kcal). Safe structural baseline.", "odds": "🟢 Low-Value items (≤ 250 kcal): 100%"},
        {"id": "box_silver", "name": "Silver Box", "cost": 400, "icon": "💎", "type": "core", "desc": "90% chance for Low-Value items (≤ 250 kcal) | 10% chance for Mid-Value items (251-600 kcal).", "odds": "🟢 Low-Value (≤ 250 kcal): 90%\n🟡 Mid-Value (251-600 kcal): 10%"},
        {"id": "box_gold", "name": "Gold Box", "cost": 900, "icon": "👑", "type": "core", "desc": "60% Low-Value | 30% Mid-Value | 10% High-Value items (> 600 kcal) premium jackpot tier.", "odds": "🟢 Low-Value: 60%\n🟡 Mid-Value: 30%\n🔴 High-Value: 10%"},
        {"id": "box_platinum", "name": "Platinum Box", "cost": 2000, "icon": "💿", "type": "core", "desc": "58% Low | 30% Mid | 10% High | Ultra-rare 2% chance to INSTANTLY unlock an unearned Cuisine Flag Trophy!", "odds": "✨ Direct Cuisine Flag Master: 2%\n🟢 Low: 58% | 🟡 Mid: 30% | 🔴 High: 10%"}
    ],
    "specialty": [
        {"id": "box_theme", "name": "🎯 Theme Box", "cost": 500, "icon": "🎯", "type": "theme", "desc": "Guarantees a progress drop strictly inside the culinary category family selected in the sub-widget dropdown.", "odds": "⭐ Drop Odds: 100% Targeted Cuisine Family Focus"},
        {"id": "box_grandmaster", "name": "🏆 Grandmaster", "cost": 1500, "icon": "🏆", "type": "grandmaster", "desc": "Eliminates low tier junk entries entirely. Requires 3 single item trophies unlocked to spin. 75% Mid | 25% High.", "odds": "🟡 Mid-Value (251-600 kcal): 75%\n🔴 High-Value (> 600 kcal): 25%"},
        {"id": "box_daily", "name": "⚡ Daily Special", "cost": 350, "icon": "⚡", "type": "daily", "desc": "Massive 50% probability chance to drop progress straight onto today's highest cost premium menu item.", "odds": "⭐ Active Featured Item: 50%\n🟢 Global Core Fallback Pool: 50%"},
        {"id": "box_underdog", "name": "🩹 Underdog", "cost": 600, "icon": "🩹", "type": "underdog", "desc": "Limits its prize pool exclusively to items with the lowest active progress counts. Built to smash Level Locks!", "odds": "🩹 Drop Odds: 100% Weighted even splits across trailing assets"}
    ],
    "chaos": [
        {"id": "box_roulette", "name": "🌶️ Spicy Roulette", "cost": 400, "icon": "🌶️", "type": "roulette", "desc": "90% chance of a kitchen fire losing a progress point from an active track. 10% chance for triple item cascade jackpot!", "odds": "💥 Kitchen Fire Loss (-1 progress): 90%\n🌶️ Cascade Jackpot (+1 to 3 items): 10%"},
        {"id": "box_double", "name": "🎲 Double/Nothing", "cost": 800, "icon": "🎲", "type": "double", "desc": "50% chance to drop absolutely nothing ('Burnt Food'), 50% chance to grant an instant high multiplier +3 Progress Jump!", "odds": "⚫ Complete Failure (Burnt): 50%\n🎰 High-Tier Multiplier (+3 Progress): 50%"},
        {"id": "box_clean", "name": "🥗 Clean Fuel", "cost": 300, "icon": "🥗", "type": "clean", "desc": "Filters rewards directly to target fitness shakes, energy protein bars, green salads, and low calorie fuel metrics.", "odds": "🟢 Healthy Diet Fitness Pool: 100% Odds"},
        {"id": "box_cheat", "name": "🍔 Cheat Day", "cost": 700, "icon": "🍔", "type": "cheat", "desc": "Filters parameters to isolate heavy, calorie-dense reward food profiles, gourmet recipes, pizza, and treats.", "odds": "🔴 Dense Cheat Feast Assets: 100% Odds"}
    ],
    "strategy": [
        {"id": "box_bogo", "name": "### 👯 BOGO Replicator", "cost": 450, "icon": "👯", "type": "bogo", "desc": "Carries a 70% chance to mirror and duplicate a progress tracking token onto the last item you bought manually in the store.", "odds": "👯 Exact Cache Mirror Copy: 70%\n📦 Global Core Baseline Roll: 30%"},
        {"id": "box_frenzy", "name": "📈 Discount Frenzy", "cost": 500, "icon": "📈", "type": "frenzy", "desc": "Each consecutive unboxing drop cuts this box cost by 75 kcal down to a 200 kcal floor! Manual market buys reset price.", "odds": "📉 Cost Shift Step: -75 kcal per consecutive pull\n🛡️ Floor: 200 kcal"},
        {"id": "box_fridge", "name": "🧹 Clear the Fridge", "cost": 350, "icon": "🧹", "type": "fridge", "desc": "Wipes loose, fractional progress points out from active tracks and packs them into a massive +3 cluster boost inside that category.", "odds": "🧹 Consolidates active fractional baseline points into +3 milestones"},
        {"id": "box_spoon", "name": "🥄 Golden Spoon", "cost": 1200, "icon": "🥄", "type": "spoon", "desc": "Elite late game chest. Excludes any food track stuck at Bronze or Silver. Guarantees progress points only on high level Gold+ assets.", "odds": "🥄 High-Level Mastery Assets (Gold Tier & Above) Focus: 100%"}
    ]
}

