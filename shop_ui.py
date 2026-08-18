# -*- coding: utf-8 -*-
# PART 1 OF 3: PRO SHOP SETUP, ATTRIBUTE NODE FORGE & WEATHER HUD INTEGRATION
import streamlit as st
import json
import random
from datetime import datetime

# ⚙️ EXTERNAL MASTER DATA CONFIGURATION IMPORTS
from pro_shop_config import gear_catalog, shop_boxes

def render_shop_interface(player, FILE_PATH):
    st.markdown('## 🛒 Pro Shop & Performance Equipment Forge')
    st.markdown(f"Current Gold Balance: **{int(getattr(player, 'gold', 50))}g** | Available Stat Tokens: **{getattr(player, 'stat_points', 0)}**")
    st.markdown('---')
    
    if not hasattr(player, 'inventory') or player.inventory is None: player.inventory = []
    if not hasattr(player, 'equipped_gear') or player.equipped_gear is None: player.equipped_gear = {}
    if not hasattr(player, 'gear_colors') or player.gear_colors is None: player.gear_colors = {}
        
    # --- ACTIVE ATHLETE KIT CONFIGURATION BLUEPRINT HUD HEADER ---
    st.markdown("### 🎽 Active Athlete Kit Configuration Blueprint")
    st.caption("Your single-slot equipped loadout and custom spray paint profiles currently active on your driver athlete:")
    
    kit_slots = {
        'Footwear': 'equipped_shoe_name',
        'Sunglasses': 'equipped_sunglasses_name',
        'Head Gear': 'equipped_headgear_name',
        'Singlets': 'equipped_singlet_name',
        'Jackets': 'equipped_jacket_name',
        'Shorts': 'equipped_shorts_name',
        'Pants': 'equipped_pants_name',
        'Watches': 'equipped_watch_name'
    }
    
    color_emojis = {
        "Basic Factory": "⚙️", "White": "⚪", "Blue": "🔵", "Red": "🔴", 
        "Green": "🟢", "Yellow": "🟡", "Silver": "🥈", "Gold": "👑"
    }
    
    # Render historical double-row cockpit inspection loadout layout
    kc_row1_cols = st.columns(4)
    kc_row2_cols = st.columns(4)
    all_hud_cols = kc_row1_cols + kc_row2_cols
    saved_colors = player.gear_colors
    
    equipped_brands = []
    equipped_weathers = []
    active_slot_count = 0
    
    for idx, (slot_title, attr_key) in enumerate(kit_slots.items()):
        with all_hud_cols[idx]:
            with st.container(border=True):
                active_item = getattr(player, attr_key, None)
                st.markdown(f"##### {slot_title}")
                
                if active_item and active_item in gear_catalog:
                    active_slot_count += 1
                    item_rank = int(player.equipped_gear.get(active_item, 1))
                    item_paint = saved_colors.get(active_item, "Factory")
                    paint_emoji = color_emojis.get(item_paint, "⚙️")
                    st.success(f"🎽 **{active_item}**")
                    st.markdown(f"`Rank +{item_rank}`\nVariant: {paint_emoji} `{item_paint.upper()}`")
                    
                    # Track brands and weather ratings for layout synchronization passes
                    brand_name = active_item.split()[0]
                    equipped_brands.append(brand_name)
                    equipped_weathers.append(gear_catalog[active_item].get('weather', 'All-Weather'))
                else:
                    st.info("ℹ️ Slot Empty")
                    st.caption("Equip a module from your Locker Vault below.")
                    
    # --- AUTOMATED LOADOUT ALIGNMENT CALCULATORS ---
    if active_slot_count >= 3:
        sync1, sync2 = st.columns(2)
        
        # 1. Weather Utility Synchronization Check
        unique_weather_traits = set(equipped_weathers) - {'All-Weather'}
        if len(unique_weather_traits) == 1 and len(equipped_weathers) == active_slot_count:
            active_sync_weather = list(unique_weather_traits)[0]
            with sync1:
                st.info(f"✨ **OUTFIT SYNCED ({active_sync_weather})**\n\nAll equipped loadout elements align seamlessly for specialized track environments!")
        elif len(set(equipped_weathers)) == 1 and list(set(equipped_weathers))[0] == 'All-Weather':
            with sync1:
                st.info("✨ **OUTFIT SYNCED (🌤️ All-Weather)**\n\nYour active layout achieves streamlined all-conditions baseline balancing efficiency!")
                
        # 2. Corporate Brand Synchronization Check
        if len(set(equipped_brands)) == 1:
            active_sync_brand = equipped_brands[0]
            with sync2:
                st.success(f"🔥 **BRAND SYNCED ({active_sync_brand})**\n\nYour profile aesthetics achieve full manufacturer sponsor synchronization harmony!")

    st.markdown('---')
    
    # --- LOCAL ENVIRONMENT WEATHER DATA BRIEFING HUD ---
    st.markdown("### 🌤️ Live Los Alamos Weather Tracker & Gear Advisory")
    
    # Capture runtime timestamp variables dynamically
    now = datetime.now()
    current_hour = now.hour
    time_display = now.strftime("%I:%M %p")
    date_display = now.strftime("%A, %B %d, %Y")
    
    # Dynamic Environment Resolver Mapping Engine
    if 17 <= current_hour < 20:  # 5:00 PM to 8:00 PM MDT storm window
        target_weather_tag = "Rain Jacket (Wet)"
        current_temp = 81.0
        current_uv = 1
        weather_alert_context = "Scattered mountain thunderstorms are currently active across track sectors. Rain chance is elevated at 35%. Hydrophobic layers and traction matrices are highly advised."
    elif 20 <= current_hour or current_hour < 6:  # Night tracking hours
        target_weather_tag = "Winter Jacket (Cold)"
        current_temp = 69.0
        current_uv = 0
        weather_alert_context = "Night tracking operations active. Radiation cooling has dropped trail temperatures. High thermal retention or insulated gear suggested."
    else:  # Standard daytime window
        target_weather_tag = "All-Weather"
        current_temp = 78.0
        current_uv = 6
        weather_alert_context = "Partly Sunny Skies. High UV index layer active. Track surface dry. Scattered mountain thunderstorms are expected to develop later around 5:00 PM MDT (35% chance)."

    with st.container(border=True):
        st.markdown(f"**Current Sync Time:** {time_display} | {date_display}")
        st.markdown(f"**Track Temperature:** {current_temp}°F | ☀️ Active UV Index: {current_uv}/10")
        st.caption(f"**Meteorological Briefing:** {weather_alert_context}")
        
        # --- DYNAMIC HARDWARE RECOMMENDATION GENERATOR ENGINE ---
        recommended_midday_loadout = []
        targeted_recommendation_cats = ['Footwear', 'Sunglasses', 'Head Gear', 'Singlets', 'Jackets', 'Shorts', 'Pants', 'Watches']
        
        for cat in targeted_recommendation_cats:
            matching_weather_items = [name for name, sp in gear_catalog.items() if sp['cat'] == cat and sp['weather'] == target_weather_tag]
            
            # Fallback to All-Weather wildcards if no specialized item exists for this category
            if not matching_weather_items:
                matching_weather_items = [name for name, sp in gear_catalog.items() if sp['cat'] == cat and sp['weather'] == 'All-Weather']
                
            if matching_weather_items:
                recommended_midday_loadout.append(sorted(matching_weather_items, key=lambda x: gear_catalog[x]['cost'])[0])
        
        st.markdown("##### 💡 Recommended Tactical Setup Checklist:")
        rec_cols = st.columns(3)
        
        owned_recommended_count = 0
        unowned_recommendations = []
        
        item_icon_map = {
            'Footwear': '👟', 'Sunglasses': '🕶️', 'Head Gear': '🧢', 
            'Singlets': '🎽', 'Jackets': '🧥', 'Shorts': '🩳', 'Pants': '👖', 'Watches': '⌚'
        }
        
        for r_idx, rec_item in enumerate(recommended_midday_loadout):
            if rec_item not in gear_catalog: continue
            rec_spec = gear_catalog[rec_item]
            rec_cat = rec_spec['cat']
            cat_icon = item_icon_map.get(rec_cat, '📦')
            
            is_owned = rec_item in player.inventory
            is_equipped = getattr(player, kit_slots.get(rec_cat, ''), '') == rec_item
            
            with rec_cols[r_idx % 3]:
                if is_equipped:
                    st.markdown(f"{cat_icon} **{rec_item}**\n\n✅ `ACTIVE ON KIT`")
                elif is_owned:
                    st.markdown(f"{cat_icon} **{rec_item}**\n\n⚠️ `OWNED IN VAULT`")
                    owned_recommended_count += 1
                else:
                    st.markdown(f"<span style='opacity:0.4;'>{cat_icon} {rec_item}</span>\n\n❌ *Not Acquired*", unsafe_allow_html=True)
                    unowned_recommendations.append(rec_item)
                    
        # Render macro tactical prompt controls based on locker scan
        st.write("")
        b_col1, b_col2 = st.columns(2)
        with b_col1:
            if owned_recommended_count > 0:
                if st.button("⚡ Auto-Equip Recommended Owned Gear", use_container_width=True):
                    for rec_item in recommended_midday_loadout:
                        if rec_item in player.inventory:
                            cat_key = gear_catalog[rec_item]['cat']
                            slot_var = kit_slots.get(cat_key)
                            if slot_var:
                                setattr(player, slot_var, rec_item)
                    with open(FILE_PATH, 'w', encoding='utf-8') as f:
                        json.dump(player.to_dict() if hasattr(player, 'to_dict') else player.__dict__, f, default=str, indent=4)
                    st.success("Successfully synchronized active kit with optimal daytime parameters!")
                    st.rerun()
            else:
                st.button("⚡ All Available Recommendations Active", disabled=True, use_container_width=True)
                
        with b_col2:
            if unowned_recommendations:
                st.caption(f"🛍️ **Procurement Hint:** Visit the Storefront below to secure the missing pieces of your recommended setup!")
            else:
                st.caption("🏆 **Perfect Preparation:** You own the entire recommended baseline configuration for today's track variables!")

    st.markdown('---')

    # --- ATTRIBUTE NODE ALLOCATION FORGE ---
    st.markdown('### 🏋️ Attribute Node Allocation Forge')
    sac1, sac2 = st.columns(2)
    with sac1:
        if st.button('Upgrade Base Velocity Nodes (+1 Running Token)', disabled=(getattr(player, 'stat_points', 0) < 1)):
            try:
                player.stat_points = getattr(player, 'stat_points', 0) - 1
                player.running_level = getattr(player, 'running_level', 1) + 1
                player.vo2_max = getattr(player, 'vo2_max', 40.0) + 0.5
                with open(FILE_PATH, 'w', encoding='utf-8') as f: json.dump(player.to_dict() if hasattr(player, 'to_dict') else player.__dict__, f, default=str, indent=4)
                st.success('✨ Attribute Node forged successfully!'); st.rerun()
            except Exception as e: st.error(f'Forge fault: {str(e)}')
    with sac2: st.caption(f"Current Forged Skill: Level **{getattr(player, 'running_level', 1)}** | VO2 Max Base: **{getattr(player, 'vo2_max', 40.0):.1f}**")
    st.markdown('---')

    # ==========================================
    # PERSISTENT PERSISTENCE VIEW TABS MATRIX ROUTER
    # ==========================================
    if "shop_active_tab" not in st.session_state:
        st.session_state.shop_active_tab = "🛒 Storefront procurement"
        
    tc1, tc2, tc3 = st.columns(3)
    with tc1:
        if st.button("🛒 Browse Pro Shop Storefront", use_container_width=True, type="primary" if st.session_state.shop_active_tab == "🛒 Storefront procurement" else "secondary"):
            st.session_state.shop_active_tab = "🛒 Storefront procurement"; st.rerun()
    with tc2:
        if st.button("🎁 Access Mystery Chest Vault", use_container_width=True, type="primary" if st.session_state.shop_active_tab == "🎁 Pro Chest Vault" else "secondary"):
            st.session_state.shop_active_tab = "🎁 Pro Chest Vault"; st.rerun()
    with tc3:
        if st.button("📦 Open Your Locker Gear Room Vault", use_container_width=True, type="primary" if st.session_state.shop_active_tab == "📦 Your Locker Gear Locker Vault" else "secondary"):
            st.session_state.shop_active_tab = "📦 Your Locker Gear Locker Vault"; st.rerun()
            
    st.write("")

    # --- TAB ROUTING RENDERING CONDITIONAL BLOCKS ---
    if st.session_state.shop_active_tab == "🛒 Storefront procurement":
        render_purchase_shop(player, FILE_PATH)
    elif st.session_state.shop_active_tab == "🎁 Pro Chest Vault":
        render_pro_chest_vault(player, FILE_PATH)
    elif st.session_state.shop_active_tab == "📦 Your Locker Gear Locker Vault":
        render_locker_vault(player, FILE_PATH, kit_slots)


