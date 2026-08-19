# -*- coding: utf-8 -*-
"""
PRO SHOP & PERFORMANCE EQUIPMENT FORGE (shop_ui.py)
Manages apparel procurement, gear unboxing mechanics, custom colorway styling, 
and local track weather recommendation algorithms.
Integrates base64 asset graphics streaming with an automatic high-fidelity emoji fallback.
100% focused on organic running performance. All automotive terminology removed.
"""

import streamlit as st
import json
import random
import os
import base64
from datetime import datetime

# ⚙️ EXTERNAL MASTER DATA CONFIGURATION IMPORTS
from pro_shop_config import gear_catalog, shop_boxes

# Global mapping for category icons
ITEM_ICON_MAP = {
    'Footwear': '👟', 'Sunglasses': '🕶️', 'Head Gear': '🧢', 
    'Singlets': '🎽', 'Jackets': '🧥', 'Shorts': '🩳', 'Pants': '👖', 'Watches': '⌚'
}

def render_shop_asset(item_name: str, fallback_emoji: str, size_px: int = 60) -> str:
    """
    Checks if a local asset image exists on disk for the specified gear piece,
    encodes it as a base64 inline string, and streams it. Falls back to an emoji container if missing.
    """
    safe_filename = item_name.lower().replace(" ", "_").replace("[", "").replace("]", "").replace("-", "_")
    img_path = f"images/pro_shop/{safe_filename}.png"
    
    if os.path.exists(img_path):
        try:
            with open(img_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
            return f'<img src="data:image/png;base64,{encoded_string}" style="width: {size_px}px; height: {size_px}px; object-fit: contain; border-radius: 6px; filter: drop-shadow(0px 0px 4px rgba(0, 240, 255, 0.25)); margin-bottom: 4px;">'
        except Exception:
            pass
            
    return f'<div style="font-size: {int(size_px * 0.55)}px; line-height: {size_px}px; height: {size_px}px; width: {size_px}px; text-align: center; margin-bottom: 4px; border: 2px dashed rgba(255,255,255,0.12); border-radius: 8px; background: rgba(255,255,255,0.015); display: inline-block;">{fallback_emoji}</div>'

def render_shop_interface(player, FILE_PATH):
    st.markdown('## 🛒 Pro Shop & Performance Equipment Forge')
    st.markdown(f"Current Gold Balance: **{int(getattr(player, 'gold', 50))}g** | Available Stat Tokens: **{getattr(player, 'stat_points', 0)}**")
    st.markdown('---')
    
    # =========================================================================
    # 🔔 PERSISTENT UNBOXING REVEAL CONTAINER & TOAST MANAGER
    # =========================================================================
    if "last_unboxed_item" in st.session_state:
        unboxed = st.session_state.last_unboxed_item
        item_name = unboxed["name"]
        item_msg = unboxed["message"]
        
        with st.container(border=True):
            st.markdown("<h3 style='text-align: center; color: #ff9800; margin-top: 4px; margin-bottom: 14px;'>🎉 REWARD UNBOXING REVEAL 🎉</h3>", unsafe_allow_html=True)
            col_rev_img, col_rev_txt = st.columns([1, 5])
            with col_rev_img:
                spec_lookup = gear_catalog.get(item_name, {})
                cat_lookup = spec_lookup.get('cat', '')
                fallback_ico = ITEM_ICON_MAP.get(cat_lookup, '👟')
                img_html = render_shop_asset(item_name, fallback_ico, size_px=80)
                st.markdown(f'<div style="text-align: center; background: rgba(255,255,255,0.02); padding: 12px; border-radius: 8px; border: 1px dashed rgba(255,255,255,0.15); margin-bottom: 4px;">{img_html}</div>', unsafe_allow_html=True)
            with col_rev_txt:
                st.markdown(f"#### {item_name}")
                st.markdown(f"{item_msg}")
                st.caption(f"Category Group: **{cat_lookup}** | Dynamic Track Utility: **{spec_lookup.get('weather', 'All-Weather')}**")
            
            st.write("")
            if st.button("Claim Item & Close Reveal Window", key="dismiss_unbox_reveal_btn", use_container_width=True, type="primary"):
                del st.session_state.last_unboxed_item
                st.rerun()
        st.markdown('---')

    if "shop_toast_message" in st.session_state:
        st.success(st.session_state.shop_toast_message, icon="✨")
        del st.session_state.shop_toast_message

    # =========================================================================
    # 🎰 PERSISTENT HIGH-CONTRAST EMOJI RAIN MANAGER
    # =========================================================================
    if "shop_emoji_rain_trigger" in st.session_state:
        falling_emoji = st.session_state.shop_emoji_rain_trigger
        rain_html = '<div style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: 999999; overflow: hidden;">'
        for i in range(25):
            left_pos = random.randint(3, 97)
            delay = random.uniform(0.0, 1.8)
            duration = random.uniform(2.2, 4.0)
            size = random.randint(24, 46)
            rain_html += f'<div style="position: absolute; top: -60px; left: {left_pos}%; font-size: {size}px; animation: shopRainAnim {duration}s linear {delay}s forwards; pointer-events: none;">{falling_emoji}</div>'
        rain_html += '</div><style>@keyframes shopRainAnim { 0% { transform: translateY(0) rotate(0deg); opacity: 1; } 85% { opacity: 1; } 100% { transform: translateY(108vh) rotate(360deg); opacity: 0; } }</style>'
        st.markdown(rain_html, unsafe_allow_html=True)
        del st.session_state.shop_emoji_rain_trigger

    if not hasattr(player, 'inventory') or player.inventory == None: 
        player.inventory = []
    if not hasattr(player, 'equipped_gear') or player.equipped_gear == None: 
        player.equipped_gear = {}
    if not hasattr(player, 'gear_colors') or player.gear_colors == None: 
        player.gear_colors = {}

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
        "Default Issue": "⚙️", "White": "⚪", "Blue": "🔵", "Red": "🔴", 
        "Green": "🟢", "Yellow": "🟡", "Silver": "🥈", "Gold": "👑"
    }
        
    # --- ATTRIBUTE NODE ALLOCATION FORGE ---
    st.markdown('### 🏋️ Attribute Node Allocation Forge')
    sac1, sac2 = st.columns(2)
    with sac1:
        if st.button('Upgrade Base Velocity Nodes (+1 Running Token)', disabled=(getattr(player, 'stat_points', 0) < 1)):
            try:
                player.stat_points = getattr(player, 'stat_points', 0) - 1
                player.running_level = getattr(player, 'running_level', 1) + 1
                player.vo2_max = getattr(player, 'vo2_max', 40.0) + 0.5
                with open(FILE_PATH, 'w', encoding='utf-8') as f: 
                    json.dump(player.to_dict() if hasattr(player, 'to_dict') else player.__dict__, f, default=str, indent=4)
                st.session_state.shop_toast_message = f"✨ Attribute Node forged successfully! VO2 Max scaled to {player.vo2_max:.1f}."
                st.rerun()
            except Exception as e: 
                st.error(f'Forge fault: {str(e)}')
    with sac2: 
        st.caption(f"Current Forged Skill: Level **{getattr(player, 'running_level', 1)}** | VO2 Max Base: **{getattr(player, 'vo2_max', 40.0):.1f}**")
    st.markdown('---')

    # ==========================================
    # PERSISTENT VIEW TABS MATRIX ROUTER
    # ==========================================
    if "shop_active_tab" not in st.session_state:
        st.session_state.shop_active_tab = "🎽 Active Kit Blueprint"
        
    tc1, tc2, tc3, tc4 = st.columns(4)
    with tc1:
        if st.button("🎽 View Active Kit Blueprint", use_container_width=True, type="primary" if st.session_state.shop_active_tab == "🎽 Active Kit Blueprint" else "secondary"):
            st.session_state.shop_active_tab = "🎽 Active Kit Blueprint"
            st.rerun()
    with tc2:
        if st.button("🛒 Browse Pro Shop Storefront", use_container_width=True, type="primary" if st.session_state.shop_active_tab == "🛒 Storefront procurement" else "secondary"):
            st.session_state.shop_active_tab = "🛒 Storefront procurement"
            st.rerun()
    with tc3:
        if st.button("🎁 Access Mystery Chest Vault", use_container_width=True, type="primary" if st.session_state.shop_active_tab == "🎁 Pro Chest Vault" else "secondary"):
            st.session_state.shop_active_tab = "🎁 Pro Chest Vault"
            st.rerun()
    with tc4:
        if st.button("📦 My Gear", use_container_width=True, type="primary" if st.session_state.shop_active_tab == "📦 My Gear" else "secondary"):
            st.session_state.shop_active_tab = "📦 My Gear"
            st.rerun()
            
    st.write("")

    if st.session_state.shop_active_tab == "🎽 Active Kit Blueprint":
        render_kit_blueprint(player, FILE_PATH, kit_slots, color_emojis)
    elif st.session_state.shop_active_tab == "🛒 Storefront procurement":
        render_purchase_shop(player, FILE_PATH)
    elif st.session_state.shop_active_tab == "🎁 Pro Chest Vault":
        render_pro_chest_vault(player, FILE_PATH)
    elif st.session_state.shop_active_tab == "📦 My Gear":
        render_locker_vault(player, FILE_PATH, kit_slots)


