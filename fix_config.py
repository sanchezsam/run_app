# -*- coding: utf-8 -*-
"""
build_clean_config.py
Generates pantry_config.py using programmatic numerical generation loops
to avoid text filtering and bracket stripping bugs.
"""

# Build standard progress increments mathematically without literal bracket lists
# standard_meals = [5, 10, 15, 20, 25]
standard_meals = list(range(5, 30, 5))

# reduced_sides = [3, 6, 12, 18, 24]
reduced_sides = [3, 6, 12, 18, 24]

# uniform_dessert = [4, 8, 12, 16, 20]
uniform_dessert = list(range(4, 24, 4))

lines = [
    "# -*- coding: utf-8 -*-",
    "",
    "TROPHY_TIERS = [",
    "    {'tier_idx': 0, 'name': 'Bronze Trophy', 'suffix': '🥉', 'level': 1},",
    "    {'tier_idx': 1, 'name': 'Silver Trophy', 'suffix': '🥈', 'level': 2},",
    "    {'tier_idx': 2, 'name': 'Gold Trophy', 'suffix': '🥇', 'level': 3},",
    "    {'tier_idx': 3, 'name': 'Platinum Trophy', 'suffix': '💎', 'level': 4},",
    "    {'tier_idx': 4, 'name': 'Coveted Belt', 'suffix': '🏆 Belt', 'level': 5}",
    "]",
    "",
    "PANTRY_MENU = {",
    "    '🥟 Chinese Cuisine': {",
    "        'flag': '🇨🇳',",
    "        'items': [",
    f"            {{'id': 'dumpling', 'name': 'Dumpling', 'portion': '1 Steamed Pork Piece', 'cost': 60, 'emoji': '🥟', 'thresholds': {standard_meals}}},",
    f"            {{'id': 'takeout_box', 'name': 'Takeout Box Lo Mein', 'portion': '1 Tofu Entree', 'cost': 650, 'emoji': '🥡', 'thresholds': {standard_meals}}},",
    f"            {{'id': 'ramen_bowl', 'name': 'Ramen Noodle Bowl', 'portion': '1 Restaurant Serving with Broth', 'cost': 850, 'emoji': '🍜', 'thresholds': {standard_meals}}},",
    f"            {{'id': 'rice_bowl', 'name': 'Rice Bowl', 'portion': '1 Cup Cooked Rice', 'cost': 215, 'emoji': '🍚', 'thresholds': {standard_meals}}},",
    f"            {{'id': 'fortune_cookie', 'name': 'Fortune Cookie', 'portion': '1 Piece', 'cost': 35, 'emoji': '🥠', 'thresholds': {reduced_sides}}},",
    f"            {{'id': 'bubble_tea', 'name': 'Bubble Tea Boba', 'portion': '16oz Sweetened Cream', 'cost': 450, 'emoji': '🧋', 'thresholds': {reduced_sides}}},",
    f"            {{'id': 'chopsticks', 'name': 'Chopsticks', 'portion': 'Utility Item', 'cost': 5, 'emoji': '🥢', 'thresholds': {reduced_sides}}}"
    "        ]",
    "    },",
    "    '🌮 Mexican Cuisine': {",
    "        'flag': '🇲🇽',",
    "        'items': [",
    f"            {{'id': 'taco', 'name': 'Taco', 'portion': '1 Corn Tortilla Beef/Chicken', 'cost': 220, 'emoji': '🌮', 'thresholds': {standard_meals}}},",
    f"            {{'id': 'burrito', 'name': 'Burrito', 'portion': '1 Large Bean & Beef Wrap', 'cost': 700, 'emoji': '🌯', 'thresholds': {standard_meals}}},",
    f"            {{'id': 'tamale', 'name': 'Tamale', 'portion': '1 Pork Steamed Husk Corn', 'cost': 310, 'emoji': '🫔', 'thresholds': {standard_meals}}},",
    f"            {{'id': 'avocado', 'name': 'Avocado', 'portion': '1 Whole Medium Avocado', 'cost': 320, 'emoji': '🥑', 'thresholds': {reduced_sides}}},",
    f"            {{'id': 'mexican_coke', 'name': 'Mexican Coke', 'portion': '1 Glass Bottle 12oz', 'cost': 150, 'emoji': '🥤', 'thresholds': {reduced_sides}}},",
    f"            {{'id': 'horchata', 'name': 'Horchata', 'portion': '32oz Rice Milk Drink', 'cost': 440, 'emoji': '🍹', 'thresholds': {reduced_sides}}}"
    "        ]",
    "    },",
    "    '🍕 Italian Cuisine': {",
    "        'flag': '🇮🇹',",
    "        'items': [",
    f"            {{'id': 'pizza_slice', 'name': 'Pizza Slice', 'portion': '1 Crust Pepperoni', 'cost': 320, 'emoji': '🍕', 'thresholds': {standard_meals}}},",
    f"            {{'id': 'spaghetti', 'name': 'Spaghetti Pasta', 'portion': '1 Cup Cooked Marinara', 'cost': 300, 'emoji': '🍝', 'thresholds': {reduced_sides}}},",
    f"            {{'id': 'green_salad', 'name': 'Green Salad', 'portion': '1 Bowl Cream Dressing', 'cost': 250, 'emoji': '🥗', 'thresholds': {reduced_sides}}},",
    f"            {{'id': 'cheese_block', 'name': 'Cheese Block', 'portion': '1.5 oz Cheddar Cheese', 'cost': 170, 'emoji': '🧀', 'thresholds': {reduced_sides}}}"
    "        ]",
    "    },",
    "    '🍔 American Diner Cuisine': {",
    "        'flag': '🇺🇸',",
    "        'items': [",
    f"            {{'id': 'hamburger', 'name': 'Hamburger', 'portion': 'Single Patty with Cheese', 'cost': 550, 'emoji': '🍔', 'thresholds': {standard_meals}}},",
    f"            {{'id': 'steak_cut', 'name': 'Steak Cut Meat', 'portion': '6 oz Cooked Sirloin', 'cost': 480, 'emoji': '🥩', 'thresholds': {standard_meals}}},",
    f"            {{'id': 'french_fries', 'name': 'French Fries', 'portion': '1 Medium Fry Basket', 'cost': 400, 'emoji': '🍟', 'thresholds': {reduced_sides}}},",
    f"            {{'id': 'hot_dog', 'name': 'Hot Dog', 'portion': '1 Ballpark Beef Frank', 'cost': 350, 'emoji': '🌭', 'thresholds': {reduced_sides}}},",
    f"            {{'id': 'chocolate_milkshake', 'name': 'Thick Chocolate Milkshake', 'portion': '1 Large 16oz Diner Glass', 'cost': 650, 'emoji': '🥤', 'thresholds': {reduced_sides}}}"
    "        ]",
    "    },",
    "    '🧁 Coveted Desserts': {",
    "        'flag': '🍨',",
    "        'items': [",
    f"            {{'id': 'ice_cream', 'name': 'Ice Cream Cone', 'portion': 'Double Waffle Cone', 'cost': 450, 'emoji': '🍦', 'thresholds': {uniform_dessert}}},",
    f"            {{'id': 'cake_slice', 'name': 'Slice of Cake', 'portion': 'Fudge Chocolate Cake', 'cost': 520, 'emoji': '🍰', 'thresholds': {uniform_dessert}}},",
    f"            {{'id': 'donut', 'name': 'Glazed Donut', 'portion': '1 Large Bakery Donut', 'cost': 380, 'emoji': '🍩', 'thresholds': {uniform_dessert}}},",
    f"            {{'id': 'cookie', 'name': 'Soft-Baked Cookie', 'portion': '1 Chocolate Chip Bakery Item', 'cost': 290, 'emoji': '🍪', 'thresholds': {uniform_dessert}}}"
    "        ]",
    "    }",
    "}"
]

with open("pantry_config.py", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("🛠️ Dynamic configuration generation verified! Running python validation test...")
import pantry_config
print("✅ SUCCESS: pantry_config.py compiles cleanly with zero syntax errors!")