def render_purchase_shop(player, FILE_PATH):
    st.markdown('### 🛍️ Equipment Catalog Storefront')
    cat_filter = st.selectbox('Filter Catalog Section:', ['Footwear', 'Sunglasses', 'Head Gear', 'Singlets', 'Jackets', 'Shorts', 'Pants', 'Watches'])
    
    # Filter out items belonging strictly to the selected category segment
    filtered_items = [(item, specs) for item, specs in gear_catalog.items() if specs['cat'] == cat_filter]
    
    # 💎 RENDERING ENGINE: GRIDS SPLIT INTO 4 COLUMNS PER ROW
    if not filtered_items:
        st.info(f"No catalog listings registered under section {cat_filter} yet.")
    else:
        for i in range(0, len(filtered_items), 4):
            chunk = filtered_items[i:i+4]
            cols = st.columns(4)
            
            for idx, (item, specs) in enumerate(chunk):
                with cols[idx]:
                    with st.container(border=True):
                        is_owned = item in player.inventory
                        
                        # 🎨 Dynamic Ghosted Text Pass for Owned Assets inside Grid Cells
                        if is_owned:
                            st.markdown(f"<div style='opacity: 0.3; filter: grayscale(100%); min-height: 140px;'>🎁 <b>{item}</b><br><small style='color: gray;'>Utility: {specs.get('weather', 'All-Weather')}</small><br><p style='font-size: 13px;'>{specs['desc']}</p></div>", unsafe_allow_html=True)
                            st.button('Acquired ✓', key=f'owned_{item.replace(" ", "_")}', disabled=True, use_container_width=True)
                        else:
                            st.markdown(f"<div style='min-height: 140px;'>📦 <b>{item}</b><br><small style='color: #4f46e5;'>Utility: {specs.get('weather', 'All-Weather')}</small><br><p style='font-size: 13px;'>{specs['desc']}</p></div>", unsafe_allow_html=True)
                            if st.button(f"Buy ({specs['cost']}g)", key=f'buy_{item.replace(" ", "_")}', disabled=(getattr(player, 'gold', 0) < specs['cost']), use_container_width=True):
                                try:
                                    player.gold = getattr(player, 'gold', 0) - specs['cost']
                                    player.inventory.append(item); player.equipped_gear[item] = 1
                                    player.gear_colors[item] = "Basic Factory"
                                    
                                    # Single-slot auto-equip triggers
                                    if specs['cat'] == 'Footwear' and not getattr(player, 'equipped_shoe_name', None): player.equipped_shoe_name = item
                                    elif specs['cat'] == 'Sunglasses' and not getattr(player, 'equipped_sunglasses_name', None): player.equipped_sunglasses_name = item
                                    elif specs['cat'] == 'Head Gear' and not getattr(player, 'equipped_headgear_name', None): player.equipped_headgear_name = item
                                    elif specs['cat'] == 'Singlets' and not getattr(player, 'equipped_singlet_name', None): player.equipped_singlet_name = item
                                    elif specs['cat'] == 'Jackets' and not getattr(player, 'equipped_jacket_name', None): player.equipped_jacket_name = item
                                    elif specs['cat'] == 'Shorts' and not getattr(player, 'equipped_shorts_name', None): player.equipped_shorts_name = item
                                    elif specs['cat'] == 'Pants' and not getattr(player, 'equipped_pants_name', None): player.equipped_pants_name = item
                                    elif specs['cat'] == 'Watches' and not getattr(player, 'equipped_watch_name', None): player.equipped_watch_name = item
                                    
                                    with open(FILE_PATH, 'w', encoding='utf-8') as f: json.dump(player.to_dict() if hasattr(player, 'to_dict') else player.__dict__, f, default=str, indent=4)
                                    st.success(f'🎁 Collected {item}!'); st.rerun()
                                except Exception as e: st.error(f'Store fault: {str(e)}')


