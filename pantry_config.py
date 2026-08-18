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