def render_kit_blueprint(player, FILE_PATH, kit_slots, color_emojis):
    """Renders the single-slot active loadout setup and weather tracker checks."""
    st.markdown("### 🎽 Active Athlete Kit Configuration Blueprint")
    st.caption("Your single-slot equipped loadout and custom colorway variants currently active on your runner athlete:")
    
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
                    item_style = saved_colors.get(active_item, "Default Issue")
                    style_emoji = color_emojis.get(item_style, "⚙️")
                    
                    box_icon = gear_catalog[active_item].get('icon', '🎽')
                    img_html = render_shop_asset(active_item, box_icon, size_px=45)
                    st.markdown(f'<div style="display: flex; align-items: center; gap: 8px;">{img_html}<div><b>{active_item}</b></div></div>', unsafe_allow_html=True)
                    st.markdown(f"`Optimization: Rank +{item_rank}`\nVariant: {style_emoji} `{item_style.upper()}`")
                    
                    brand_name = active_item.split()[0]
                    equipped_brands.append(brand_name)
                    equipped_weathers.append(gear_catalog[active_item].get('weather', 'All-Weather'))
                else:
                    st.info("ℹ️ Slot Empty")
                    st.caption("Equip a gear piece from your locker inventory.")
                    
    # --- AUTOMATED LOADOUT ALIGNMENT CALCULATORS ---
    if active_slot_count >= 3:
        sync1, sync2 = st.columns(2)
        
        unique_weather_traits = set(equipped_weathers) - {'All-Weather'}
        if len(unique_weather_traits) == 1 and len(equipped_weathers) == active_slot_count:
            active_sync_weather = list(unique_weather_traits)[0]
            with sync1:
                st.info(f"✨ **OUTFIT SYNCED ({active_sync_weather})**\n\nAll equipped apparel elements align seamlessly for specialized track environments!")
        elif len(set(equipped_weathers)) == 1 and list(set(equipped_weathers))[0] == 'All-Weather':
            with sync1:
                st.info("✨ **OUTFIT SYNCED (🌤️ All-Weather)**\n\nYour active layout achieves streamlined all-conditions baseline balancing efficiency!")
                
        if len(set(equipped_brands)) == 1:
            active_sync_brand = equipped_brands[0]
            with sync2:
                st.success(f"🔥 **BRAND SYNCED ({active_sync_brand})**\n\nYour profile aesthetics achieve full brand sponsor synchronization harmony!")

    st.markdown('---')
    
    # --- LOCAL ENVIRONMENT WEATHER DATA BRIEFING HUD ---
    st.markdown("### 🌤️ Live Los Alamos Weather Tracker & Gear Advisory")
    
    now = datetime.now()
    current_hour = now.hour
    time_display = now.strftime("%I:%M %p")
    date_display = now.strftime("%A, %B %d, %Y")
    
    if 17 <= current_hour < 20:
        target_weather_tag = "Rain Jacket (Wet)"
        current_temp = 81.0
        current_uv = 1
        weather_alert_context = "Scattered mountain thunderstorms are currently active across track sectors. Rain chance is elevated at 35%. Hydrophobic layers and traction matrices are highly advised."
    elif 20 <= current_hour or current_hour < 6:
        target_weather_tag = "Winter Jacket (Cold)"
        current_temp = 69.0
        current_uv = 0
        weather_alert_context = "Night training operations active. Radiation cooling has dropped trail temperatures. High thermal retention or insulated gear suggested."
    else:
        target_weather_tag = "All-Weather"
        current_temp = 78.0
        current_uv = 6
        weather_alert_context = "Partly Sunny Skies. High UV index layer active. Track surface dry. Scattered mountain thunderstorms are expected to develop later around 5:00 PM MDT (35% chance)."

    with st.container(border=True):
        st.markdown(f"**Current Sync Time:** {time_display} | {date_display}")
        st.markdown(f"**Track Temperature:** {current_temp}°F | ☀️ Active UV Index: {current_uv}/10")
        st.caption(f"**Meteorological Briefing:** {weather_alert_context}")
        
        recommended_midday_loadout = []
        targeted_recommendation_cats = ['Footwear', 'Sunglasses', 'Head Gear', 'Singlets', 'Jackets', 'Shorts', 'Pants', 'Watches']
        
        for cat in targeted_recommendation_cats:
            matching_weather_items = [name for name, sp in gear_catalog.items() if sp['cat'] == cat and sp['weather'] == target_weather_tag]
            if not matching_weather_items:
                matching_weather_items = [name for name, sp in gear_catalog.items() if sp['cat'] == cat and sp['weather'] == 'All-Weather']
            if matching_weather_items:
                recommended_midday_loadout.append(sorted(matching_weather_items, key=lambda x: gear_catalog[x]['cost'])[0])
        
        st.markdown("##### 💡 Recommended Tactical Setup Checklist:")
        rec_cols = st.columns(3)
        
        owned_recommended_count = 0
        unowned_recommendations = []
        
        for r_idx, rec_item in enumerate(recommended_midday_loadout):
            if rec_item not in gear_catalog: 
                continue
            rec_spec = gear_catalog[rec_item]
            rec_cat = rec_spec['cat']
            cat_icon = ITEM_ICON_MAP.get(rec_cat, '📦')
            
            is_owned = rec_item in player.inventory
            is_equipped = getattr(player, kit_slots.get(rec_cat, ''), '') == rec_item
            
            with rec_cols[r_idx % 3]:
                img_html = render_shop_asset(rec_item, cat_icon, size_px=40)
                st.markdown(f'<div style="display: flex; align-items: center; gap: 8px;">{img_html}<div><b>{rec_item}</b></div></div>', unsafe_allow_html=True)
                if is_equipped:
                    st.markdown("✅ `ACTIVE ON KIT`")
                elif is_owned:
                    st.markdown("⚠️ `OWNED IN VAULT`")
                    owned_recommended_count += 1
                else:
                    st.markdown("❌ *Not Acquired*")
                    unowned_recommendations.append(rec_item)
                    
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
                    st.session_state.shop_toast_message = "Successfully synchronized active apparel kit with optimal training parameters!"
                    st.rerun()
            else:
                st.button("⚡ All Available Recommendations Active", disabled=True, use_container_width=True)
                
        with b_col2:
            if unowned_recommendations:
                st.caption(f"🛍️ **Procurement Hint:** Visit the Storefront tab to secure the missing pieces of your recommended setup!")
            else:
                st.caption("🏆 **Perfect Preparation:** You own the entire recommended baseline configuration for today's training variables!")


