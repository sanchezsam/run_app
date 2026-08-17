# -*- coding: utf-8 -*-
# PART 1 OF 3: PRO SHOP SETUP, ATTRIBUTE NODE FORGE & 6-CATEGORY INTEGRATION
import streamlit as st
from run_utils import save_player_profile

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
        'Shorts': 'equipped_shorts_name',
        'Watches': 'equipped_watch_name'
    }
    
    color_emojis = {
        "Basic Factory": "⚙️", "Factory": "⚙️", "White": "⚪", "Blue": "🔵", "Red": "🔴", 
        "Green": "🟢", "Yellow": "🟡", "Silver": "🥈", "Gold": "👑"
    }
    
    # Render horizontal single-slot cockpit inspection loadout layout
    kc1, kc2, kc3, kc4, kc5, kc6 = st.columns(6)
    cols_list = [kc1, kc2, kc3, kc4, kc5, kc6]
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
                    st.success(f"🎽 **{active_item}**")
                    st.markdown(f"`Rank +{item_rank}`\nVariant: {paint_emoji} `{item_paint.upper()}`")
                else:
                    st.info("ℹ️ Slot Empty")
                    st.caption("Equip a module from your Locker Vault below.")
                    
    st.markdown('---')
    
    # Re-engineered 6-slot master catalog matrices
    gear_catalog = {
        # --- FOOTWEAR ---
        'Nike Vaporfly 4%': {'cost': 120, 'cat': 'Footwear', 'desc': 'Carbon-plated shoe. Massive Sprint Velocity physics bonus.'},
        'adidas UltraBoost': {'cost': 95, 'cat': 'Footwear', 'desc': 'Premium cushioning foam. Absorbs high track mileage.'},
        'Hoka One One Speedgoat': {'cost': 110, 'cat': 'Footwear', 'desc': 'Maximalist trail tread. Best for mountain torque.'},
        'Saucony Endorphin Elite': {'cost': 130, 'cat': 'Footwear', 'desc': 'Aggressive rocker geometry. Injects consistent tempo pace splits.'},
        'Brooks Ghost Speed': {'cost': 85, 'cat': 'Footwear', 'desc': 'Ultra-reliable daily workload workhorse. Excellent fatigue dampening.'},
        'New Balance FuelCell Rebel': {'cost': 105, 'cat': 'Footwear', 'desc': 'Explosive high-rebound compound foam. Boosts rapid cadence changes.'},
        'Puma Fast-R Nitro Elite': {'cost': 140, 'cat': 'Footwear', 'desc': 'Decoupled carbon plate chassis. Cutting-edge drag reduction metrics.'},
        'ASICS Metaspeed Sky+': {'cost': 145, 'cat': 'Footwear', 'desc': 'Elongated stride efficiency. Elite scaling for high-velocity drivers.'},
        
        # --- SUNGLASSES ---
        'Oakley Speed Jacket Sunglasses': {'cost': 45, 'cat': 'Sunglasses', 'desc': 'Aerodynamic shatterproof frames. Maximizes tracking accuracy.'},
        '100% Speedcraft Shaded Shields': {'cost': 55, 'cat': 'Sunglasses', 'desc': 'Expanded peripheral vision. High-impact arcade neon visibility lenses.'},
        'Goodr No Bounce Optics': {'cost': 20, 'cat': 'Sunglasses', 'desc': 'Lightweight textured frame grip. Eliminates slipping during sprint cadence loops.'},
        'Smith Vert Performance Shades': {'cost': 65, 'cat': 'Sunglasses', 'desc': 'Chameleon color-adjusting lenses adapting smoothly to canyon trail glare.'},
        
        # --- HEAD GEAR ---
        'Arcade Neon Headband': {'cost': 20, 'cat': 'Head Gear', 'desc': 'Retro sweat protection. Adds style and focus multipliers.'},
        'Ciele Athletics GOCap': {'cost': 25, 'cat': 'Head Gear', 'desc': 'Lightweight collapsible mesh race cap. Deflects extreme canyon sun glare.'},
        'Compressport Visor Engine': {'cost': 18, 'cat': 'Head Gear', 'desc': 'Ultra-minimal ventilated tracking peak. Maximizes cockpit cooling layers.'},
        'Buff Merino Thermal Wrap': {'cost': 22, 'cat': 'Head Gear', 'desc': 'Insulates head and neck vitals. Solid for high altitude winter stages.'},
        
        # --- SINGLETS ---
        'Elite Aero-Grid Singlet': {'cost': 40, 'cat': 'Singlets', 'desc': 'Weightless track singlet. Decreases wind drag factors.'},
        'Championship Crimson Jersey': {'cost': 50, 'cat': 'Singlets', 'desc': 'Vibrant racing jersey boosting team prestige indices.'},
        'Tracksmith Van Cortlandt Singlet': {'cost': 65, 'cat': 'Singlets', 'desc': 'Luxury mesh fabric layout with iconic racing sash. Elite comfort lines.'},
        'Nike Dri-FIT ADV Aeroswift': {'cost': 70, 'cat': 'Singlets', 'desc': 'Engineered precision breathability zones. Minimizes heat build-up blockades.'},
        'Under Armour Iso-Chill Mesh': {'cost': 30, 'cat': 'Singlets', 'desc': 'Flat titanium fibers pull skin heat away, boosting torque stability.'},
        'adidas Adizero Race Vest': {'cost': 45, 'cat': 'Singlets', 'desc': 'Barely-there ultraweight microfiber layout tailored for speedways.'},
        'New Balance RC Short Sleeve': {'cost': 38, 'cat': 'Singlets', 'desc': 'Premium anti-chafing welded seams. Solid for deep high-mileage volume.'},
        'Gore-Tex Windstopper Shell': {'cost': 85, 'cat': 'Singlets', 'desc': 'Hardcore weather shield. Insulates core vitals across alpine storms.'},
        
        # --- SHORTS ---
        'Split Training Track Shorts': {'cost': 35, 'cat': 'Shorts', 'desc': 'Classic maximum range of motion splits. Improves cadence loops.'},
        'Compression Racing Tights': {'cost': 55, 'cat': 'Shorts', 'desc': 'Streamlined thermal tights optimizing lower body blood flow.'},
        'Patagonia Strider Pro Shorts': {'cost': 60, 'cat': 'Shorts', 'desc': '5-pocket system carrying emergency power fuel arrays effortlessly.'},
        'Brooks Sherpa 2-in-1 Chassis': {'cost': 42, 'cat': 'Shorts', 'desc': 'Chafing-free inner brief liner. Maximum baseline support limits.'},
        'ASICS Actibreeze Track Tight': {'cost': 48, 'cat': 'Shorts', 'desc': 'High-ventilation elastic wrap keeping muscle matrices oxygenated.'},
        'Lululemon Surge Pace Split': {'cost': 52, 'cat': 'Shorts', 'desc': 'Premium lightweight stretch fabric. Moves fluidly with high strides.'},
        'Salomon S/Lab Ultra Skirt-Short': {'cost': 95, 'cat': 'Shorts', 'desc': 'Elite long-range trail armor. Specialized for rugged canyon operations.'},
        'Nike Trail Brief split 2"': {'cost': 38, 'cat': 'Shorts', 'desc': 'Hyper-minimal track splits designed to maximize raw sprint cadence.'},
        
        # --- WATCHES ---
        'Garmin Forerunner Pro': {'cost': 85, 'cat': 'Watches', 'desc': 'Surgical track splitting. Smooths out raw pacing lines.'},
        'Coros Pace Performance Matrix': {'cost': 70, 'cat': 'Watches', 'desc': 'Weightless satellite capture engine. Elite driver telemetry sync.'},
        'Apple Watch Ultra Matrix': {'cost': 160, 'cat': 'Watches', 'desc': 'Titanium diving cockpit hull. Dual-frequency precision tracking.'},
        'Polar Vanguard Heart Hub': {'cost': 115, 'cat': 'Watches', 'desc': 'Electrocardiogram telemetry tracking. Smooths out fatigue recovery curves.'},
        'Suunto Vertical Solar Array': {'cost': 140, 'cat': 'Watches', 'desc': 'Solar harvest lens extends battery indefinitely on wilderness loops.'},
        'Vintage Casio Chrono-Shock': {'cost': 20, 'cat': 'Watches', 'desc': 'Vintage basic 1/100s stopwatch. Old-school tactical aesthetics.'},
        'Garmin Fenix Enduro Hull': {'cost': 180, 'cat': 'Watches', 'desc': 'Indestructible sapphire tracking lens. Absolute peak luxury watch.'},
        'Coros Vertix Mountain Engine': {'cost': 150, 'cat': 'Watches', 'desc': 'Barometric altitude calculator. Injects major bonus to climbing analytics.'}
    }
    
    # --- ATTRIBUTE Node ALLOCATION FORGE ---
    st.markdown('### 🏋️ Attribute Node Allocation Forge')
    sac1, sac2 = st.columns(2)
    with sac1:
        if st.button('Upgrade Base Velocity Nodes (+1 Running Token)', disabled=(getattr(player, 'stat_points', 0) < 1)):
            try:
                player.stat_points = getattr(player, 'stat_points', 0) - 1
                player.running_level = getattr(player, 'running_level', 1) + 1
                player.vo2_max = getattr(player, 'vo2_max', 40.0) + 0.5
                save_player_profile(player, FILE_PATH)
                st.success('✨ Attribute Node forged successfully!'); st.rerun()
            except Exception as e: st.error(f'Forge fault: {str(e)}')
    with sac2: st.caption(f"Current Forged Skill: Level **{getattr(player, 'running_level', 1)}** | VO2 Max Base: **{getattr(player, 'vo2_max', 40.0):.1f}**")
    st.markdown('---')
