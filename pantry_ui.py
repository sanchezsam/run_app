# -*- coding: utf-8 -*-
import streamlit as st
import json
from pantry_config import PANTRY_MENU, TROPHY_TIERS

def render_pantry_interface(player, FILE_PATH):
    st.markdown('## 🏪 The Master Calorie Pantry Market')
    st.markdown('Spend workout calories to purchase fuel and progress your cooking mastery. Earning a trophy resets your progress count to 0 for that tier!')
    st.markdown('---')

    # =========================================================================
    # 🛡️ ENGINE INITIALIZATION LAYER: SCHEMA INTEGRITY CHECKERS
    # =========================================================================
    if not hasattr(player, 'pantry_purchase_counts') or getattr(player, 'pantry_purchase_counts') is None:
        player.pantry_purchase_counts = {}
    if not hasattr(player, 'pantry_single_trophies') or getattr(player, 'pantry_single_trophies') is None:
        player.pantry_single_trophies = []
    if not hasattr(player, 'pantry_cuisine_trophies') or getattr(player, 'pantry_cuisine_trophies') is None:
        player.pantry_cuisine_trophies = []

    purchase_counts = getattr(player, 'pantry_purchase_counts')
    single_trophies = getattr(player, 'pantry_single_trophies')
    cuisine_trophies = getattr(player, 'pantry_cuisine_trophies')

    balance = getattr(player, 'calorie_bank_balance', 0)
    total_earned = getattr(player, 'calorie_bank_total_earned', 0)

    # Core Hub Balance Ledger HUD Summary Panel Display
    with st.container(border=True):
        col_hud_1, col_hud_2 = st.columns(2)
        with col_hud_1:
            st.metric("🏦 Current Calorie Vault Balance", f"{balance} kcal", delta="Available Funds")
        with col_hud_2:
            st.metric("📈 Lifetime Account Accumulation", f"{total_earned} kcal", delta="Total Sweated Equity")
    # =========================================================================
    # 🏆 DISPLAY CABINET: RENDER COMPLETE LOCALIZED FOOD TROPHIES & STOCK
    # =========================================================================
    st.markdown('### 🏆 Your Food Trophy & Inventory Cabinet')
    tab_single, tab_cuisine, tab_inventory = st.tabs([
        "🍖 Single Item Masteries", 
        "🥞 Cuisine & Confectionery Flags",
        "📦 Lifetime Inventory Stock"
    ])
    
    with tab_single:
        item_trophy_list = []
        for c_group, c_data in PANTRY_MENU.items():
            for item in c_data["items"]:
                highest_tier = -1
                for tier_idx in range(5):
                    if f"{item['id']}:{tier_idx}" in single_trophies:
                        highest_tier = tier_idx
                
                if highest_tier >= 0:
                    tier_meta = TROPHY_TIERS[highest_tier]
                    display_title = f"{item['emoji']} {item['name']} {tier_meta['name']} Lvl {tier_meta['level']} {tier_meta['suffix']}"
                    item_trophy_list.append(display_title)
        
        if item_trophy_list:
            cols = st.columns(min(3, len(item_trophy_list)))
            for idx, trophy_label in enumerate(item_trophy_list):
                with cols[idx % 3]:
                    st.success(trophy_label)
        else:
            st.caption("No single item mastery awards unlocked yet. Start shopping to claim your first trophy!")

    with tab_cuisine:
        unlocked_sectors_list = []
        for c_group, c_data in PANTRY_MENU.items():
            highest_c_tier = -1
            for tier_idx in range(5):
                if f"{c_group}:{tier_idx}" in cuisine_trophies:
                    highest_c_tier = tier_idx
            if highest_c_tier >= 0:
                tier_meta = TROPHY_TIERS[highest_c_tier]
                unlocked_sectors_list.append(f"{c_data['flag']} {c_group} Collection {tier_meta['name']} {tier_meta['suffix']}")
                
        if unlocked_sectors_list:
            cols = st.columns(min(3, len(unlocked_sectors_list)))
            for idx, c_label in enumerate(unlocked_sectors_list):
                with cols[idx % 3]:
                    st.info(c_label)
        else:
            st.caption("No sector collection flags unlocked yet. Buy evenly across a cuisine menu to unlock its flag!")
    with tab_inventory:
        st.markdown("##### 🧾 Total Career Items Unlocked & Consumed")
        has_purchased_anything = False
        
        # Grid arrangement for displaying total career inventory balances
        inv_cols = st.columns(4)
        col_selector = 0
        
        for c_group, c_data in PANTRY_MENU.items():
            for item in c_data["items"]:
                # Calculate career lifetime stock sum = current active pool + requirements of unlocked ranks
                active_pool = purchase_counts.get(item["id"], 0)
                previous_unlocked_sums = sum(
                    item["thresholds"][t_idx] 
                    for t_idx in range(5) 
                    if f"{item['id']}:{t_idx}" in single_trophies
                )
                lifetime_total = active_pool + previous_unlocked_sums
                
                if lifetime_total > 0:
                    has_purchased_anything = True
                    with inv_cols[col_selector % 4]:
                        st.metric(
                            label=f"{item['emoji']} {item['name']}", 
                            value=f"{lifetime_total} units",
                            delta="Total Stocked",
                            delta_color="normal"
                        )
                    col_selector += 1
                    
        if not has_purchased_anything:
            st.caption("Your inventory is currently empty! Exchange your workout calories below to populate your lifetime pantry.")

    st.markdown('---')
    st.markdown('### 🛒 Browse Market Inventory & Mastery Tracks')
    # =========================================================================
    # 🛒 MAIN INVENTORY DISPLAY & INTERACTIVE TRANSACTION PROCESSING
    # =========================================================================
    for cuisine_group, cuisine_data in PANTRY_MENU.items():
        st.markdown(f"#### {cuisine_data['flag']} {cuisine_group}")
        
        # Determine the next locked cuisine/dessert collection target flag threshold
        next_c_tier = 0
        for tier_idx in range(5):
            if f"{cuisine_group}:{tier_idx}" in cuisine_trophies:
                next_c_tier = tier_idx + 1
                
        if next_c_tier < 5:
            # 🏁 Sector flag progress math: evaluate progress against resetting values
            items_completed_count = 0
            total_items_in_sector = len(cuisine_data["items"])
            
            status_details = []
            for food in cuisine_data["items"]:
                owned = purchase_counts.get(food["id"], 0)
                req = food["thresholds"][next_c_tier]
                if owned >= req:
                    items_completed_count += 1
                status_details.append(f"{food['emoji']}: {owned}/{req}")
                
            c_progress = min(1.0, items_completed_count / total_items_in_sector)
            st.caption(f"🏁 **Collection Track:** Progress towards **{TROPHY_TIERS[next_c_tier]['name']}** by hitting current tier goals.")
            st.progress(c_progress, text=f"Variety Progress: {items_completed_count} / {total_items_in_sector} items qualified at current tier target levels.")
            st.caption(f"📊 *Current Tier Goals: {', '.join(status_details)}*")
        else:
            st.caption(f"👑 **Maximum Sector Mastery Achieved!** You possess the full Collection Belt for this menu.")
        # Render rows for item elements inside the category
        for food in cuisine_data["items"]:
            f_id = food["id"]
            name = food["name"]
            portion = food["portion"]
            cost = food["cost"]
            emoji = food["emoji"]
            thresholds = food["thresholds"]

            # Pull current level-specific reset progress count
            owned_count = purchase_counts.get(f_id, 0)

            # Detect the active target tier index of this item
            current_item_tier = 0
            for tier_idx in range(5):
                if f"{f_id}:{tier_idx}" in single_trophies:
                    current_item_tier = tier_idx + 1
            
            with st.container(border=True):
                item_col, cost_col, tracking_col, action_col = st.columns()
                
                with item_col:
                    st.markdown(f"**{emoji} {name}**")
                    st.caption(f"Serving size: {portion}")
                
                with cost_col:
                    st.markdown(f"`🔥 {cost} kcal`")
                
                with tracking_col:
                    st.markdown(f"📦 Progress Toward Next Tier: **{owned_count}**")
                    
                    if current_item_tier < 5:
                        target_requirement = thresholds[current_item_tier]
                        tier_meta = TROPHY_TIERS[current_item_tier]
                        
                        st.markdown(f"🎯 *Target: **{tier_meta['name']} Lvl {tier_meta['level']}** ({target_requirement} required)*")
                        
                        progress_ratio = min(1.0, owned_count / target_requirement)
                        st.progress(progress_ratio)
                        
                        # Generate the active visual icon representation track string
                        unlocked_icon = emoji
                        locked_icon = "⚪"
                        
                        display_icons_count = 5
                        milestone_step = target_requirement / display_icons_count
                        earned_icons = min(display_icons_count, int(owned_count / milestone_step)) if milestone_step > 0 else 0
                        remaining_icons = display_icons_count - earned_icons
                        
                        icon_track_str = (unlocked_icon * earned_icons) + (locked_icon * remaining_icons)
                        st.markdown(f"{icon_track_str} `[{owned_count}/{target_requirement}]`")
                    else:
                        st.markdown(f"🏆 **Maximum Mastery Level Reached: {emoji} Belt Holder!**")
                with action_col:
                    is_locked = balance < cost
                    button_label = "🔒 Locked" if is_locked else "🛒 Buy"
                    
                    if st.button(button_label, key=f"pantry_buy_{f_id}", disabled=is_locked):
                        player.calorie_bank_balance -= cost
                        
                        # Increment active progress toward the current unlock goal
                        purchase_counts[f_id] = owned_count + 1
                        player.pantry_purchase_counts = purchase_counts

                        # Evaluate individual food item unlock parameters sequentially using distinct bounds
                        for tier_idx in range(5):
                            trophy_key = f"{f_id}:{tier_idx}"
                            if trophy_key not in single_trophies:
                                if tier_idx == 0 or f"{f_id}:{tier_idx-1}" in single_trophies:
                                    if purchase_counts[f_id] >= thresholds[tier_idx]:
                                        single_trophies.append(trophy_key)
                                        player.pantry_single_trophies = single_trophies
                                        t_meta = TROPHY_TIERS[tier_idx]
                                        st.toast(f"🏆 MASTERY LEVEL UP: Unlocked the {emoji} {name} {t_meta['name']} Lvl {t_meta['level']} {t_meta['suffix']}!", icon="🔥")
                                        
                                        # 💥 CRITICAL RESET DOCK: Set back to 0 to begin acquiring the next tier!
                                        purchase_counts[f_id] = 0
                                        player.pantry_purchase_counts = purchase_counts
                                        break # Terminate loops immediately upon rank up to preserve the 0 state

                        # Evaluate dynamic variety sector flag completions
                        for tier_idx in range(5):
                            c_trophy_key = f"{cuisine_group}:{tier_idx}"
                            if c_trophy_key not in cuisine_trophies:
                                if tier_idx == 0 or f"{cuisine_group}:{tier_idx-1}" in cuisine_trophies:
                                    
                                    # Verify if all items within the active cuisine meet their independent thresholds
                                    sector_qualified = all(
                                        purchase_counts.get(it["id"], 0) >= it["thresholds"][tier_idx] 
                                        for it in cuisine_data["items"]
                                    )
                                    
                                    if sector_qualified:
                                        cuisine_trophies.append(c_trophy_key)
                                        player.pantry_cuisine_trophies = cuisine_trophies
                                        t_meta = TROPHY_TIERS[tier_idx]
                                        st.toast(f"🎉 SECTOR COMPLETED: Unlocked the {cuisine_data['flag']} {cuisine_group} {t_meta['name']} {t_meta['suffix']}!", icon="👑")
                                        
                                        # 💥 FLAG RESET TRACKER: Zero out active metrics for all items in this sector
                                        for it in cuisine_data["items"]:
                                            purchase_counts[it["id"]] = 0
                                        player.pantry_purchase_counts = purchase_counts
                                        break

                        # Write updated models safely back down to disk JSON
                        save_data = player.to_dict() if hasattr(player, 'to_dict') else player.__dict__
                        with open(FILE_PATH, 'w', encoding='utf-8') as db_file:
                            json.dump(save_data, db_file, default=str, indent=4)
                        
                        st.toast(f"🎉 Successfully purchased {emoji} {name}!", icon="✅")
                        st.rerun()
        st.markdown('---')