def render_purchase_shop(player, FILE_PATH):
    st.markdown('### 🛍️ Equipment Catalog Storefront')
    
    if "purchase_shop_cat" not in st.session_state:
        st.session_state.purchase_shop_cat = 'Footwear'
        
    categories = ['Footwear', 'Sunglasses', 'Head Gear', 'Singlets', 'Jackets', 'Shorts', 'Pants', 'Watches']
    
    cat_cols = st.columns(8)
    for c_idx, cat_name in enumerate(categories):
        with cat_cols[c_idx]:
            is_sel = (st.session_state.purchase_shop_cat == cat_name)
            icon = ITEM_ICON_MAP.get(cat_name, '🎽')
            if st.button(f"{icon}\n{cat_name}", key=f"btn_store_filter_{cat_name}", type="primary" if is_sel else "secondary", use_container_width=True):
                st.session_state.purchase_shop_cat = cat_name
                st.rerun()
                
    cat_filter = st.session_state.purchase_shop_cat
    filtered_items = [(item, specs) for item, specs in gear_catalog.items() if specs['cat'] == cat_filter]
    
    if not filtered_items:
        st.info(f"No catalog listings registered under section {cat_filter} yet.")
    else:
        st.write("")
        for i in range(0, len(filtered_items), 4):
            chunk = filtered_items[i:i+4]
            cols = st.columns(4)
            
            for idx, (item, specs) in enumerate(chunk):
                with cols[idx]:
                    with st.container(border=True):
                        is_owned = item in player.inventory
                        cat_icon = specs.get('icon', '🎽')
                        img_html = render_shop_asset(item, cat_icon, size_px=55)
                        
                        if is_owned:
                            st.markdown(f'<div style="opacity: 0.3; filter: grayscale(100%); min-height: 190px; text-align: center;">{img_html}<br><b>{item}</b><br><small style="color: gray;">Utility: {specs.get("weather", "All-Weather")}</small><br><p style="font-size: 13px; margin-top: 4px;">{specs["desc"]}</p></div>', unsafe_allow_html=True)
                            st.button('Acquired ✓', key=f'owned_{item.replace(" ", "_")}', disabled=True, use_container_width=True)
                        else:
                            st.markdown(f'<div style="min-height: 190px; text-align: center;">{img_html}<br><b>{item}</b><br><small style="color: #4f46e5;">Utility: {specs.get("weather", "All-Weather")}</small><br><p style="font-size: 13px; margin-top: 4px;">{specs["desc"]}</p></div>', unsafe_allow_html=True)
                            if st.button(f"Buy ({specs['cost']}g)", key=f'buy_{item.replace(" ", "_")}', disabled=(getattr(player, 'gold', 0) < specs['cost']), use_container_width=True):
                                try:
                                    player.gold = getattr(player, 'gold', 0) - specs['cost']
                                    player.inventory.append(item)
                                    player.equipped_gear[item] = 1
                                    player.gear_colors[item] = "Default Issue"
                                    
                                    if specs['cat'] == 'Footwear' and not getattr(player, 'equipped_shoe_name', None): player.equipped_shoe_name = item
                                    elif specs['cat'] == 'Sunglasses' and not getattr(player, 'equipped_sunglasses_name', None): player.equipped_sunglasses_name = item
                                    elif specs['cat'] == 'Head Gear' and not getattr(player, 'equipped_headgear_name', None): player.equipped_headgear_name = item
                                    elif specs['cat'] == 'Singlets' and not getattr(player, 'equipped_singlet_name', None): player.equipped_singlet_name = item
                                    elif specs['cat'] == 'Jackets' and not getattr(player, 'equipped_jacket_name', None): player.equipped_jacket_name = item
                                    elif specs['cat'] == 'Shorts' and not getattr(player, 'equipped_shorts_name', None): player.equipped_shorts_name = item
                                    elif specs['cat'] == 'Pants' and not getattr(player, 'equipped_pants_name', None): player.equipped_pants_name = item
                                    elif specs['cat'] == 'Watches' and not getattr(player, 'equipped_watch_name', None): player.equipped_watch_name = item
                                    
                                    with open(FILE_PATH, 'w', encoding='utf-8') as f: 
                                        json.dump(player.to_dict() if hasattr(player, 'to_dict') else player.__dict__, f, default=str, indent=4)
                                    st.session_state.shop_toast_message = f"🛍️ Successfully purchased and added {item} to your vault locker!"
                                    st.rerun()
                                except Exception as e: 
                                    st.error(f'Store fault: {str(e)}')


