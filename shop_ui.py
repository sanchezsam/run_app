# -*- coding: utf-8 -*-
import streamlit as st
import json
import random

# ==============================================================================
# 🏪 CENTRALISED DATA MATRIX CONFIGURATION WITH ENVIRONMENTAL METADATA
# ==============================================================================
gear_catalog = {
    # --- FOOTWEAR ---
    'Nike Vaporfly 4%': {'cost': 120, 'cat': 'Footwear', 'weather': 'All-Weather', 'desc': 'Carbon-plated shoe. Massive Sprint Velocity physics bonus.'},
    'adidas UltraBoost': {'cost': 95, 'cat': 'Footwear', 'weather': 'All-Weather', 'desc': 'Premium cushioning foam. Absorbs high track mileage.'},
    'Hoka One One Speedgoat': {'cost': 110, 'cat': 'Footwear', 'weather': 'All-Weather', 'desc': 'Maximalist trail tread. Best for mountain torque.'},
    'Saucony Endorphin Elite': {'cost': 130, 'cat': 'Footwear', 'weather': 'All-Weather', 'desc': 'Aggressive rocker geometry. Injects consistent tempo pace splits.'},
    'Brooks Ghost Speed': {'cost': 85, 'cat': 'Footwear', 'weather': 'All-Weather', 'desc': 'Ultra-reliable daily workload workhorse. Excellent fatigue dampening.'},
    'New Balance FuelCell Rebel': {'cost': 105, 'cat': 'Footwear', 'weather': 'All-Weather', 'desc': 'Explosive high-rebound compound foam. Boosts rapid cadence changes.'},
    'Puma Fast-R Nitro Elite': {'cost': 140, 'cat': 'Footwear', 'weather': 'All-Weather', 'desc': 'Decoupled carbon plate chassis. Cutting-edge drag reduction metrics.'},
    'ASICS Metaspeed Sky+': {'cost': 145, 'cat': 'Footwear', 'weather': 'All-Weather', 'desc': 'Elongated stride efficiency. Elite scaling for high-velocity drivers.'},
    
    # --- SUNGLASSES ---
    'Oakley Speed Jacket Sunglasses': {'cost': 45, 'cat': 'Sunglasses', 'weather': 'All-Weather', 'desc': 'Aerodynamic shatterproof frames. Maximizes tracking accuracy.'},
    '100% Speedcraft Shaded Shields': {'cost': 55, 'cat': 'Sunglasses', 'weather': 'All-Weather', 'desc': 'Expanded peripheral vision. High-impact arcade neon visibility lenses.'},
    'Goodr No Bounce Optics': {'cost': 20, 'cat': 'Sunglasses', 'weather': 'All-Weather', 'desc': 'Lightweight textured frame grip. Eliminates slipping during sprint cadence loops.'},
    'Smith Vert Performance Shades': {'cost': 65, 'cat': 'Sunglasses', 'weather': 'All-Weather', 'desc': 'Chameleon color-adjusting lenses adapting smoothly to canyon trail glare.'},
    
    # --- HEAD GEAR ---
    'Arcade Neon Headband': {'cost': 20, 'cat': 'Head Gear', 'weather': 'All-Weather', 'desc': 'Retro sweat protection. Adds style and focus multipliers.'},
    'Ciele Athletics GOCap': {'cost': 25, 'cat': 'Head Gear', 'weather': 'All-Weather', 'desc': 'Lightweight collapsible mesh race cap. Deflects extreme canyon sun glare.'},
    'Compressport Visor Engine': {'cost': 18, 'cat': 'Head Gear', 'weather': 'All-Weather', 'desc': 'Ultra-minimal ventilated tracking peak. Maximizes cockpit cooling layers.'},
    'Buff Merino Thermal Wrap': {'cost': 22, 'cat': 'Head Gear', 'weather': 'Winter Jacket (Cold)', 'desc': 'Insulates head and neck vitals. Solid for high altitude winter stages.'},
    
    # --- JACKETS ---
    'Patagonia Houdini Windbreaker': {'cost': 75, 'cat': 'Jackets', 'weather': 'Windbreaker (Windy)', 'desc': 'Featherlight ripstop shell. Completely negates wind resistance penalties.'},
    'Arc\'teryx Norvan Gore-Tex Jacket': {'cost': 150, 'cat': 'Jackets', 'weather': 'Rain Jacket (Wet)', 'desc': 'Fully seam-sealed waterproof barrier. Prevents tracking friction in severe storms.'},
    'The North Face Summit Winter Parka': {'cost': 195, 'cat': 'Jackets', 'weather': 'Winter Jacket (Cold)', 'desc': 'Advanced down insulation pack. Sustains core temperatures during alpine winter stages.'},

    # --- SINGLETS ---
    'Elite Aero-Grid Singlet': {'cost': 40, 'cat': 'Singlets', 'weather': 'All-Weather', 'desc': 'Weightless track singlet. Decreases wind drag factors.'},
    'Championship Crimson Jersey': {'cost': 50, 'cat': 'Singlets', 'weather': 'All-Weather', 'desc': 'Vibrant racing jersey boosting team prestige indices.'},
    'Tracksmith Van Cortlandt Singlet': {'cost': 65, 'cat': 'Singlets', 'weather': 'All-Weather', 'desc': 'Luxury mesh fabric layout with iconic racing sash. Elite comfort lines.'},
    'Nike Dri-FIT ADV Aeroswift': {'cost': 70, 'cat': 'Singlets', 'weather': 'All-Weather', 'desc': 'Engineered precision breathability zones. Minimizes heat build-up blockades.'},
    'Under Armour Iso-Chill Mesh': {'cost': 30, 'cat': 'Singlets', 'weather': 'All-Weather', 'desc': 'Flat titanium fibers pull skin heat away, boosting torque stability.'},
    'adidas Adizero Race Vest': {'cost': 45, 'cat': 'Singlets', 'weather': 'All-Weather', 'desc': 'Barely-there ultraweight microfiber layout tailored for speedways.'},
    'New Balance RC Short Sleeve': {'cost': 38, 'cat': 'Singlets', 'weather': 'All-Weather', 'desc': 'Premium anti-chafing welded seams. Solid for deep high-mileage volume.'},
    'Gore-Tex Windstopper Shell': {'cost': 85, 'cat': 'Singlets', 'weather': 'Winter Jacket (Cold)', 'desc': 'Hardcore weather shield. Insulates core vitals across alpine storms.'},
    
    # --- SHORTS ---
    'Split Training Track Shorts': {'cost': 35, 'cat': 'Shorts', 'weather': 'All-Weather', 'desc': 'Classic maximum range of motion splits. Improves cadence loops.'},
    'Compression Racing Tights': {'cost': 55, 'cat': 'Shorts', 'weather': 'Winter Jacket (Cold)', 'desc': 'Streamlined thermal tights optimizing lower body blood flow.'},
    'Patagonia Strider Pro Shorts': {'cost': 60, 'cat': 'Shorts', 'weather': 'All-Weather', 'desc': '5-pocket system carrying emergency power fuel arrays effortlessly.'},
    'Brooks Sherpa 2-in-1 Chassis': {'cost': 42, 'cat': 'Shorts', 'weather': 'All-Weather', 'desc': 'Chafing-free inner brief liner. Maximum baseline support limits.'},
    'ASICS Actibreeze Track Tight': {'cost': 48, 'cat': 'Shorts', 'weather': 'All-Weather', 'desc': 'High-ventilation elastic wrap keeping muscle matrices oxygenated.'},
    'Lululemon Surge Pace Split': {'cost': 52, 'cat': 'Shorts', 'weather': 'All-Weather', 'desc': 'Premium lightweight stretch fabric. Moves fluidly with high strides.'},
    'Salomon S/Lab Ultra Skirt-Short': {'cost': 95, 'cat': 'Shorts', 'weather': 'Rain Jacket (Wet)', 'desc': 'Elite long-range trail armor. Specialized for rugged canyon operations.'},
    'Nike Trail Brief split 2"': {'cost': 38, 'cat': 'Shorts', 'weather': 'All-Weather', 'desc': 'Hyper-minimal track splits designed to maximize raw sprint cadence.'},
    
    # --- PANTS ---
    'Nike Phenom Elite Wind Pants': {'cost': 70, 'cat': 'Pants', 'weather': 'Windbreaker (Windy)', 'desc': 'Tapered aerodynamic track pants. Stabilizes leg stride cycles during heavy gusts.'},
    'adidas Terrex Waterproof Pants': {'cost': 110, 'cat': 'Pants', 'weather': 'Rain Jacket (Wet)', 'desc': 'Hydrophobic storm weave. Deflects mud and water log drag multipliers.'},
    'Under Armour ColdGear Infrared Tights': {'cost': 85, 'cat': 'Pants', 'weather': 'Winter Jacket (Cold)', 'desc': 'Thermo-conductive inner lining that absorbs and retains lower body muscle heat.'},

    # --- WATCHES ---
    'Garmin Forerunner Pro': {'cost': 85, 'cat': 'Watches', 'weather': 'All-Weather', 'desc': 'Surgical track splitting. Smooths out raw pacing lines.'},
    'Coros Pace Performance Matrix': {'cost': 70, 'cat': 'Watches', 'weather': 'All-Weather', 'desc': 'Weightless satellite capture engine. Elite driver telemetry sync.'},
    'Apple Watch Ultra Matrix': {'cost': 160, 'cat': 'Watches', 'weather': 'All-Weather', 'desc': 'Titanium diving cockpit hull. Dual-frequency precision tracking.'},
    'Polar Vanguard Heart Hub': {'cost': 115, 'cat': 'Watches', 'weather': 'All-Weather', 'desc': 'Electrocardiogram telemetry tracking. Smooths out fatigue recovery curves.'},
    'Suunto Vertical Solar Array': {'cost': 140, 'cat': 'Watches', 'weather': 'All-Weather', 'desc': 'Solar harvest lens extends battery indefinitely on wilderness loops.'},
    'Vintage Casio Chrono-Shock': {'cost': 20, 'cat': 'Watches', 'weather': 'All-Weather', 'desc': 'Vintage basic 1/100s stopwatch. Old-school tactical aesthetics.'},
    'Garmin Fenix Enduro Hull': {'cost': 180, 'cat': 'Watches', 'weather': 'All-Weather', 'desc': 'Indestructible sapphire tracking lens. Absolute peak luxury watch.'},
    'Coros Vertix Mountain Engine': {'cost': 150, 'cat': 'Watches', 'weather': 'All-Weather', 'desc': 'Barometric altitude calculator. Injects major bonus to climbing analytics.'}
}