def render_pro_chest_vault(player, FILE_PATH):
    st.markdown("### 🎁 Performance Mystery Chest Vault")
    st.caption("Spend accumulated gold tokens to purchase experimental hardware drops and custom spray paint profile modifiers:")
    
    # Recombining master catalog items across cost brackets for unboxing pulls
    pool_low = [name for name, sp in gear_catalog.items() if sp['cost'] <= 45]
    pool_mid = [name for name, sp in gear_catalog.items() if 45 < sp['cost'] <= 95]
    pool_high = [name for name, sp in gear_catalog.items() if sp['cost'] > 95]
    
    gold_balance = getattr(player, 'gold', 0)
    
    for idx, box in enumerate(shop_boxes):
        with st.container(border=True):
            st.markdown(f"#### {box['icon']} {box['name']} | `Cost: {box['cost']}g`")
            st.markdown(box['desc'])
            
            # --- DYNAMIC UPSTREAM POOL ODDS PREVIEW LOGIC ---
            with st.expander("📊 View Complete Drop Pool Items & Percentage Odds"):
                st.info(f"**Loot Table Probability Structure:**\n{box['odds']}")
                if box['id'] == "sb_apparel":
                    st.write("🟢 Eligible Entry-Level Drop Pool:", pool_low)
                elif box['id'] == "sb_performance":
                    st.write("🟢 Entry-Level Items (85%):", pool_low)
                    st.write("🟡 Professional Items (15%):", pool_mid)
                elif box['id'] == "sb_champ":
                    st.write("🟢 Entry Items (50%):", pool_low)
                    st.write("🟡 Professional Items (35%):", pool_mid)
                    st.write("🔴 Elite Items (15%):", pool_high)
                elif box['id'] == "sb_focus":
                    st.write("🎯 Context Mapping: Pulls 100% from whatever category filter is highlighted on the dropdown selector container row below.")
                elif box['id'] == "sb_catchup":
                    st.write("🩹 Tailored Mapping: Loops over your active account profile settings to filter items below Rank 10 dynamically.")
                elif box['id'] == "sb_proto":
                    st.write("🟡 Standard Target Options (45%):", pool_mid + pool_high)
                    st.write("🔴 Quantum Cascade Boost Targets (15%):", pool_high)
                elif box['id'] == "sb_palette":
                    st.write("🎨 Surface Targets: Every item inside the catalog can be rolled alongside White, Blue, Red, Green, Yellow, Silver, or Gold finishes.")
            
            # Additional option handles for Slot Focus Chests
            target_focus_cat = None
            if box['id'] == "sb_focus":
                target_focus_cat = st.selectbox("Select Target Chest Focus Class:", ['Footwear', 'Sunglasses', 'Head Gear', 'Singlets', 'Jackets', 'Shorts', 'Pants', 'Watches'], key=f"focus_box_select_key_{idx}")
                
            if st.button(f"Unbox {box['name']}", key=f"unbox_action_btn_{idx}", disabled=(gold_balance < box['cost'])):
                try:
                    player.gold = gold_balance - box['cost']
                    rolled_item = None
                    rolled_paint = "Basic Factory"
                    tuning_boost = 1
                    is_failure_misfit = False
                    
                    # 1. Apparel Mystery Chest
                    if box['id'] == "sb_apparel" and pool_low:
                        rolled_item = random.choice(pool_low)
                    # 2. Performance Track Chest
                    elif box['id'] == "sb_performance":
                        rolled_item = random.choice(pool_mid) if random.random() < 0.15 else random.choice(pool_low)
                    # 3. Championship Grand Chest
                    elif box['id'] == "sb_champ":
                        roll = random.random()
                        if roll < 0.15: rolled_item = random.choice(pool_high)
                        elif roll < 0.50: rolled_item = random.choice(pool_mid)
                        else: rolled_item = random.choice(pool_low)
                    # 4. Slot Focus Chest
                    elif box['id'] == "sb_focus" and target_focus_cat:
                        valid_sub_pool = [n for name, sp in gear_catalog.items() if sp['cat'] == target_focus_cat]
                        if valid_sub_pool: rolled_item = random.choice(valid_sub_pool)
                    # 5. Trailing Catch-Up Chest
                    elif box['id'] == "sb_catchup":
                        owned_ranks = [player.equipped_gear.get(x, 1) for x in player.inventory if x in gear_catalog]
                        if owned_ranks:
                            lowest_rank_value = min(owned_ranks)
                            catchup_pool = [x for x in player.inventory if x in gear_catalog and player.equipped_gear.get(x, 1) == lowest_rank_value]
                            if catchup_pool: rolled_item = random.choice(catchup_pool)
                        if not rolled_item and list(gear_catalog.keys()):
                            rolled_item = random.choice(list(gear_catalog.keys()))
                    # 6. Prototype Lab Chest (40% Failure, 45% standard +1, 15% quantum +4)
                    elif box['id'] == "sb_proto":
                        proto_roll = random.random()
                        if proto_roll < 0.40:
                            is_failure_misfit = True
                        elif proto_roll < 0.85:
                            rolled_item = random.choice(pool_mid + pool_high)
                            tuning_boost = 1
                        else:
                            rolled_item = random.choice(pool_high)
                            tuning_boost = 4
                    # 7. Paint Palette Box (Duplicate combos result in complete failure)
                    elif box['id'] == "sb_palette":
                        rolled_item = random.choice(list(gear_catalog.keys()))
                        rolled_paint = random.choice(["White", "Blue", "Red", "Green", "Yellow", "Silver", "Gold"])
                        
                    # --- COMMIT UNBOXING TRANSACTION ---
                    if is_failure_misfit:
                        with open(FILE_PATH, 'w', encoding='utf-8') as f: json.dump(player.to_dict() if hasattr(player, 'to_dict') else player.__dict__, f, default=str, indent=4)
                        st.error("💥 **Prototype Lab Misfit Failure:** Sizing and alignment calibration malfunctioned. Drop components vaporized!")
                        st.session_state.shop_emoji_rain_trigger = "💥"
                        st.rerun()
                        
                    elif rolled_item:
                        notice_banner = ""
                        if box['id'] == "sb_palette":
                            current_registered_paint = player.gear_colors.get(rolled_item, "Basic Factory")
                            if rolled_item in player.inventory and current_registered_paint == rolled_paint:
                                notice_banner = f"❌ **Duplicate Coating Alignment:** Rolled {rolled_item} in {rolled_paint.upper()}, but you already own that colorway profile. Complete miss, no rewards issued!"
                                st.error(notice_banner)
                            else:
                                if rolled_item not in player.inventory:
                                    player.inventory.append(rolled_item)
                                    player.equipped_gear[rolled_item] = 1
                                player.gear_colors[rolled_item] = rolled_paint
                                notice_banner = f"🎨 **Paint Palette Unboxed:** Successfully applied {rolled_paint.upper()} custom coating over {rolled_item}!"
                                st.success(notice_banner)
                        else:
                            if rolled_item not in player.inventory:
                                player.inventory.append(rolled_item)
                                player.equipped_gear[rolled_item] = tuning_boost
                                player.gear_colors[rolled_item] = "Basic Factory"
                                notice_banner = f"🎁 **New Unboxing Unlocked:** Collected permanent asset entry: {rolled_item}!"
                            else:
                                previous_rank = player.equipped_gear.get(rolled_item, 1)
                                player.equipped_gear[rolled_item] = min(10, previous_rank + tuning_boost)
                                notice_banner = f"⚡ **Tuning Rank Upgrade:** Pulled duplicate entry for {rolled_item}. Performance hardware auto-tuned by +{tuning_boost} Ranks (Rank {player.equipped_gear[rolled_item]}/10)!"
                            st.success(notice_banner)
                            
                        with open(FILE_PATH, 'w', encoding='utf-8') as f: json.dump(player.to_dict() if hasattr(player, 'to_dict') else player.__dict__, f, default=str, indent=4)
                        st.session_state.shop_emoji_rain_trigger = gear_catalog[rolled_item].get('icon', '👟') if box['id'] != "sb_palette" else "🎨"
                        st.rerun()
                except Exception as e: st.error(f'Unboxing fault: {str(e)}')


