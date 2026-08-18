# -*- coding: utf-8 -*-
import streamlit as st
import json
import random
from pantry_config import PANTRY_MENU, TROPHY_TIERS, VAULT_BOX_REGISTRY

def render_pantry_interface(player, FILE_PATH):
    st.markdown('## 🏪 The Master Calorie Pantry Market')
    st.markdown('Spend workout calories to purchase fuel and progress your cooking mastery. Earning a trophy resets your progress count to 0 for that tier!')
    st.markdown('---')

    # =========================================================================
    # 🎰 PERSISTENT TOAST & HIGH-CONTRAST EMOJI RAIN MANAGER
    # =========================================================================
    if "pantry_toast" in st.session_state:
        st.toast(st.session_state.pantry_toast["text"], icon=st.session_state.pantry_toast["icon"])
        del st.session_state.pantry_toast

    if "pantry_highlight" in st.session_state:
        falling_emoji = st.session_state.get("pantry_highlight_emoji", "🎁")
        rain_html = '<div style="position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: 999999; overflow: hidden;">'
        for i in range(25):
            left_pos = random.randint(3, 97)
            delay = random.uniform(0.0, 2.0)
            duration = random.uniform(2.5, 4.5)
            size = random.randint(22, 48)
            rain_html += f'<div style="position: absolute; top: -60px; left: {left_pos}%; font-size: {size}px; animation: pantryRainAnim {duration}s linear {delay}s forwards; pointer-events: none;">{falling_emoji}</div>'
        rain_html += """
        </div>
        <style>
        @keyframes pantryRainAnim {
            0% { transform: translateY(0) rotate(0deg); opacity: 1; }
            85% { opacity: 1; }
            100% { transform: translateY(108vh) rotate(360deg); opacity: 0; }
        }
        </style>
        """
        st.markdown(rain_html, unsafe_allow_html=True)
        st.success(st.session_state.pantry_highlight, icon="✨")
        del st.session_state.pantry_highlight
        if "pantry_highlight_emoji" in st.session_state:
            del st.session_state.pantry_highlight_emoji

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

    with st.container(border=True):
        col_hud_1, col_hud_2 = st.columns(2)
        with col_hud_1:
            st.metric("🏦 Current Calorie Vault Balance", f"{balance} kcal", delta="Available Funds")
        with col_hud_2:
            st.metric("📈 Lifetime Account Accumulation", f"{total_earned} kcal", delta="Total Sweated Equity")
            
    st.markdown('---')

    if "discount_frenzy_cost" not in st.session_state:
        st.session_state.discount_frenzy_cost = 500
    if "pantry_active_tab" not in st.session_state:
        st.session_state.pantry_active_tab = "trophy_cabinet"

    # Synchronize dynamic runtime price state constraints for specialized frenzied boxes
    for box in VAULT_BOX_REGISTRY["strategy"]:
        if box["id"] == "box_frenzy":
            box["cost"] = st.session_state.discount_frenzy_cost

    # =========================================================================
    # ⚖️ STATE-DRIVEN TAB NAVIGATION ROUTER
    # =========================================================================
    nav_col_1, nav_col_2, nav_col_3 = st.columns(3)
    with nav_col_1:
        is_cabinet_selected = st.session_state.pantry_active_tab == "trophy_cabinet"
        if st.button("🏆 Your Trophy Cabinet", key="nav_btn_cabinet", use_container_width=True, type="primary" if is_cabinet_selected else "secondary"):
            st.session_state.pantry_active_tab = "trophy_cabinet"
            st.rerun()
    with nav_col_2:
        is_market_selected = st.session_state.pantry_active_tab == "purchase_market"
        if st.button("🛒 Purchase Market Hub", key="nav_btn_market", use_container_width=True, type="primary" if is_market_selected else "secondary"):
            st.session_state.pantry_active_tab = "purchase_market"
            st.rerun()
    with nav_col_3:
        is_vault_selected = st.session_state.pantry_active_tab == "mystery_vault"
        if st.button("🎁 Mystery Box Vault", key="nav_btn_vault", use_container_width=True, type="primary" if is_vault_selected else "secondary"):
            st.session_state.pantry_active_tab = "mystery_vault"
            st.rerun()

    st.markdown('<br>', unsafe_allow_html=True)

    # Pre-build list layouts for use across configurations
    p_low_display, p_mid_display, p_high_display = [], [], []
    for c_group, c_data in PANTRY_MENU.items():
        for item in c_data["items"]:
            icost = item.get("cost", 0)
            ientry = f"{item['emoji']} {item['name']} ({icost} kcal)"
            if icost <= 250: p_low_display.append(ientry)
            elif 251 <= icost <= 600: p_mid_display.append(ientry)
            else: p_high_display.append(ientry)

    # =========================================================================
    # 🏆 ROUTE PANEL: TROPHY CABINET
    # =========================================================================
    if st.session_state.pantry_active_tab == "trophy_cabinet":
        st.markdown('### 🏆 Unlocked Awards & Achievements')
        
        flag_cols_data = []
        for cuisine_group, cuisine_data in PANTRY_MENU.items():
            for tier_idx in range(5):
                if f"{cuisine_group}:{tier_idx}" in cuisine_trophies:
                    t_meta = TROPHY_TIERS[tier_idx]
                    flag_cols_data.append(f"👑 **{cuisine_data['flag']} {cuisine_group}**\n{t_meta['name']}")
                    
        if flag_cols_data:
            st.markdown("##### 🗺️ Earned Cuisine Category Master Flags")
            num_flag_cols = min(4, len(flag_cols_data))
            flag_cols = st.columns(num_flag_cols)
            for f_idx, flag_text in enumerate(flag_cols_data):
                with flag_cols[f_idx % num_flag_cols]:
                    st.info(flag_text)
            st.markdown("---")
        
        if "active_trophy_tier" not in st.session_state:
            st.session_state.active_trophy_tier = "Summary"
            
        counts = {"Bronze": 0, "Silver": 0, "Gold": 0, "Platinum": 0, "Diamond": 0}
        for array_src in [single_trophies, cuisine_trophies]:
            for t_key in array_src:
                if ":" in t_key:
                    try:
                        t_idx = int(t_key.split(":")[-1])
                        if 0 <= t_idx < 5:
                            t_name = TROPHY_TIERS[t_idx]["name"].split()[0]
                            if t_name in counts: counts[t_name] += 1
                    except ValueError: pass

        st.markdown("###### 📊 Click a medal type below to expand details grouped by cuisine:")
        medal_cols = st.columns(5)
        medals_meta = [("Bronze", "🥉"), ("Silver", "🥈"), ("Gold", "🥇"), ("Platinum", "💿"), ("Diamond", "💎")]
        
        for m_idx, (m_name, m_icon) in enumerate(medals_meta):
            with medal_cols[m_idx]:
                is_active = st.session_state.active_trophy_tier == m_name
                lbl = f"{m_icon} {m_name[:4]}\n【 {counts[m_name]} Max 】" if is_active else f"{m_icon} {m_name[:4]}\n{counts[m_name]} items"
                if st.button(lbl, key=f"btn_click_{m_name.lower()}", use_container_width=True):
                    st.session_state.active_trophy_tier = "Summary" if is_active else m_name
                    st.rerun()

        if st.session_state.active_trophy_tier != "Summary":
            selected_tier = st.session_state.active_trophy_tier
            tier_map = {"Bronze": 0, "Silver": 1, "Gold": 2, "Platinum": 3, "Diamond": 4}
            target_idx = tier_map[selected_tier]
            tier_meta = TROPHY_TIERS[target_idx]
            
            st.markdown(f"#### 🔎 Detailed breakdown for {selected_tier} Medals:")
            valid_cuisine_blocks = []
            for cuisine_group, cuisine_data in PANTRY_MENU.items():
                cuisine_matches = []
                if f"{cuisine_group}:{target_idx}" in cuisine_trophies:
                    cuisine_matches.append(f"👑 **{cuisine_data['flag']} {cuisine_group} Flag Master**")
                for item in cuisine_data["items"]:
                    if f"{item['id']}:{target_idx}" in single_trophies:
                        cuisine_matches.append(f"{item['emoji']} {item['name']} — {tier_meta['name']}")
                if cuisine_matches:
                    valid_cuisine_blocks.append((cuisine_group, cuisine_data, cuisine_matches))
            
            if valid_cuisine_blocks:
                breakdown_cols = st.columns(3)
                for b_idx, (c_group, c_data, c_matches) in enumerate(valid_cuisine_blocks):
                    with breakdown_cols[b_idx % 3]:
                        with st.container(border=True):
                            st.markdown(f"##### {c_data['flag']} {c_group}")
                            for award_string in c_matches: st.write(award_string)
            else:
                st.caption(f"No {selected_tier} medals unlocked yet.")
                
            if st.button("↩️ Collapse Details View", key="pantry_collapse_trophy_view"):
                st.session_state.active_trophy_tier = "Summary"
                st.rerun()

        st.markdown('---')
        with st.expander("📦 View Lifetime Career Inventory Stock Ledger Balance", expanded=False):
            has_purchased_anything = False
            inv_cols = st.columns(4)
            col_selector = 0
            for c_group, c_data in PANTRY_MENU.items():
                for item in c_data["items"]:
                    active_pool = purchase_counts.get(item["id"], 0)
                    previous_unlocked_sums = sum(item["thresholds"][t_idx] for t_idx in range(5) if f"{item['id']}:{t_idx}" in single_trophies)
                    lifetime_total = active_pool + previous_unlocked_sums
                    if lifetime_total > 0:
                        has_purchased_anything = True
                        with inv_cols[col_selector % 4]:
                            st.metric(label=f"{item['emoji']} {item['name']}", value=f"{lifetime_total} units")
                        col_selector += 1
            if not has_purchased_anything: st.caption("Your inventory is currently empty!")

    # =========================================================================
    # 🛒 ROUTE PANEL: PURCHASE MARKET HUB
    # =========================================================================
    elif st.session_state.pantry_active_tab == "purchase_market":
        st.markdown('### 🛒 Browse Market Inventory & Mastery Tracks')
        sort_option = st.selectbox("↕️ Sort items inside categories by:", ["Highest Cost", "Lowest Cost", "Alphabetical Order"], key="pantry_market_sort_selector")
        st.markdown('---')
        
        cuisine_cols = st.columns(3)
        for idx, (cuisine_group, cuisine_data) in enumerate(PANTRY_MENU.items()):
            next_c_tier = 0
            for tier_idx in range(5):
                if f"{cuisine_group}:{tier_idx}" in cuisine_trophies: next_c_tier = tier_idx + 1
                    
            items_completed_count = sum(1 for food in cuisine_data["items"] if f"{food['id']}:{next_c_tier}" in single_trophies)
            total_items_in_sector = len(cuisine_data["items"])
            
            with cuisine_cols[idx % 3]:
                with st.container(border=True):
                    st.markdown(f"### {cuisine_data['flag']} {cuisine_group}")
                    if next_c_tier < 5:
                        tier_meta = TROPHY_TIERS[next_c_tier]
                        st.markdown(f"🎯 **{tier_meta['name']}** ({items_completed_count}/{total_items_in_sector})")
                        u_circle = cuisine_data['flag']
                        earned_html = "".join([f'<span style="filter: drop-shadow(0px 0px 2px #000); margin-right: 2px;">{u_circle}</span>' for _ in range(items_completed_count)])
                        unearned_html = "".join([f'<span style="opacity: 0.12; filter: grayscale(100%); margin-right: 2px;">{u_circle}</span>' for _ in range(total_items_in_sector - items_completed_count)])
                        st.markdown(f"{earned_html}{unearned_html}", unsafe_allow_html=True)
                    else:
                        st.markdown("🏆 **👑 Maximum Sector Mastery!**")
                    st.markdown("---")
                    
                    min_unfinished_tier = min([next(tier_idx for tier_idx in range(6) if tier_idx == 5 or f"{it['id']}:{tier_idx}" not in single_trophies) for it in cuisine_data["items"]])
                        
                    if sort_option == "Highest Cost": sorted_items = sorted(cuisine_data["items"], key=lambda x: x.get("cost", 0), reverse=True)
                    elif sort_option == "Lowest Cost": sorted_items = sorted(cuisine_data["items"], key=lambda x: x.get("cost", 0))
                    else: sorted_items = sorted(cuisine_data["items"], key=lambda x: x.get("name", ""))
                        
                    for food in sorted_items:
                        f_id, name, cost, emoji, thresholds = food["id"], food["name"], food["cost"], food["emoji"], food["thresholds"]
                        owned_count = purchase_counts.get(f_id, 0)
                        current_item_tier = next((t for t in range(5) if f"{f_id}:{t}" not in single_trophies), 5)
                        is_progression_locked = current_item_tier > min_unfinished_tier
                                
                        item_row_col, btn_row_col = st.columns([1.9, 2.1])
                        with item_row_col:
                            st.markdown(f"**{emoji} {name}**\n(`🔥 {cost}` kcal)")
                            if current_item_tier < 5:
                                active_tier_idx = current_item_tier - 1 if (is_progression_locked and current_item_tier > 0) else current_item_tier
                                target_req = thresholds[active_tier_idx]
                                t_meta = TROPHY_TIERS[active_tier_idx]
                                earned_icons = 5 if (is_progression_locked and current_item_tier > 0) else min(5, int(owned_count / (target_req / 5))) if target_req > 0 else 0
                                
                                earned_html = "".join([f'<span style="filter: drop-shadow(0px 0px 2px #000); margin-right: 1px;">{emoji}</span>' for _ in range(earned_icons)])
                                unearned_html = "".join([f'<span style="opacity: 0.12; filter: grayscale(100%); margin-right: 1px;">{emoji}</span>' for _ in range(5 - earned_icons)])
                                cur_stk = target_req if (is_progression_locked and current_item_tier > 0) else owned_count
                                st.markdown(f'<p style="font-size: 11px; color: #808495; margin: 0;">Stk: {cur_stk}/{target_req}<br>{t_meta["name"]}<br>{earned_html}{unearned_html}</p>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<p style="font-size: 11px; color: #808495; margin: 0;">🏆 Maxed Belt<br>{"".join([f"<span>{emoji}</span>" for _ in range(5)])}</p>', unsafe_allow_html=True)
                                
                        with btn_row_col:
                            is_funds_low = balance < cost
                            if is_progression_locked: btn_lbl = "Locked (Level Gate)"
                            elif is_funds_low: btn_lbl = f"Need {cost} kcal"
                            else: btn_lbl = "Buy"
                            
                            if st.button(btn_lbl, key=f"p_buy_{cuisine_group}_{f_id}_{current_item_tier}", disabled=is_funds_low or is_progression_locked, use_container_width=True):
                                player.calorie_bank_balance -= cost
                                st.session_state.pantry_last_bought = (cuisine_group, food)
                                st.session_state.discount_frenzy_cost = 500
                                purchase_counts[f_id] = owned_count + 1
                                player.pantry_purchase_counts = purchase_counts

                                for t_idx in range(5):
                                    if f"{f_id}:{t_idx}" not in single_trophies and purchase_counts[f_id] >= thresholds[t_idx]:
                                        single_trophies.append(f"{f_id}:{t_idx}")
                                        player.pantry_single_trophies = single_trophies
                                        st.session_state.pantry_toast = {"text": f"🏆 LEVEL UP: Unlocked {emoji} {name} {TROPHY_TIERS[t_idx]['name']}!", "icon": "🔥"}
                                        purchase_counts[f_id] = 0
                                        break
                                for t_idx in range(5):
                                    if f"{cuisine_group}:{t_idx}" not in cuisine_trophies and all(f"{it['id']}:{t_idx}" in single_trophies for it in cuisine_data["items"]):
                                        cuisine_trophies.append(f"{cuisine_group}:{t_idx}")
                                        player.pantry_cuisine_trophies = cuisine_trophies
                                        st.session_state.pantry_toast = {"text": f"🎉 SECTOR COMPLETE: Unlocked {cuisine_data['flag']} {cuisine_group} Flag!", "icon": "👑"}
                                        for it in cuisine_data["items"]: purchase_counts[it["id"]] = 0
                                        break
                                with open(FILE_PATH, 'w', encoding='utf-8') as f: json.dump(player.to_dict() if hasattr(player, 'to_dict') else player.__dict__, f, default=str, indent=4)
                                if "pantry_toast" not in st.session_state: st.session_state.pantry_toast = {"text": f"🎉 Purchased {name}!", "icon": "✅"}
                                st.rerun()
                        st.markdown('<div style="margin-bottom: 8px; border-bottom: 1px solid #1f232a; opacity: 0.15;"></div>', unsafe_allow_html=True)

    # =========================================================================
    # 🎁 ROUTE PANEL: DYNAMIC REFACTORED MYSTERY BOX VAULT
    # =========================================================================
    elif st.session_state.pantry_active_tab == "mystery_vault":
        st.markdown('### 🎁 The High-Volume Mystery Box Vault')
        st.markdown('Gamble your hard-sweated workout balance across data-driven dynamic prize configurations.')
        
        pool_clean_display, pool_cheat_display = [], []
        for cg, cd in PANTRY_MENU.items():
            for it in cd["items"]:
                icost = it.get("cost", 0)
                ientry = f"{it['emoji']} {it['name']} ({icost} kcal)"
                name_l = it["name"].lower()
                if "shake" in name_l or "bar" in name_l or "salad" in name_l or "fuel" in name_l or icost <= 200:
                    pool_clean_display.append(ientry)
                else:
                    pool_cheat_display.append(ientry)

        def execute_box_award(c_g, c_d, c_it, points=1):
            f_id, name, emoji, val = c_it["id"], c_it["name"], c_it["emoji"], c_it.get("cost", 0)
            purchase_counts[f_id] = purchase_counts.get(f_id, 0) + points
            player.pantry_purchase_counts = purchase_counts
            for t_idx in range(5):
                if f"{f_id}:{t_idx}" not in single_trophies and purchase_counts[f_id] >= c_it["thresholds"][t_idx]:
                    single_trophies.append(f"{f_id}:{t_idx}")
                    purchase_counts[f_id] = 0
                    break
            for t_idx in range(5):
                if f"{c_g}:{t_idx}" not in cuisine_trophies and all(f"{it['id']}:{t_idx}" in single_trophies for it in c_d["items"]):
                    cuisine_trophies.append(f"{c_g}:{t_idx}")
                    for it in c_d["items"]: purchase_counts[it["id"]] = 0
                    break
            with open(FILE_PATH, 'w', encoding='utf-8') as f: json.dump(player.to_dict() if hasattr(player, 'to_dict') else player.__dict__, f, default=str, indent=4)
            return emoji, name, val

        sections_meta = [
            ("💎 Core Cost-Anchored Chests", "core"), 
            ("🚀 Specialty & Gated Clusters", "specialty"), 
            ("🎲 Chaos & Volatility Hubs", "chaos"), 
            ("📈 Strategy & Dynamic Modifiers", "strategy")
        ]
        
        for section_title, registry_key in sections_meta:
            st.markdown(f"#### {section_title}")
            row_cols = st.columns(4)
            
            for b_idx, b_conf in enumerate(VAULT_BOX_REGISTRY[registry_key]):
                with row_cols[b_idx]:
                    with st.container(border=True):
                        st.markdown(f"### {b_conf['icon']} {b_conf['name'].replace('### ', '')}")
                        st.markdown(f"`🔥 {b_conf['cost']}` kcal")
                        st.caption(b_conf["desc"])
                        
                        t_theme = None
                        if b_conf["type"] == "theme":
                            t_theme = st.selectbox("Family:", list(PANTRY_MENU.keys()), key=f"v_theme_sel_{b_conf['id']}")
                        
                        with st.expander("📊 View Odds & Loot Profiles", expanded=False):
                            st.text(b_conf["odds"])
                            st.markdown("---")
                            if b_conf["type"] == "core" and "Bronze" in b_conf["name"]: st.markdown(f"**Loot Pool:** {', '.join(p_low_display)}")
                            elif b_conf["type"] == "clean": st.markdown(f"**Loot Pool:** {', '.join(pool_clean_display)}")
                            elif b_conf["type"] == "cheat": st.markdown(f"**Loot Pool:** {', '.join(pool_cheat_display)}")
                            else: st.markdown(f"**Low:** {len(p_low_display)} items | **Mid:** {len(p_mid_display)} items | **High:** {len(p_high_display)} items")

                        is_gated = (b_conf["type"] == "grandmaster" and len(single_trophies) < 3)
                        final_cost = b_conf["cost"]
                        is_disabled = balance < final_cost or is_gated or (b_conf["type"] == "underdog" and not [it for cg, cd in PANTRY_MENU.items() for it in cd["items"] if purchase_counts.get(it["id"],0) == min([purchase_counts.get(x["id"],0) for c, d in PANTRY_MENU.items() for x in d["items"]])])
                        
                        btn_lbl = "Locked" if is_gated else "Open Box"
                        if st.button(btn_lbl, key=f"v_btn_{b_conf['id']}", disabled=is_disabled, use_container_width=True):
                            player.calorie_bank_balance -= final_cost
                            
                            if b_conf["type"] == "frenzy": st.session_state.discount_frenzy_cost = max(200, final_cost - 75)
                            else: st.session_state.discount_frenzy_cost = 500
                            
                            pool_low, pool_mid, pool_high, all_flat = [], [], [], []
                            for cg, cd in PANTRY_MENU.items():
                                for it in cd["items"]:
                                    ip = (cg, cd, it)
                                    all_flat.append(ip)
                                    if it.get("cost", 0) <= 250: pool_low.append(ip)
                                    elif 251 <= it.get("cost", 0) <= 600: pool_mid.append(ip)
                                    else: pool_high.append(ip)
                                    
                            roll = random.random() * 100
                            chosen_pool = all_flat
                            
                            if b_conf["type"] == "core":
                                if "Bronze" in b_conf["name"]: chosen_pool = pool_low
                                elif "Silver" in b_conf["name"]: chosen_pool = pool_mid if roll < 10.0 and pool_mid else pool_low
                                elif "Gold" in b_conf["name"]: chosen_pool = pool_high if roll < 10.0 and pool_high else pool_mid if roll < 40.0 and pool_mid else pool_low
                                elif "Platinum" in b_conf["name"] and roll < 2.0:
                                    eligible = [(g, d, t) for g, d in PANTRY_MENU.items() for t in range(5) if f"{g}:{t}" not in cuisine_trophies]
                                    if eligible:
                                        cg, cd, ct = random.choice(eligible)
                                        cuisine_trophies.append(f"{cg}:{ct}")
                                        for it in cd["items"]: purchase_counts[it["id"]] = 0
                                        with open(FILE_PATH, 'w', encoding='utf-8') as f: json.dump(player.to_dict() if hasattr(player, 'to_dict') else player.__dict__, f, default=str, indent=4)
                                        st.session_state.pantry_highlight_emoji, st.session_state.pantry_highlight = cd["flag"], f"✨ 🏆 **COVETED TROPHY DIRECT UNLOCK!** 🏆 ✨ Instantly awarded the {cd['flag']} **{cg} {TROPHY_TIERS[ct]['name']} Flag**!"
                                        st.rerun()
                                    else: chosen_pool = pool_high
                                    
                            elif b_conf["type"] == "theme" and t_theme: chosen_pool = [(t_theme, PANTRY_MENU[t_theme], x) for x in PANTRY_MENU[t_theme]["items"]]
                            elif b_conf["type"] == "grandmaster": chosen_pool = pool_high if roll < 25.0 and pool_high else pool_mid
                            elif b_conf["type"] == "daily": chosen_pool = [sorted(all_flat, key=lambda x: x[2].get("cost",0), reverse=True)[0]] if roll < 50.0 else all_flat
                            elif b_conf["type"] == "underdog":
                                m_score = min([purchase_counts.get(x["id"],0) for c, d in PANTRY_MENU.items() for x in d["items"]])
                                chosen_pool = [(c, d, x) for c, d in PANTRY_MENU.items() for x in d["items"] if purchase_counts.get(x["id"],0) == m_score]
                            elif b_conf["type"] == "clean": chosen_pool = [(c, d, x) for c, d in all_flat if "shake" in x["name"].lower() or "bar" in x["name"].lower() or "salad" in x["name"].lower() or x.get("cost",0) <= 200]
                            elif b_conf["type"] == "cheat": chosen_pool = [(c, d, x) for c, d in all_flat if not ("shake" in x["name"].lower() or "bar" in x["name"].lower() or "salad" in x["name"].lower() or x.get("cost",0) <= 200)]
                            elif b_conf["type"] == "bogo" and last_bought_cache and roll < 70.0: chosen_pool = [(last_bought_cache[0], last_bought_cache[1], last_bought_cache[1])]
                            elif b_conf["type"] == "spoon": chosen_pool = [(c, d, x) for c, d in all_flat if next((t for t in range(5) if f"{x['id']}:{t}" not in single_trophies), 5) >= 2]
                            
                            if b_conf["type"] == "roulette":
                                if roll < 90.0:
                                    active = [x for c, d in PANTRY_MENU.items() for x in d["items"] if purchase_counts.get(x["id"],0) > 0]
                                    if active:
                                        lit = random.choice(active)
                                        purchase_counts[lit["id"]] -= 1
                                        st.session_state.pantry_highlight_emoji, st.session_state.pantry_highlight = lit["emoji"], f"💥 **KITCHEN FIRE ACCIDENT!** 💥 Roulette backfired! Lost 1 progress point from your active {lit['emoji']} **{lit['name']}** track!"
                                    else: st.session_state.pantry_highlight = "💨 **ROULETTE DRAW:** Fire sparked but active slots were completely empty! No points lost."
                                    with open(FILE_PATH, 'w', encoding='utf-8') as f: json.dump(player.to_dict() if hasattr(player, 'to_dict') else player.__dict__, f, default=str, indent=4)
                                else:
                                    winners = random.sample(all_flat, min(3, len(all_flat)))
                                    wns = []
                                    for wc, wd, wi in winners:
                                        purchase_counts[wi["id"]] = purchase_counts.get(wi["id"], 0) + 1
                                        wns.append(f"{wi['emoji']} {wi['name']} (Value: {wi.get('cost',0)} kcal)")
                                    st.session_state.pantry_highlight_emoji, st.session_state.pantry_highlight = "🌶️", f"🌶️ **JACKPOT! CASCADING CASCADE WIN!** 🌶️ Conquered 10% odds! +1 progress granted simultaneously to:\n\n{', '.join(wns)}!"
                                st.rerun()
                                
                            elif b_conf["type"] == "double":
                                if roll < 50.0:
                                    st.session_state.pantry_highlight_emoji, st.session_state.pantry_highlight = "🗑️", "💥 **BURNT MEAL OVERCOOKED!** Double or Nothing failed. 800 kcal vanished in smoke."
                                    with open(FILE_PATH, 'w', encoding='utf-8') as f: json.dump(player.to_dict() if hasattr(player, 'to_dict') else player.__dict__, f, default=str, indent=4)
                                else:
                                    chosen_g, chosen_cd, chosen_it = random.choice([x for x in all_flat if x[2].get("cost",0) > 250] or all_flat)
                                    emoji, name, val = execute_box_award(chosen_g, chosen_cd, chosen_it, points=3)
                                    st.session_state.pantry_highlight_emoji, st.session_state.pantry_highlight = emoji, f"🎰 **DOUBLE OR NOTHING VICTORY!** 🎲 Instant **+3 Progress Jump** awarded to {emoji} **{name}** (Value: {val} kcal)!"
                                st.rerun()
                                
                            elif b_conf["type"] == "fridge":
                                active_fridge = [(c, d, x, purchase_counts[x["id"]]) for c, d in PANTRY_MENU.items() for x in d["items"] if purchase_counts.get(x["id"],0) > 0]
                                sac = random.choice(active_fridge)
                                for it in sac[1]["items"]: purchase_counts[it["id"]] = 0
                                boosted = random.choice(sac[1]["items"])
                                emoji, name, val = execute_box_award(sac[0], sac[1], boosted, points=3)
                                st.session_state.pantry_highlight_emoji, st.session_state.pantry_highlight = emoji, f"🧹 **FRIDGE SWEEP COMPLETE!** Sacrificed category progress fragments to deliver an instant **+3 Boost** to {emoji} **{name}**!"
                                st.rerun()

                            if not chosen_pool: chosen_pool = all_flat
                            chosen_g, chosen_cd, chosen_it = random.choice(chosen_pool)
                            emoji, name, val = execute_box_award(chosen_g, chosen_cd, chosen_it, points=1)
                            st.session_state.pantry_highlight_emoji, st.session_state.pantry_highlight = emoji, f"📦 **UNBOXING COMPLETE:** Opened {b_conf['name']}! Received progress point for: {emoji} **{name}** valued at `🔥 {val}` kcal!"
                            st.rerun()
            st.markdown('<br>', unsafe_allow_html=True)