def render_pro_chest_vault(player, FILE_PATH):
    st.markdown("### 🎁 Performance Mystery Chest Vault")
    st.caption("Spend accumulated gold tokens to purchase experimental apparel gear drops and premium custom colorway variants:")
    
    pool_low = [name for name, sp in gear_catalog.items() if sp['cost'] <= 45]
    pool_mid = [name for name, sp in gear_catalog.items() if 45 < sp['cost'] <= 95]
    pool_high = [name for name, sp in gear_catalog.items() if sp['cost'] > 95]
    
    gold_balance = getattr(player, 'gold', 0)
    
    for idx, box in enumerate(shop_boxes):
        with st.container(border=True):
            box_img_html = render_shop_asset(box['name'], box['icon'], size_px=50)
            
            st.markdown(f'<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 6px;">{box_img_html}<div><h4 style="margin:0;">{box["name"]}</h4><span style="color: #ff9800; font-weight: bold;">Cost: {box["cost"]}g</span></div></div>', unsafe_allow_html=True)
            st.markdown(box['desc'])
            
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
                    st.write("🎯 Context Mapping: Pulls 100% from whatever category filter is highlighted on the button array row above.")
                elif box['id'] == "sb_catchup":
                    st.write("🩹 Tailored Mapping: Loops over your active account profile settings to filter items below Rank 10 dynamically.")
                elif box['id'] == "sb_proto":
                    st.write("🟡 Standard Target Options (45%):", pool_mid + pool_high)
                    st.write("🔴 Quantum Cascade Boost Targets (15%):", pool_high)
                elif box['id'] == "sb_palette":
                    st.write("🎨 Style Targets: Every item inside the catalog can be rolled alongside White, Blue, Red, Green, Yellow, Silver, or Gold finishes.")
            
            target_focus_cat = None
            if box['id'] == "sb_focus":
                target_focus_cat = st.selectbox("Select Target Chest Focus Class:", ['Footwear', 'Sunglasses', 'Head Gear', 'Singlets', 'Jackets', 'Shorts', 'Pants', 'Watches'], key=f"focus_box_select_key_{idx}")
                
            if st.button(f"Unbox {box['name']}", key=f"unbox_action_btn_{idx}", disabled=(gold_balance < box['cost'])):
                try:
                    player.gold = gold_balance - box['cost']
                    rolled_item = None
                    rolled_style = "Default Issue"
                    gear_boost = 1
                    is_failure_misfit = False
                    
                    if box['id'] == "sb_apparel" and pool_low:
                        rolled_item = random.choice(pool_low)
                    elif box['id'] == "sb_performance":
                        rolled_item = random.choice(pool_mid) if random.random() < 0.15 else random.choice(pool_low)
                    elif box['id'] == "sb_champ":
                        roll = random.random()
                        if roll < 0.15: 
                            rolled_item = random.choice(pool_high)
                        elif roll < 0.50: 
                            rolled_item = random.choice(pool_mid)
                        else: 
                            rolled_item = random.choice(pool_low)
                    elif box['id'] == "sb_focus" and target_focus_cat:
                        valid_sub_pool = [name for name, sp in gear_catalog.items() if sp['cat'] == target_focus_cat]
                        if valid_sub_pool: 
                            rolled_item = random.choice(valid_sub_pool)
                    elif box['id'] == "sb_catchup":
                        owned_ranks = [player.equipped_gear.get(x, 1) for x in player.inventory if x in gear_catalog]
                        if owned_ranks:
                            lowest_rank_value = min(owned_ranks)
                            catchup_pool = [x for x in player.inventory if x in gear_catalog and player.equipped_gear.get(x, 1) == lowest_rank_value]
                            if catchup_pool: 
                                rolled_item = random.choice(catchup_pool)
                        if not rolled_item and list(gear_catalog.keys()):
                            rolled_item = random.choice(list(gear_catalog.keys()))
                    elif box['id'] == "sb_proto":
                        proto_roll = random.random()
                        if proto_roll < 0.40:
                            is_failure_misfit = True
                        elif proto_roll < 0.85:
                            rolled_item = random.choice(pool_mid + pool_high)
                            gear_boost = 1
                        else:
                            rolled_item = random.choice(pool_high)
                            gear_boost = 4
                    elif box['id'] == "sb_palette":
                        rolled_item = random.choice(list(gear_catalog.keys()))
                        rolled_style = random.choice(["White", "Blue", "Red", "Green", "Yellow", "Silver", "Gold"])
                        
                    if is_failure_misfit:
                        with open(FILE_PATH, 'w', encoding='utf-8') as f: 
                            json.dump(player.to_dict() if hasattr(player, 'to_dict') else player.__dict__, f, default=str, indent=4)
                        st.session_state.shop_toast_message = "💥 **Prototype Lab Calibration Failure:** Sizing and alignment matching malfunctioned. Drop components vaporized!"
                        st.session_state.shop_emoji_rain_trigger = "💥"
                        st.rerun()
                        
                    elif rolled_item:
                        notice_banner = ""
                        if box['id'] == "sb_palette":
                            current_registered_style = player.gear_colors.get(rolled_item, "Default Issue")
                            if rolled_item in player.inventory and current_registered_style == rolled_style:
                                notice_banner = f"❌ **Duplicate Alignment:** Rolled {rolled_item} in {rolled_style.upper()}, but you already own that colorway. Profile miss, no rewards issued!"
                            else:
                                if rolled_item not in player.inventory:
                                    player.inventory.append(rolled_item)
                                    player.equipped_gear[rolled_item] = 1
                                player.gear_colors[rolled_item] = rolled_style
                                notice_banner = f"🎨 **Colorway Unboxed:** Successfully applied {rolled_style.upper()} custom variant over {rolled_item}!"
                        else:
                            if rolled_item not in player.inventory:
                                player.inventory.append(rolled_item)
                                player.equipped_gear[rolled_item] = gear_boost
                                player.gear_colors[rolled_item] = "Default Issue"
                                notice_banner = f"🎁 **New Apparel Unlocked:** Collected permanent asset: {rolled_item}!"
                            else:
                                previous_rank = player.equipped_gear.get(rolled_item, 1)
                                player.equipped_gear[rolled_item] = min(10, previous_rank + gear_boost)
                                notice_banner = f"⚡ **Gear Optimization Upgrade:** Pulled duplicate entry for {rolled_item}. Performance gear auto-optimized by +{gear_boost} Ranks (Rank {player.equipped_gear[rolled_item]}/10)!"
                            
                        st.session_state.last_unboxed_item = {
                            "name": rolled_item,
                            "message": notice_banner
                        }
                        with open(FILE_PATH, 'w', encoding='utf-8') as f: 
                            json.dump(player.to_dict() if hasattr(player, 'to_dict') else player.__dict__, f, default=str, indent=4)
                        st.session_state.shop_emoji_rain_trigger = gear_catalog[rolled_item].get('icon', '👟') if box['id'] != "sb_palette" else "🎨"
                        st.rerun()
                except Exception as e: 
                    st.error(f'Unboxing fault: {str(e)}')