# PART 2 OF 3: STOREFRONT PROCUREMENT LOGIC AND CATALOG FILTER GENERATORS
    col_sale, col_vault = st.columns(2)
    
    with col_sale:
        st.markdown('### 🛍️ Equipment Catalog Storefront')
        cat_filter = st.selectbox('Filter Catalog Section:', ['Footwear', 'Sunglasses', 'Head Gear', 'Singlets', 'Shorts', 'Watches'])
        
        for item, specs in gear_catalog.items():
            if specs['cat'] != cat_filter: continue
            is_owned = item in player.inventory
            
            with st.container(border=True):
                st.markdown(f"📦 **{item}** | `Section: {specs['cat']}`")
                st.caption(specs['desc'])
                if is_owned: st.button('Item Acquired ✓', key=f'owned_{item.replace(" ", "_")}', disabled=True)
                else:
                    if st.button(f"Purchase Gear ({specs['cost']}g)", key=f'buy_{item.replace(" ", "_")}', disabled=(getattr(player, 'gold', 0) < specs['cost'])):
                        try:
                            player.gold = getattr(player, 'gold', 0) - specs['cost']
                            player.inventory.append(item); player.equipped_gear[item] = 1
                            player.gear_colors[item] = "Basic Factory"
                            
                            # Single-slot auto-equip triggers
                            if specs['cat'] == 'Footwear' and not getattr(player, 'equipped_shoe_name', None): player.equipped_shoe_name = item
                            elif specs['cat'] == 'Sunglasses' and not getattr(player, 'equipped_sunglasses_name', None): player.equipped_sunglasses_name = item
                            elif specs['cat'] == 'Head Gear' and not getattr(player, 'equipped_headgear_name', None): player.equipped_headgear_name = item
                            elif specs['cat'] == 'Singlets' and not getattr(player, 'equipped_singlet_name', None): player.equipped_singlet_name = item
                            elif specs['cat'] == 'Shorts' and not getattr(player, 'equipped_shorts_name', None): player.equipped_shorts_name = item
                            elif specs['cat'] == 'Watches' and not getattr(player, 'equipped_watch_name', None): player.equipped_watch_name = item
                            
                            save_player_profile(player, FILE_PATH)
                            st.success(f'🎁 Collected {item}!'); st.rerun()
                        except Exception as e: st.error(f'Store fault: {str(e)}')