weather_labels = {
    'All-Weather': '🌤️ All-Weather',
    'Windbreaker (Windy)': '💨 Windbreaker (Windy)',
    'Rain Jacket (Wet)': '🌧️ Rain Jacket (Wet)',
    'Winter Jacket (Cold)': '❄️ Winter Jacket (Cold)'
}

try:
    from pro_shop_config import PRO_SHOP_SKINS_REGISTRY
except ImportError:
    PRO_SHOP_SKINS_REGISTRY = [
        {"unlock_level": 1, "skin_id": "theme_pacer_green", "title": "🔰 Standard Pacer Green", "accent_color": "#2ecc71"}
    ]

def render_shop_interface(player, FILE_PATH):
    st.markdown('## 🛒 Pro Shop & Performance Equipment Forge')
    
    gold_balance = int(getattr(player, 'gold', 50))
    st.markdown(f"Current Gold Balance: **{gold_balance}g** | Available Stat Tokens: **{getattr(player, 'stat_points', 0)}**")
    st.markdown('---')

    # =========================================================================
    # 🎰 PERSISTENT STATE TOAST & HIGH-CONTRAST EMOJI RAIN MANAGER
    # =========================================================================
    if "shop_toast" in st.session_state:
        st.toast(st.session_state.shop_toast["text"], icon=st.session_state.shop_toast["icon"])
        del st.session_state.shop_toast

    if "shop_highlight" in st.session_state:
        falling_emoji = st.session_state.get("shop_highlight_emoji", "📦")
        rain_html = '<div style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: 999999; overflow: hidden;">'
        for _ in range(25):
            left_pos = random.randint(3, 97)
            delay = random.uniform(0.0, 2.0)
            duration = random.uniform(2.5, 4.5)
            size = random.randint(22, 48)
            rain_html += f'<div style="position: absolute; top: -60px; left: {left_pos}%; font-size: {size}px; animation: shopRainAnim {duration}s linear {delay}s forwards; pointer-events: none;">{falling_emoji}</div>'
        rain_html += """
        </div>
        <style>
        @keyframes shopRainAnim {
            0% { transform: translateY(0) rotate(0deg); opacity: 1; }
            85% { opacity: 1; }
            100% { transform: translateY(108vh) rotate(360deg); opacity: 0; }
        }
        </style>
        """
        st.markdown(rain_html, unsafe_allow_html=True)
        st.success(st.session_state.shop_highlight, icon="✨")
        del st.session_state.shop_highlight
        if "shop_highlight_emoji" in st.session_state:
            del st.session_state.shop_highlight_emoji

    # =========================================================================
    # 🛡️ ENGINE DATA INTEGRITY SAFETY HANDLERS
    # =========================================================================
    if not hasattr(player, 'inventory') or player.inventory is None: player.inventory = []
    if not hasattr(player, 'equipped_gear') or player.equipped_gear is None: player.equipped_gear = {}
    if not hasattr(player, 'gear_colors') or player.gear_colors is None: player.gear_colors = {}
    
    if "shop_discount_frenzy_cost" not in st.session_state:
        st.session_state.shop_discount_frenzy_cost = 150
    if "shop_active_tab" not in st.session_state:
        st.session_state.shop_active_tab = "gear_cabinet"

    # =========================================================================
    # ⚖️ STATE-DRIVEN TAB NAVIGATION ROUTER
    # =========================================================================
    nav_col_1, nav_col_2, nav_col_3 = st.columns(3)
    with nav_col_1:
        is_cabinet_selected = st.session_state.shop_active_tab == "gear_cabinet"
        if st.button("👟 Your Equipment Gear", key="shop_nav_btn_cabinet", use_container_width=True, type="primary" if is_cabinet_selected else "secondary"):
            st.session_state.shop_active_tab = "gear_cabinet"
            st.rerun()
    with nav_col_2:
        is_market_selected = st.session_state.shop_active_tab == "purchase_shop"
        if st.button("🛒 Browse Pro Shop", key="shop_nav_btn_market", use_container_width=True, type="primary" if is_market_selected else "secondary"):
            st.session_state.shop_active_tab = "purchase_shop"
            st.rerun()
    with nav_col_3:
        is_vault_selected = st.session_state.shop_active_tab == "mystery_vault"
        if st.button("🎁 Pro Chest Vault", key="shop_nav_btn_vault", use_container_width=True, type="primary" if is_vault_selected else "secondary"):
            st.session_state.shop_active_tab = "mystery_vault"
            st.rerun()

    st.markdown('<br>', unsafe_allow_html=True)

    # Pre-build catalog lists based on cost brackets
    p_low_display, p_mid_display, p_high_display = [], [], []
    for item, specs in gear_catalog.items():
        icost = specs.get("cost", 0)
        ientry = f"{item} ({icost}g)"
        if icost <= 40: p_low_display.append(ientry)
        elif 41 <= icost <= 90: p_mid_display.append(ientry)
        else: p_high_display.append(ientry)

    def save_player_state():
        with open(FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(player.to_dict() if hasattr(player, 'to_dict') else player.__dict__, f, default=str, indent=4)

    # Global kit slot mapping configuration parameters
    kit_slots = {
        'Footwear': 'equipped_shoe_name', 'Sunglasses': 'equipped_sunglasses_name',
        'Head Gear': 'equipped_headgear_name', 'Singlets': 'equipped_singlet_name',
        'Jackets': 'equipped_jacket_name', 'Shorts': 'equipped_shorts_name',
        'Pants': 'equipped_pants_name', 'Watches': 'equipped_watch_name'
    }

    # =========================================================================
    # 👟 ROUTE PANEL: EQUIPMENT LOADOUT & ATTRIBUTE VAULT
    # =========================================================================
    if st.session_state.shop_active_tab == "gear_cabinet":
        # --- LIVE ENVIRONMENT FORECAST & LOADOUT BRIEFING BANNER WITH INVENTORY CHECKING ---
        with st.container(border=True):
            st.markdown("#### 🌤️ Live Weather Briefing & Dynamic Gear Advisory")
            st.markdown(
                "**Current Conditions (Los Alamos, NM):** 78°F | Partly Sunny | 💨 Wind: SE 4 mph | ☀️ UV Index: 6 (High)\n\n"
                "**Hourly Forecast Outlook:** UV levels rise to a peak of 8 midday. Stable dry conditions hold for now, but local "
                "mountain weather maps signal a **35% chance of light rain and scattered thunderstorms starting around 5:00 PM MDT**.\n\n"
                "**🎯 Personalized Inventory Equipment Recommendations:**"
            )
            
            ideal_recommendations = {
                'Footwear': ('Nike Vaporfly 4%', 'Optimizes raw pacing lines under warm sunny midday tracks.', '👟'),
                'Sunglasses': ('Oakley Speed Jacket Sunglasses', 'Essential to shield vision metrics from high midday UV indices.', '🕶️'),
                'Head Gear': ('Ciele Athletics GOCap', 'Lightweight mesh build to deflect extreme midday canyon glare.', '🧢'),
                'Singlets': ('Nike Dri-FIT ADV Aeroswift', 'Engineered precision breathability zones suited for 78°F ambient heat.', '🎽'),
                'Shorts': ('Split Training Track Shorts', 'Unrestricted fluid motion designed for warm daytime pacing iterations.', '🩳'),
                'Watches': ('Garmin Forerunner Pro', 'Surgical track splitting tracking telemetry.', '⌚'),
                'Jackets': ("Arc'teryx Norvan Gore-Tex Jacket", '🚨 WEATHER ALERT: Fully sealed waterproof layer required for 5:00 PM storms.', '🧥'),
                'Pants': ('adidas Terrex Waterproof Pants', '🚨 WEATHER ALERT: Hydrophobic barrier required for rainy evening trail mud logs.', '👖')
            }
            
            # --- ONE-CLICK RECOMENDATION ACTION BUTTON SYSTEM ---
            owned_recommendations = [item for slot, (item, _, _) in ideal_recommendations.items() if item in player.inventory]
            already_equipped = [item for slot, (item, _, _) in ideal_recommendations.items() if getattr(player, kit_slots[slot], None) == item]
            can_equip_more = len(owned_recommendations) > len(already_equipped)
            
            if st.button("⚡ Auto-Equip All Recommended Owned Gear", key="auto_equip_rec_btn", use_container_width=True, disabled=not can_equip_more):
                equip_counter = 0
                for slot, (item_name, _, _) in ideal_recommendations.items():
                    if item_name in player.inventory and getattr(player, kit_slots[slot], None) != item_name:
                        setattr(player, kit_slots[slot], item_name)
                        equip_counter += 1
                if equip_counter > 0:
                    save_player_state()
                    st.session_state.shop_toast = {"text": f"Successfully loaded +{equip_counter} optimal weather gear modules!", "icon": "🎽"}
                    st.rerun()
            
            st.markdown("---")
            
            rec_row1 = st.columns(4)
            rec_row2 = st.columns(4)
            rec_cols = rec_row1 + rec_row2
            
            for idx, (slot, (item_name, reason, slot_emoji)) in enumerate(ideal_recommendations.items()):
                with rec_cols[idx]:
                    is_owned = item_name in player.inventory
                    is_equipped = getattr(player, kit_slots[slot], None) == item_name
                    
                    if is_owned:
                        if is_equipped:
                            st.markdown(f"{slot_emoji} **{slot}**: `{item_name}`\n\n<small style='color:#2ecc71; font-weight:bold;'>✓ Optimal & Active</small>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"{slot_emoji} **{slot}**: `{item_name}`\n\n<small style='color:#f1c40f; font-weight:bold;'>⚠️ Owned - Equip below</small>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"{slot_emoji} **{slot}**: `{item_name}`\n\n<small style='color:#e74c3c; font-weight:bold;'>🛒 Suggest Buying in Shop</small>", unsafe_allow_html=True)
                    st.caption(f"<small style='color:#9aa0a6;'>{reason}</small>", unsafe_allow_html=True)

        st.markdown('<br>', unsafe_allow_html=True)

        # --- ACTIVE ATHLETE KIT CONFIGURATION BLUEPRINT HUD HEADER ---
        st.markdown("### 🎽 Active Athlete Kit Configuration Blueprint")
        st.caption("Your single-slot equipped loadout and custom spray paint profiles currently active on your driver athlete:")
        
        color_emojis = {
            "Basic Factory": "⚙️", "Factory": "⚙️", "White": "⚪", "Blue": "🔵", "Red": "🔴", 
            "Green": "🟢", "Yellow": "🟡", "Silver": "🥈", "Gold": "👑"
        }
        
        # 8-Slot Layout Split evenly across two compact rows of 4
        kc_row1 = st.columns(4)
        kc_row2 = st.columns(4)
        cols_list = kc_row1 + kc_row2
        saved_colors = player.gear_colors
        
        for idx, (slot_title, attr_key) in enumerate(kit_slots.items()):
            with cols_list[idx]:
                with st.container(border=True):
                    active_item = getattr(player, attr_key, None)
                    st.markdown(f"##### {slot_title}")
                    if active_item:
                        item_rank = int(player.equipped_gear.get(active_item, 1))
                        item_paint = saved_colors.get(active_item, "Factory")
                        paint_emoji = color_emojis.get(item_paint, "⚙️")
                        w_type = gear_catalog.get(active_item, {}).get('weather', 'All-Weather')
                        w_lbl = weather_labels.get(w_type, '🌤️ All-Weather')
                        
                        st.success(f"🎽 **{active_item}**")
                        st.markdown(f"`Rank +{item_rank}` | <small>{w_lbl}</small>\nVariant: {paint_emoji} `{item_paint.upper()}`", unsafe_allow_html=True)
                    else:
                        st.info("ℹ️ Slot Empty")
                        st.caption("Equip a module from your Locker Vault below.")
                        
        # ---------------------------------------------------------------------
        # 📊 DYNAMIC ENVIRONMENTAL AND CORPORATE SPONSOR SYNC BANNER LAUNCHERS
        # ---------------------------------------------------------------------
        equipped_items = []
        for slot_title, attr_key in kit_slots.items():
            item = getattr(player, attr_key, None)
            if item:
                equipped_items.append(item)
                
        if len(equipped_items) >= 3:
            # Weather Sync Evaluation Block (All-Weather behaves as a dynamic wildcard)
            active_weathers = [gear_catalog[it]['weather'] for it in equipped_items if it in gear_catalog]
            specific_weathers = [w for w in active_weathers if w != 'All-Weather']
            
            is_weather_synced = False
            synced_weather_target = "All-Weather"
            
            if len(set(active_weathers)) == 1 and active_weathers[0] == 'All-Weather':
                is_weather_synced = True
            elif len(set(specific_weathers)) == 1 and len(specific_weathers) > 0:
                is_weather_synced = True
                synced_weather_target = specific_weathers[0]
                
            # Brand Sync Evaluation Block
            brands_db = ["Nike", "adidas", "Hoka", "Saucony", "Brooks", "New Balance", "Puma", "ASICS", "Oakley", "100%", "Goodr", "Smith", "Arcade", "Ciele", "Compressport", "Buff", "Patagonia", "Arc'teryx", "The North Face", "Tracksmith", "Under Armour", "Gore-Tex", "Lululemon", "Salomon", "Garmin", "Coros", "Apple", "Polar", "Suunto", "Casio"]
            def extract_item_brand(name):
                for b in brands_db:
                    if b.lower() in name.lower(): return b
                return None
                
            active_brands = [extract_item_brand(it) for it in equipped_items if extract_item_brand(it) is not None]
            is_brand_synced = len(active_brands) == len(equipped_items) and len(set(active_brands)) == 1
            
            if is_weather_synced or is_brand_synced:
                sync_b1, sync_b2 = st.columns(2)
                with sync_b1:
                    if is_weather_synced:
                        st.info(f"✨ **OUTFIT SYNCED ({weather_labels.get(synced_weather_target, synced_weather_target)})**\n\nAll equipped loadout elements align seamlessly for specialized track environments!")
                with sync_b2:
                    if is_brand_synced:
                        st.success(f"🔥 **BRAND SYNCED ({active_brands[0]})**\n\nYour profile aesthetics achieve full manufacturer sponsor synchronization harmony!")

        st.markdown('---')
        
        # --- ATTRIBUTE Node ALLOCATION FORGE ---
        st.markdown('### 🏋️ Attribute Node Allocation Forge')
        sac1, sac2 = st.columns(2)
        with sac1:
            if st.button('Upgrade Base Velocity Nodes (+1 Running Token)', disabled=(getattr(player, 'stat_points', 0) < 1)):
                try:
                    player.stat_points = getattr(player, 'stat_points', 0) - 1
                    player.running_level = getattr(player, 'running_level', 1) + 1
                    player.vo2_max = getattr(player, 'vo2_max', 40.0) + 0.5
                    save_player_state()
                    st.session_state.shop_toast = {"text": "Attribute Node forged successfully!", "icon": "✨"}
                    st.rerun()
                except Exception as e: st.error(f'Forge fault: {str(e)}')
        with sac2: st.caption(f"Current Forged Skill: Level **{getattr(player, 'running_level', 1)}** | VO2 Max Base: **{getattr(player, 'vo2_max', 40.0):.1f}**")
        st.markdown('---')

        # --- LOCKER ROOM VAULT SYSTEMS ---
        st.markdown('### 📦 Your Locker Gear Locker Vault')
        if not player.inventory: 
            st.info('Your equipment chest is empty. Purchase storefront items or open gear boxes to populate inventory tabs.')
        else:
            vault_tab_filter = st.radio('View Locker Category:', ['Footwear', 'Sunglasses', 'Head Gear', 'Singlets', 'Jackets', 'Shorts', 'Pants', 'Watches'], horizontal=True)
            active_slot_variable = kit_slots[vault_tab_filter]
            currently_equipped_item = getattr(player, active_slot_variable, None)
            category_items = [item for item in player.inventory if item in gear_catalog and gear_catalog[item]['cat'] == vault_tab_filter]
            
            if not category_items: 
                st.info(f"No collected item entries inside {vault_tab_filter} yet.")
            else:
                vault_row_cols = st.columns(3)
                for idx, owned_item in enumerate(category_items):
                    curr_level = min(10, max(1, int(player.equipped_gear.get(owned_item, 1))))
                    base_cost = gear_catalog.get(owned_item, {'cost': 40})['cost']
                    is_maxed = curr_level >= 10
                    next_level_cost = int(base_cost * (curr_level + 1) * 0.5 * curr_level)
                    is_equipped = (owned_item == currently_equipped_item)
                    active_paint = player.gear_colors.get(owned_item, "Basic Factory")
                    current_emoji = color_emojis.get(active_paint, "⚙️")
                    w_type = gear_catalog.get(owned_item, {}).get('weather', 'All-Weather')
                    w_lbl = weather_labels.get(w_type, '🌤️ All-Weather')
                    
                    with vault_row_cols[idx % 3]:
                        with st.container(border=True):
                            st.markdown(f"🏅 **{owned_item}**")
                            v1, v2 = st.columns(2)
                            with v1:
                                st.markdown(f"`Rank {curr_level}/10`")
                                st.markdown(f" `{w_lbl}`")
                                st.markdown(f"🎨 {current_emoji} `{active_paint.upper()}`")
                                st.progress(float(curr_level / 10.0))
                                
                                if is_equipped: 
                                    st.button('ACTIVE ON KIT', key=f'act_slot_eq_{owned_item}_{idx}', disabled=True, use_container_width=True)
                                else:
                                    if st.button('Equip Gear', key=f'equip_slot_action_{owned_item}_{idx}', use_container_width=True):
                                        setattr(player, active_slot_variable, owned_item)
                                        save_player_state()
                                        st.session_state.shop_toast = {"text": f"Equipped {owned_item}!", "icon": "⚡"}
                                        st.rerun()
                            with v2:
                                available_shades = ["Basic Factory", "White", "Blue", "Red", "Green", "Yellow", "Silver", "Gold"]
                                chosen_shade = st.selectbox(
                                    "Stage Color:", options=available_shades,
                                    index=available_shades.index(active_paint) if active_paint in available_shades else 0,
                                    key=f"paint_selector_{idx}_{owned_item.replace(' ', '_')}"
                                )
                                if chosen_shade != active_paint:
                                    if st.button(f"Paint (-15g)", key=f"purchase_color_btn_{idx}_{owned_item.replace(' ', '_')}", disabled=(gold_balance < 15), use_container_width=True):
                                        player.gold = gold_balance - 15
                                        player.gear_colors[owned_item] = chosen_shade
                                        save_player_state()
                                        st.session_state.shop_toast = {"text": f"Applied colorway {chosen_shade}!", "icon": "🎨"}
                                        st.rerun()
                                        
                                if is_maxed: 
                                    st.button('MAX RANK', key=f'max_slot_rank_{owned_item}_{idx}', disabled=True, use_container_width=True)
                                else:
                                    if st.button(f"Tune (+{next_level_cost}g)", key=f'tune_slot_action_{owned_item}_{idx}', disabled=(gold_balance < next_level_cost), use_container_width=True):
                                        player.gold = gold_balance - next_level_cost
                                        player.equipped_gear[owned_item] = curr_level + 1
                                        save_player_state()
                                        st.session_state.shop_toast = {"text": f"Tuned asset to Rank +{curr_level + 1}!", "icon": "⚡"}
                                        st.rerun()

    # =========================================================================
    # 🛒 ROUTE PANEL: EQUIPMENT PRO STOREFRONT BROWSER
    # =========================================================================
    elif st.session_state.shop_active_tab == "purchase_shop":
        st.markdown('### 🛍️ Equipment Catalog Storefront')
        cat_filter = st.selectbox('Filter Catalog Section:', ['Footwear', 'Sunglasses', 'Head Gear', 'Singlets', 'Jackets', 'Shorts', 'Pants', 'Watches'])
        
        market_cols = st.columns(4)
        filtered_items = [(it, sp) for it, sp in gear_catalog.items() if sp['cat'] == cat_filter]
        
        for idx, (item, specs) in enumerate(filtered_items):
            is_owned = item in player.inventory
            w_type = specs.get('weather', 'All-Weather')
            w_lbl = weather_labels.get(w_type, '🌤️ All-Weather')
            
            with market_cols[idx % 4]:
                with st.container(border=True):
                    if is_owned:
                        st.markdown(f'<p style="opacity: 0.3; filter: grayscale(100%); margin: 0;">📦 <b>{item}</b> | <small style="color: #555;">{w_lbl}</small></p>', unsafe_allow_html=True)
                        st.markdown(f'<p style="opacity: 0.3; filter: grayscale(100%); font-size: 13px; color: #808495; margin: 0 0 10px 0;">{specs["desc"]}</p>', unsafe_allow_html=True)
                    else:
                        st.markdown(f"📦 **{item}** | `{w_lbl}`")
                        st.caption(specs['desc'])
                    if is_owned: 
                        st.button('Item Acquired ✓', key=f'm_owned_{item.replace(" ", "_")}', disabled=True, use_container_width=True)
                    else:
                        if st.button(f"Purchase Gear ({specs['cost']}g)", key=f'm_buy_{item.replace(" ", "_")}', disabled=(gold_balance < specs['cost']), use_container_width=True):
                            try:
                                player.gold = gold_balance - specs['cost']
                                player.inventory.append(item)
                                player.equipped_gear[item] = 1
                                player.gear_colors[item] = "Basic Factory"
                                st.session_state.shop_last_bought = item
                                st.session_state.shop_discount_frenzy_cost = 150
                                
                                # Automatic slot fitting router
                                if specs['cat'] == 'Footwear' and not getattr(player, 'equipped_shoe_name', None): player.equipped_shoe_name = item
                                elif specs['cat'] == 'Sunglasses' and not getattr(player, 'equipped_sunglasses_name', None): player.equipped_sunglasses_name = item
                                elif specs['cat'] == 'Head Gear' and not getattr(player, 'equipped_headgear_name', None): player.equipped_headgear_name = item
                                elif specs['cat'] == 'Singlets' and not getattr(player, 'equipped_singlet_name', None): player.equipped_singlet_name = item
                                elif specs['cat'] == 'Jackets' and not getattr(player, 'equipped_jacket_name', None): player.equipped_jacket_name = item
                                elif specs['cat'] == 'Shorts' and not getattr(player, 'equipped_shorts_name', None): player.equipped_shorts_name = item
                                elif specs['cat'] == 'Pants' and not getattr(player, 'equipped_pants_name', None): player.equipped_pants_name = item
                                elif specs['cat'] == 'Watches' and not getattr(player, 'equipped_watch_name', None): player.equipped_watch_name = item
                                
                                save_player_state()
                                st.session_state.shop_toast = {"text": f"Collected {item}!", "icon": "🎁"}
                                st.rerun()
                            except Exception as e: st.error(f'Store fault: {str(e)}')

    # =========================================================================
    # 🎁 ROUTE PANEL: DATA-DRIVEN PRO GEAR MYSTERY CHEST VAULT
    # =========================================================================
    elif st.session_state.shop_active_tab == "mystery_vault":
        st.markdown('### 🎁 The High-Volume Pro Gear Chest Vault')
        st.markdown('Exchange your gold balance tokens across programmatic dynamic lottery categories to pull or rank up gear sets.')
        
        # Centralized Box Configurations Matrix Registry
        SHOP_BOX_REGISTRY = {
            "core": [
                {"id": "s_box_apparel", "name": "Apparel Box", "cost": 50, "icon": "📦", "type": "core", "desc": "100% chance to drop Low-Value items (costing ≤ 40g). Balanced styling baseline.", "odds": "🟢 Low-Value items (≤ 40g): 100%"},
                {"id": "s_box_performance", "name": "Performance Box", "cost": 120, "icon": "💎", "type": "core", "desc": "90% Low-Value items (≤ 40g) | 10% Mid-Value specialized item tech (41-90g).", "odds": "🟢 Low-Value (≤ 40g): 90%\n🟡 Mid-Value (41-90g): 10%"},
                {"id": "s_box_championship", "name": "Championship Box", "cost": 250, "icon": "👑", "type": "core", "desc": "60% Low-Value | 30% Mid-Value | 10% Elite High-Value telemetry assets (> 90g).", "odds": "🟢 Low: 60% | 🟡 Mid: 30% | 🔴 High: 10%"}
            ],
            "specialty": [
                {"id": "s_box_focus", "name": "🎯 Focus Chest", "cost": 180, "icon": "🎯", "type": "theme", "desc": "Guarantees an entry drop or rank upgrade strictly matching the selected loadout section family.", "odds": "⭐ Department Focus Odds: 100% Target Match"},
                {"id": "s_box_underdog", "name": "🩹 Catch-Up Pack", "cost": 220, "icon": "🩹", "type": "underdog", "desc": "Wipes variance by pulling/upgrading exclusively from your lowest rank gear components.", "odds": "🩹 Dynamic balancing: 100% trailing asset target"},
                {"id": "s_box_colorway", "name": "🎨 Paint Palette", "cost": 80, "icon": "🎨", "type": "colorway", "desc": "Rolls a random gear piece and spray color combo. If your item already has that coating, the roll results in zero reward!", "odds": "🎨 Random Gear Piece + Random Premium Spray Colorway.\n⚠️ Duplicate hits result in absolute zero reward output."}
            ],
            "chaos": [
                {"id": "s_box_overdrive", "name": "⚡ Overdrive Roulette", "cost": 140, "icon": "⚡", "type": "roulette", "desc": "90% chance to blow a fuse losing 1 rank from an item track. 10% chance for triple gear upgrade cascade!", "odds": "💥 Fuse Blowout (-1 Rank): 90%\n⚡ Overdrive Cascade (+1 to 3 items): 10%"},
                {"id": "s_box_allin", "name": "🎲 All-In Wedge", "cost": 260, "icon": "🎲", "type": "double", "desc": "50% chance to drop a completely dead 'Defective Fit' token. 50% chance for a massive instant +3 Rank Jump!", "odds": "⚫ Defective Fit Failure: 50%\n🎰 High-Tech Tuning (+3 Ranks): 50%"},
                {"id": "s_box_prototype", "name": "🧪 Prototype Lab", "cost": 175, "icon": "🧪", "type": "prototype", "desc": "40% Misfit calibration fail | 45% Standard Calibration (+1 Rank) | 15% Quantum Breakthrough (+4 Ranks to Elite asset).", "odds": "⚫ Prototype Misfit (Fail): 40%\n🟡 Standard Calibration (+1 Rank): 45%\n✨ Quantum Synchronization (+4 Ranks): 15%"}
            ],
            "strategy": [
                {"id": "s_box_bogo", "name": "👯 BOGO Replicator", "cost": 160, "icon": "👯", "type": "bogo", "desc": "Carries a 70% chance to duplicate an additional rank token straight onto the last item you bought manually.", "odds": "👯 Storefront Mirror Link: 70%\n📦 Global Base Baseline Roll: 30%"},
                {"id": "s_box_frenzy", "name": "📈 Discount Frenzy", "cost": st.session_state.shop_discount_frenzy_cost, "icon": "📈", "type": "frenzy", "desc": "Sequential pulls cut entry fees by 20g down to an 80g floor! Buying manual store assets resets price.", "odds": "📉 Cost Shift Step: -20g per consecutive spin\n🛡️ Floor Limit: 80g"},
                {"id": "s_box_spoon", "name": "🥄 Golden Spoon", "cost": 320, "icon": "🥄", "type": "spoon", "desc": "Luxury elite chest filtering out standard tier apparel completely. Guarantees upgrading or pulling high tier gear.", "odds": "🥄 High-Value Elite Equipment Focus: 100%"}
            ]
        }

        def execute_gear_award(item_name, rank_bonus=1):
            specs = gear_catalog[item_name]
            if item_name not in player.inventory:
                player.inventory.append(item_name)
                player.equipped_gear[item_name] = rank_bonus
                player.gear_colors[item_name] = "Basic Factory"
                msg = f"📦 **NEW ITEM UNLOCKED:** Added {item_name} at Rank +1!"
            else:
                current_rk = player.equipped_gear.get(item_name, 1)
                new_rk = min(10, current_rk + rank_bonus)
                player.equipped_gear[item_name] = new_rk
                msg = f"⚡ **GEAR UPGRADED:** Transferred rank chips to {item_name}! (Rank: {current_rk} ➔ {new_rk})"
            save_player_state()
            return specs.get("cost", 40), msg

        sections_meta = [
            ("💎 Standard Cost-Anchored Boxes", "core"),
            ("🚀 Functional Gated Lockers", "specialty"),
            ("⚡ High Variance Circuit Modifiers", "chaos"),
            ("📈 Strategic Dynamic Matrix Boxes", "strategy")
        ]

        for s_title, reg_key in sections_meta:
            st.markdown(f"#### {s_title}")
            row_cols = st.columns(4)
            for b_idx, b_conf in enumerate(SHOP_BOX_REGISTRY[reg_key]):
                with row_cols[b_idx]:
                    with st.container(border=True):
                        st.markdown(f"### {b_conf['icon']} {b_conf['name']}")
                        st.markdown(f"`{b_conf['cost']}g`")
                        st.caption(b_conf["desc"])
                        
                        t_theme = None
                        if b_conf["type"] == "theme":
                            t_theme = st.selectbox("Locker Category Target:", ['Footwear', 'Sunglasses', 'Head Gear', 'Singlets', 'Jackets', 'Shorts', 'Pants', 'Watches'], key=f"s_theme_box_sel_{b_conf['id']}")
                        
                        with st.expander("📊 View Drop Probability Scales", expanded=False):
                            st.markdown("**Current Pool Breakdown & Odds:**")
                            st.text(b_conf["odds"])
                            st.markdown("---")
                            
                            b_type = b_conf["type"]
                            if b_type == "core":
                                if "Apparel" in b_conf["name"]:
                                    st.markdown(f"**🟢 Eligible Low-Value Items (100% Chance):**\n{', '.join(p_low_display)}")
                                elif "Performance" in b_conf["name"]:
                                    st.markdown(f"**🟢 Eligible Low-Value Items (90% Chance):**\n{', '.join(p_low_display)}")
                                    st.markdown(f"**🟡 Eligible Mid-Value Items (10% Chance):**\n{', '.join(p_mid_display)}")
                                elif "Championship" in b_conf["name"]:
                                    st.markdown(f"**🟢 Eligible Low-Value Items (60% Chance):**\n{', '.join(p_low_display)}")
                                    st.markdown(f"**🟡 Eligible Mid-Value Items (30% Chance):**\n{', '.join(p_mid_display)}")
                                    st.markdown(f"**🔴 Eligible High-Value Items (10% Chance):**\n{', '.join(p_high_display)}")
                            elif b_type == "theme":
                                if t_theme:
                                    t_items = [f"{it} ({specs['cost']}g)" for it, specs in gear_catalog.items() if specs["cat"] == t_theme]
                                    st.markdown(f"**🎯 Targeted {t_theme} Items (100% Chance):**\n{', '.join(t_items)}")
                                else:
                                    st.caption("Select a category above to view item odds.")
                            elif b_type == "underdog":
                                if player.inventory:
                                    min_rk = min([int(player.equipped_gear.get(x, 1)) for x in player.inventory])
                                    u_items = [f"{x} (Rank {min_rk})" for x in player.inventory if int(player.equipped_gear.get(x, 1)) == min_rk]
                                    st.markdown(f"**🩹 Current Trailing Items (Equal Split - 100% Total):**\n{', '.join(u_items)}")
                                else:
                                    st.caption("Inventory empty.")
                            elif b_type == "colorway":
                                st.markdown("**🎨 Paint Customizations Pool (100% Overall Chance):**")
                                st.markdown("Randomly aggregates any item in the catalog alongside one of 7 color styles: White, Blue, Red, Green, Yellow, Silver, Gold.")
                            elif b_type == "prototype":
                                st.markdown("**⚫ Misfit (40%):** Nothing Gained")
                                st.markdown(f"**🟡 Calibration (+1 Rank - 45%):**\n{', '.join(p_mid_display + p_high_display)}")
                                st.markdown(f"**✨ Quantum Cascade (+4 Ranks - 15%):**\n{', '.join(p_high_display)}")
                            elif b_type == "spoon":
                                st.markdown(f"**🥄 Eligible Elite/High Items (100% Chance):**\n{', '.join(p_mid_display + p_high_display)}")
                            elif b_type == "bogo":
                                if "shop_last_bought" in st.session_state:
                                    st.markdown(f"**👯 Last Purchased Item (70% Duplicate Chance):**\n{st.session_state.shop_last_bought}")
                                    st.markdown(f"**📦 Global Baseline Items (30% Fallback Chance):**\n{', '.join(p_low_display + p_mid_display + p_high_display)}")
                                else:
                                    st.markdown(f"**📦 No item purchased yet. Defaults to Global Items (100%):**\n{', '.join(p_low_display + p_mid_display + p_high_display)}")
                            elif b_type == "roulette":
                                st.markdown("**💥 Risk Pool (90% Chance to reduce 1 Rank):** Any owned equipment asset currently above Rank 1")
                                st.markdown(f"**⚡ Jackpot Pool (10% Chance to get +1 to 3 Random Items):**\n{', '.join(p_low_display + p_mid_display + p_high_display)}")
                            elif b_type == "double":
                                st.markdown("**⚫ Failure Pool (50% Chance):** Defective Fit (Nothing Gained)")
                                st.markdown(f"**🎰 Jackpot Pool (50% Chance to get +3 Ranks to a High item):**\n{', '.join(p_high_display if p_high_display else p_low_display)}")
                            elif b_type == "frenzy":
                                st.markdown(f"**📦 Global Items Pool (100% Chance):**\n{', '.join(p_low_display + p_mid_display + p_high_display)}")

                        final_cost = b_conf["cost"]
                        is_disabled = gold_balance < final_cost or (b_conf["type"] == "underdog" and not player.inventory)
                        btn_lbl = "Open Chest"
                        
                        if st.button(btn_lbl, key=f"s_vault_btn_{b_conf['id']}", disabled=is_disabled, use_container_width=True):
                            player.gold = gold_balance - final_cost
                            
                            if b_conf["type"] == "frenzy": st.session_state.shop_discount_frenzy_cost = max(80, final_cost - 20)
                            else: st.session_state.shop_discount_frenzy_cost = 150
                            
                            pool_low, pool_mid, pool_high, all_flat = [], [], [], []
                            for it, specs in gear_catalog.items():
                                if specs["cost"] <= 40: pool_low.append(it)
                                elif 41 <= specs["cost"] <= 90: pool_mid.append(it)
                                else: pool_high.append(it)
                                all_flat.append(it)
                                
                            roll = random.random() * 100
                            chosen_pool = all_flat
                            
                            if b_conf["type"] == "core":
                                if "Apparel" in b_conf["name"]: chosen_pool = pool_low
                                elif "Performance" in b_conf["name"]: chosen_pool = pool_mid if roll < 10.0 and pool_mid else pool_low
                                elif "Championship" in b_conf["name"]: chosen_pool = pool_high if roll < 10.0 and pool_high else pool_mid if roll < 40.0 and pool_mid else pool_low
                                    
                            elif b_conf["type"] == "theme" and t_theme: chosen_pool = [it for it, specs in gear_catalog.items() if specs["cat"] == t_theme]
                            elif b_conf["type"] == "underdog":
                                min_rk = min([int(player.equipped_gear.get(x, 1)) for x in player.inventory])
                                chosen_pool = [x for x in player.inventory if int(player.equipped_gear.get(x, 1)) == min_rk]
                            elif b_conf["type"] == "spoon": chosen_pool = pool_mid + pool_high
                            elif b_conf["type"] == "bogo" and "shop_last_bought" in st.session_state and roll < 70.0:
                                chosen_pool = [st.session_state.shop_last_bought]
                                
                            # Custom override pathways for chaos/specialty variants
                            if b_conf["type"] == "prototype":
                                if roll < 40.0:
                                    st.session_state.shop_highlight_emoji = "🗑️"
                                    st.session_state.shop_highlight = "💥 **PROTOTYPE MISFIT:** The experimental hardware configuration configuration destabilized. Material scrap pass resulted in zero reward!"
                                    save_player_state()
                                elif roll < 85.0:
                                    target_it = random.choice(pool_mid + pool_high if (pool_mid + pool_high) else all_flat)
                                    val, note = execute_gear_award(target_it, rank_bonus=1)
                                    st.session_state.shop_highlight_emoji = "🧪"
                                    st.session_state.shop_highlight = f"🧪 **PROTOTYPE CALIBRATION SUCCESS:** Core structural modules balanced. {note} (Market equity value: {val}g)."
                                else:
                                    target_it = random.choice(pool_high if pool_high else all_flat)
                                    val, note = execute_gear_award(target_it, rank_bonus=4)
                                    st.session_state.shop_highlight_emoji = "✨"
                                    st.session_state.shop_highlight = f"✨ **QUANTUM CASCADE SYNCHRONIZATION!** 🧪 The laboratory chip synchronized flawlessly! Granted an instant **+4 Tuning Rank Upgrade** into {target_it}!"
                                st.rerun()

                            elif b_conf["type"] == "colorway":
                                target_it = random.choice(all_flat)
                                shades = ["White", "Blue", "Red", "Green", "Yellow", "Silver", "Gold"]
                                chosen_shade = random.choice(shades)
                                current_shade = player.gear_colors.get(target_it, "Basic Factory")
                                
                                if current_shade == chosen_shade:
                                    st.session_state.shop_highlight_emoji = "💨"
                                    st.session_state.shop_highlight = f"🎨 **COATING MISSED:** Rolled custom `{chosen_shade.upper()}` for **{target_it}**, but your locker profile already records that exact overlay! Duplicate coat resulted in zero reward output."
                                    save_player_state()
                                else:
                                    if target_it not in player.inventory:
                                        player.inventory.append(target_it)
                                        player.equipped_gear[target_it] = 1
                                    player.gear_colors[target_it] = chosen_shade
                                    save_player_state()
                                    st.session_state.shop_highlight_emoji = "🎨"
                                    st.session_state.shop_highlight = f"🎨 **CUSTOM PAINT FINISH UNLOCKED:** Successfully applied premium automotive `{chosen_shade.upper()}` spray coating layouts onto **{target_it}**!"
                                st.rerun()

                            if b_conf["type"] == "roulette":
                                if roll < 90.0:
                                    active_owned = [x for x in player.inventory if int(player.equipped_gear.get(x, 1)) > 1]
                                    if active_owned:
                                        lost_it = random.choice(active_owned)
                                        player.equipped_gear[lost_it] -= 1
                                        st.session_state.shop_highlight_emoji = "⚙️"
                                        st.session_state.shop_highlight = f"💥 **CIRCUIT SHORT: OVERDRIVE BLOWOUT!** 💥 Sizing loop collapsed! Corrupted 1 Tuning Rank from {lost_it}."
                                    else:
                                        st.session_state.shop_highlight = "💨 **OVERDRIVE LOOP:** Circuit sparked but all inventory pieces were baseline Rank 1! Zero data corrupted."
                                    save_player_state()
                                else:
                                    winners = random.sample(all_flat, min(3, len(all_flat)))
                                    wns = []
                                    for w_item in winners:
                                        execute_gear_award(w_item, rank_bonus=1)
                                        wns.append(w_item)
                                    st.session_state.shop_highlight_emoji = "⚡"
                                    st.session_state.shop_highlight = f"⚡ **OVERDRIVE JACKPOT IMMINENT ACCELERATION!** ⚡ Broke 10% odds! Forced rank additions simultaneously onto:\n\n{', '.join(wns)}!"
                                st.rerun()
                                
                            elif b_conf["type"] == "double":
                                if roll < 50.0:
                                    st.session_state.shop_highlight_emoji = "🗑️"
                                    st.session_state.shop_highlight = "💥 **FABRICATION EXCEPTION: DEFECTIVE FIT!** Sizing alignment mismatched. 260g lost in material scrap lines."
                                    save_player_state()
                                else:
                                    target_it = random.choice(pool_high or all_flat)
                                    val, note = execute_gear_award(target_it, rank_bonus=3)
                                    st.session_state.shop_highlight_emoji = "⚙️"
                                    st.session_state.shop_highlight = f"🎰 **ALL-IN CRITICAL HIT JACKPOT!** 🎲 Instant **+3 Structural Tuning Rank Upgrade** forced into {target_it} (Equity value: {val}g)!"
                                st.rerun()

                            # Execute core unboxing reward logic
                            if not chosen_pool: chosen_pool = all_flat
                            target_it = random.choice(chosen_pool)
                            val, note = execute_gear_award(target_it, rank_bonus=1)
                            st.session_state.shop_highlight_emoji = "📦"
                            st.session_state.shop_highlight = f"📦 **COMPARTMENT SEAL UNLOCKED:** Opened {b_conf['name']}! {note} (Market value: {val}g)."
                            st.rerun()
            st.markdown('<br>', unsafe_allow_html=True)