def render_locker_vault(player, FILE_PATH, kit_slots):
    st.markdown('### 📦 My Gear')
    if not player.inventory: 
        st.info('Your equipment chest is empty. Complete trail runs to generate gold balances.')
    else:
        if "locker_vault_cat" not in st.session_state:
            st.session_state.locker_vault_cat = 'Footwear'
            
        categories = ['Footwear', 'Sunglasses', 'Head Gear', 'Singlets', 'Jackets', 'Shorts', 'Pants', 'Watches']
        
        l_cols = st.columns(8)
        for c_idx, cat_name in enumerate(categories):
            with l_cols[c_idx]:
                is_sel = (st.session_state.locker_vault_cat == cat_name)
                icon = ITEM_ICON_MAP.get(cat_name, '🎽')
                if st.button(f"{icon}\n{cat_name}", key=f"btn_locker_filter_{cat_name}", type="primary" if is_sel else "secondary", use_container_width=True):
                    st.session_state.locker_vault_cat = cat_name
                    st.rerun()
                    
        vault_tab_filter = st.session_state.locker_vault_cat
        active_slot_variable = kit_slots[vault_tab_filter]
        currently_equipped_item = getattr(player, active_slot_variable, None)
        category_items = [item for item in player.inventory if item in gear_catalog and gear_catalog[item]['cat'] == vault_tab_filter]
        
        if not category_items: 
            st.info(f"No collected item entries inside {vault_tab_filter} yet.")
        else:
            st.write("")
            for idx, owned_item in enumerate(category_items):
                curr_level = min(10, max(1, int(player.equipped_gear.get(owned_item, 1))))
                base_cost = gear_catalog.get(owned_item, {'cost': 40})['cost']
                gold_balance = getattr(player, 'gold', 0)
                is_maxed = curr_level >= 10
                next_level_cost = int(base_cost * (curr_level + 1) * 0.5 * curr_level)
                is_equipped = (owned_item == currently_equipped_item)
                
                active_style = player.gear_colors.get(owned_item, "Default Issue")
                color_emojis = {
                    "Default Issue": "⚙️", "White": "⚪", "Blue": "🔵", "Red": "🔴", 
                    "Green": "🟢", "Yellow": "🟡", "Silver": "🥈", "Gold": "👑"
                }
                current_emoji = color_emojis.get(active_style, "⚙️")
                
                with st.container(border=True):
                    box_icon = gear_catalog[owned_item].get('icon', '🎽')
                    img_html = render_shop_asset(owned_item, box_icon, size_px=45)
                    st.markdown(f'<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;">{img_html}<div><h5 style="margin:0;">{owned_item}</h5><small style="color: gray;">Utility: {gear_catalog[owned_item].get("weather", "All-Weather")}</small></div></div>', unsafe_allow_html=True)
                    
                    v1, v2 = st.columns(2)
                    with v1:
                        st.markdown(f"`Optimization Status: Rank {curr_level}/10`")
                        st.markdown(f"🎨 Style: {current_emoji} `{active_style.upper()}`")
                        st.progress(float(curr_level / 10.0))
                        
                        if is_equipped: 
                            st.button('🎽 ACTIVE ON KIT', key=f'act_slot_eq_{idx}', disabled=True)
                        else:
                            if st.button('🟢 Equip Gear', key=f'equip_slot_action_{idx}'):
                                try:
                                    setattr(player, active_slot_variable, owned_item)
                                    with open(FILE_PATH, 'w', encoding='utf-8') as f: 
                                        json.dump(player.to_dict() if hasattr(player, 'to_dict') else player.__dict__, f, default=str, indent=4)
                                    st.session_state.shop_toast_message = f"⚡ Successfully equipped {owned_item} to your active kit configuration!"
                                    st.rerun()
                                except Exception: 
                                    pass
                    with v2:
                        available_shades = ["Default Issue", "White", "Blue", "Red", "Green", "Yellow", "Silver", "Gold"]
                        chosen_shade = st.selectbox(
                            "Stage Colorway Option:",
                            options=available_shades,
                            index=available_shades.index(active_style) if active_style in available_shades else 0,
                            key=f"paint_selector_{idx}_{owned_item.replace(' ', '_')}"
                        )
                        
                        if chosen_shade != active_style:
                            if st.button(f"🎨 Apply Colorway (-15g)", key=f"purchase_color_btn_{idx}_{owned_item.replace(' ', '_')}", disabled=(gold_balance < 15)):
                                try:
                                    player.gold = gold_balance - 15
                                    player.gear_colors[owned_item] = chosen_shade
                                    with open(FILE_PATH, 'w', encoding='utf-8') as f: 
                                        json.dump(player.to_dict() if hasattr(player, 'to_dict') else player.__dict__, f, default=str, indent=4)
                                    st.session_state.shop_toast_message = f"🎨 Successfully applied custom colorway: {chosen_shade} over your {owned_item}!"
                                    st.rerun()
                                except Exception: 
                                    pass
                                
                            if gold_balance < 15:
                                st.error("❌ Insufficient gold balance to change style variants.")
                                
                        if is_maxed: 
                            st.button('👑 MAX OPTIMIZATION', key=f'max_slot_rank_{idx}', disabled=True)
                        else:
                            if st.button(f"Optimize (+{next_level_cost}g)", key=f'tune_slot_action_{idx}', disabled=(gold_balance < next_level_cost)):
                                try:
                                    player.gold = gold_balance - next_level_cost
                                    player.equipped_gear[owned_item] = curr_level + 1
                                    with open(FILE_PATH, 'w', encoding='utf-8') as f: 
                                        json.dump(player.to_dict() if hasattr(player, 'to_dict') else player.__dict__, f, default=str, indent=4)
                                    st.session_state.shop_toast_message = f"⚡ Optimized gear to Rank +{curr_level + 1}!"
                                    st.rerun()
                                except Exception as e: 
                                    st.error(f'Optimization fault: {str(e)}')