# PART 3 OF 3: VAULT SWAPPING HOOKS AND LOCKER ROOM APPAREL PAINT STATIONS
    with col_vault:
        st.markdown('### 📦 Your Locker Gear Locker Vault')
        if not player.inventory: st.info('Your equipment chest is empty. Run New Mexico tracks to generate gold balances.')
        else:
            vault_tab_filter = st.radio('View Locker Category:', ['Footwear', 'Sunglasses', 'Head Gear', 'Singlets', 'Shorts', 'Watches'], horizontal=True)
            
            slot_var_map = {
                'Footwear': 'equipped_shoe_name', 'Sunglasses': 'equipped_sunglasses_name',
                'Head Gear': 'equipped_headgear_name', 'Singlets': 'equipped_singlet_name', 
                'Shorts': 'equipped_shorts_name', 'Watches': 'equipped_watch_name'
            }
            active_slot_variable = slot_var_map[vault_tab_filter]
            currently_equipped_item = getattr(player, active_slot_variable, None)
            category_items = [item for item in player.inventory if item in gear_catalog and gear_catalog[item]['cat'] == vault_tab_filter]
            
            if not category_items: st.info(f"No collected item entries inside {vault_tab_filter} yet.")
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
                        st.markdown(f"🏅 **{owned_item}**")
                        v1, v2 = st.columns(2)
                        with v1:
                            st.markdown(f"`Tier Status: Rank {curr_level}/10`")
                            st.markdown(f"🎨 Style: {current_emoji} `{active_paint.upper()}`")
                            st.progress(float(curr_level / 10.0))
                            
                            if is_equipped: st.button('🎽 ACTIVE ON KIT', key=f'act_slot_eq_{idx}', disabled=True)
                            else:
                                if st.button('🟢 Equip Gear', key=f'equip_slot_action_{idx}'):
                                    try:
                                        setattr(player, active_slot_variable, owned_item)
                                        save_player_profile(player, FILE_PATH)
                                        st.success(f'⚡ Equipped {owned_item}!'); st.rerun()
                                    except Exception: pass
                        with v2:
                            # --- COSMETIC SPRAY-PAINT DROPDOWN MATRIX ---
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
                                        save_player_profile(player, FILE_PATH)
                                        st.success(f"⚡ Successfully applied {chosen_shade}!"); st.rerun()
                                    except Exception: pass
                                    
                                if gold_balance < 15:
                                    st.error("❌ Insufficient gold balance to repurchase coating variants.")
                                    
                            if is_maxed: st.button('👑 MAX RANK', key=f'max_slot_rank_{idx}', disabled=True)
                            else:
                                if st.button(f"Tune (+{next_level_cost}g)", key=f'tune_slot_action_{idx}', disabled=(gold_balance < next_level_cost)):
                                    try:
                                        player.gold = gold_balance - next_level_cost
                                        player.equipped_gear[owned_item] = curr_level + 1
                                        save_player_profile(player, FILE_PATH)
                                        st.success(f'⚡ Tuned asset to Rank +{curr_level + 1}!'); st.rerun()
                                    except Exception as e: st.error(f'Tuning fault: {str(e)}')