def render_locker_vault(player, FILE_PATH, kit_slots):
    st.markdown('### 📦 Your Locker Gear Locker Vault')
    if not player.inventory: 
        st.info('Your equipment chest is empty. Run tracks to generate gold balances.')
    else:
        vault_tab_filter = st.radio('View Locker Category:', ['Footwear', 'Sunglasses', 'Head Gear', 'Singlets', 'Jackets', 'Shorts', 'Pants', 'Watches'], horizontal=True)
        
        active_slot_variable = kit_slots[vault_tab_filter]
        currently_equipped_item = getattr(player, active_slot_variable, None)
        category_items = [item for item in player.inventory if item in gear_catalog and gear_catalog[item]['cat'] == vault_tab_filter]
        
        if not category_items: 
            st.info(f"No collected item entries inside {vault_tab_filter} yet.")
        else:
            for idx, owned_item in enumerate(category_items):
                curr_level = min(10, max(1, int(player.equipped_gear.get(owned_item, 1))))
                base_cost = gear_catalog.get(owned_item, {'cost': 40})['cost']
                gold_balance = getattr(player, 'gold', 0); is_maxed = curr_level >= 10
                next_level_cost = int(base_cost * (curr_level + 1) * 0.5 * curr_level)
                is_equipped = (owned_item == currently_equipped_item)
                
                active_paint = player.gear_colors.get(owned_item, "Basic Factory")
                color_emojis = {
                    "Basic Factory": "⚙️", "White": "⚪", "Blue": "🔵", "Red": "🔴", 
                    "Green": "🟢", "Yellow": "🟡", "Silver": "🥈", "Gold": "👑"
                }
                current_emoji = color_emojis.get(active_paint, "⚙️")
                
                with st.container(border=True):
                    st.markdown(f"🏅 **{owned_item}** | *Utility: {gear_catalog[owned_item].get('weather', 'All-Weather')}*")
                    v1, v2 = st.columns(2)
                    with v1:
                        st.markdown(f"`Tier Status: Rank {curr_level}/10`")
                        st.markdown(f"🎨 Style: {current_emoji} `{active_paint.upper()}`")
                        st.progress(float(curr_level / 10.0))
                        
                        if is_equipped: 
                            st.button('🎽 ACTIVE ON KIT', key=f'act_slot_eq_{idx}', disabled=True)
                        else:
                            if st.button('🟢 Equip Gear', key=f'equip_slot_action_{idx}'):
                                try:
                                    setattr(player, active_slot_variable, owned_item)
                                    with open(FILE_PATH, 'w', encoding='utf-8') as f: json.dump(player.to_dict() if hasattr(player, 'to_dict') else player.__dict__, f, default=str, indent=4)
                                    st.success(f'⚡ Equipped {owned_item}!'); st.rerun()
                                except Exception: pass
                    with v2:
                        available_shades = ["Basic Factory", "White", "Blue", "Red", "Green", "Yellow", "Silver", "Gold"]
                        chosen_shade = st.selectbox(
                            "Stage Color Option:",
                            options=available_shades,
                            index=available_shades.index(active_paint) if active_paint in available_shades else 0,
                            key=f"paint_selector_{idx}_{owned_item.replace(' ', '_')}"
                        )
                        
                        if chosen_shade != active_paint:
                            if st.button(f"🎨 Apply Colorway (-15g)", key=f"purchase_color_btn_{idx}_{owned_item.replace(' ', '_')}", disabled=(gold_balance < 15)):
                                try:
                                    player.gold = gold_balance - 15
                                    player.gear_colors[owned_item] = chosen_shade
                                    with open(FILE_PATH, 'w', encoding='utf-8') as f: json.dump(player.to_dict() if hasattr(player, 'to_dict') else player.__dict__, f, default=str, indent=4)
                                    st.success(f"⚡ Successfully applied {chosen_shade}!"); st.rerun()
                                except Exception: pass
                                
                            if gold_balance < 15:
                                st.error("❌ Insufficient gold balance to repurchase coating variants.")
                                
                        if is_maxed: 
                            st.button('👑 MAX RANK', key=f'max_slot_rank_{idx}', disabled=True)
                        else:
                            if st.button(f"Tune (+{next_level_cost}g)", key=f'tune_slot_action_{idx}', disabled=(gold_balance < next_level_cost)):
                                try:
                                    player.gold = gold_balance - next_level_cost
                                    player.equipped_gear[owned_item] = curr_level + 1
                                    with open(FILE_PATH, 'w', encoding='utf-8') as f: json.dump(player.to_dict() if hasattr(player, 'to_dict') else player.__dict__, f, default=str, indent=4)
                                    st.success(f'⚡ Tuned asset to Rank +{curr_level + 1}!'); st.rerun()
                                except Exception as e: st.error(f'Tuning fault: {str(e)}')

