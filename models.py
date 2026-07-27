# -*- coding: utf-8 -*-
import random
import streamlit as st  
import os
import shutil

class Character:
    def __init__(self, name="Athlete", bodyweight_lbs=180):
        self.name = name
        self.bodyweight = bodyweight_lbs
        self.level = 1
        self.total_xp = 0
        self.running_level = 1

        # --- PHYSIOLOGICAL BIOMETRICS LAYER ---
        self.vo2_max = 40.0         
        self.avg_heart_rate = 150   
        self.resting_heart_rate = 65 
        
        # Telemetry expanded vectors
        self.lifetime_elevation_gain = 0.0
        self.cadence_history = []
        self.elevation_milestone_history = []
        self.deep_rem_streak = 0

        # Currencies & Inventory Management
        self.stat_points = 0  
        self.gold = 50
        self.inventory = []
        self.equipped_gear = {"feet": "None", "accessory": "None"}
        self.registered_races = []

        # Infinite Grand Prix Track Records (15 Boss Slots)
        self.boss_wins = {
            "The Couch Potato": 0, "The Desk Jockey": 0, "The Cardio Hydra": 0,
            "The 5K Local Contender": 0, "The 10K Track Specialist": 0, "The Sonic Singularity": 0,
            "The Half-Marathon Cruiser": 0, "The Treadmill Titan": 0, "The Hill Sprint Gorgon": 0,
            "The Lactate Overlord": 0, "The Marathon Monarch": 0, "The 50K Trail Blazer": 0,
            "The Ultramarathon Wraith": 0, "The 100-Mile Century Drone": 0, "The Chronos Phantom": 0
        }

        # Fatigue & Recovery Engine Variables
        self.fatigue = 0
        self.days_tracked = 1
        self.synced_garmin_activities = []
        self.history_logs = []
        self.unlocked_badges = []  
        self.daily_miles = []
        # Hardcore Progression Tuning Factor Matrix
        self.base_xp = 250
        self.exponent = 1.8
        self.last_distance = 0.0
        self.last_pace = 0.0

    def xp_for_next_level(self):
        dynamic_exponent = self.exponent + (self.level * 0.04)
        calculated_xp = int(self.base_xp * (self.level ** dynamic_exponent))
        if self.equipped_gear.get("accessory") == "Oxygen Infused Fuel Cell":
            calculated_xp = int(calculated_xp * 0.90) 
        return max(1, calculated_xp)

    def check_level_up(self):
        leveled_up = False
        while True:
            required = self.xp_for_next_level()
            if self.total_xp >= required:
                self.total_xp -= required
                self.level += 1
                self.stat_points += 2  
                self.gold += 100
                leveled_up = True
            else:
                break
        return leveled_up

    def upgrade_stat(self, stat_name):
        if self.stat_points < 1:
            return False, "❌ No Allocation Points left!"
        if stat_name == "running":
            self.running_level += 1
            self.vo2_max += 0.5 
            self.stat_points -= 1
            self.log_history(f"Upgraded Running Skill to Lvl {self.running_level}. VO2 Max estimate pushed +0.5.")
            return True, f"🏃‍♂️ Fleetfoot Velocity specs upgraded! Base VO2 Max increased."
        return False, "Unknown stat."

    def exchange_gold_for_stat_point(self, base_cost=250):
        if self.gold < base_cost:
            return False, f"❌ Insufficient treasury funds! Requires {base_cost}g per point."
        self.gold -= base_cost
        self.stat_points += 1
        self.log_history(f"💱 CURRENCY EXCHANGE: Exchanged {base_cost}g for +1 Stat Allocation Point.")
        return True, "✨ Transaction Confirmed! +1 Skill Point transferred to your Physiology Matrix."
    def forge_apex_gear(self, item_one, item_two):
        """Combines two unique raw components into a Tier-2 Apex legendary artifact."""
        if item_one not in self.inventory or item_two not in self.inventory:
            return False, "❌ Material error: One or both of these components are missing from inventory stocks!"
        
        if item_one == item_two:
            return False, "❌ Alchemy error: Cannot craft an upgraded item using duplicate item instances!"

        crafted_item = "None"
        if (item_one == "Speed Vapor Pack" and item_two == "Carbon-Plated Carbon Shell") or (item_one == "Carbon-Plated Carbon Shell" and item_two == "Speed Vapor Pack"):
            crafted_item = "⚡ Hyper-Velocity Sonic Propulsion Boot"
        elif (item_one == "Titan Hydration Shaker" and item_two == "Bio-Engineered Buffer") or (item_one == "Bio-Engineered Buffer" and item_two == "Titan Hydration Shaker"):
            crafted_item = "🧬 Cellular Rejuvenation Serum Injector"

        if crafted_item == "None":
            return False, "❌ Blueprint mismatch: Those item combinations do not possess a valid alchemy product recipe."

        self.inventory.remove(item_one)
        self.inventory.remove(item_two)
        self.inventory.append(crafted_item)
        self.log_history(f"🛠️ ALALCHEMY FORGE: Synthesized {item_one} + {item_two} into {crafted_item}!")
        return True, f"✨ FORGE SUCCESSFUL! You synthesized the Tier-2 Apex artifact: **{crafted_item}**!"

    def calculate_hr_zone(self, avg_hr):
        max_hr = 220 - (self.level + 20)  
        pct = (avg_hr / max_hr) * 100 if max_hr > 0 else 0
        if pct >= 90: return 5, "🔥 Zone 5: Anaerobic Max Capacity", 2.0
        elif pct >= 80: return 4, "⚡ Zone 4: Lactate Threshold Effort", 1.5
        elif pct >= 70: return 3, "🏃 Zone 3: Aerobic Tempo Target", 1.2
        elif pct >= 60: return 2, "👟 Zone 2: Base Endurance Cruise", 1.0
        return 1, "🌱 Zone 1: Active Recovery Mobilization", 0.8
    def estimate_player_race_pace(self, target_distance_miles, course_elevation_feet=0.0):
        base_1mi_pace_mins = 60.0 / (max(5.0, self.vo2_max) * 0.25)
        predicted_total_time = (base_1mi_pace_mins * 1.0) * (max(0.01, target_distance_miles) ** 1.06)
        estimated_pace_per_mile = predicted_total_time / max(0.01, target_distance_miles)
        
        hist_cadence = getattr(self, 'cadence_history', [])
        avg_cadence = sum(hist_cadence) / len(hist_cadence) if hist_cadence else 165.0
        if avg_cadence >= 180: estimated_pace_per_mile *= 0.96  
        elif avg_cadence >= 170: estimated_pace_per_mile *= 0.98  
        else: estimated_pace_per_mile *= 1.03  
            
        if self.avg_heart_rate >= 160: estimated_pace_per_mile -= 0.12  
            
        if course_elevation_feet > 0:
            climbing_tax_pct = (course_elevation_feet / 100.0) * 0.035
            mitigation_factor = max(0.15, 1.0 - (self.running_level * 0.025))
            estimated_pace_per_mile *= (1.0 + (climbing_tax_pct * mitigation_factor))
            
        if self.fatigue >= 50: estimated_pace_per_mile *= (1.0 + ((self.fatigue - 49) * 0.0025))
        
        if self.equipped_gear.get("feet") == "⚡ Hyper-Velocity Sonic Propulsion Boot": estimated_pace_per_mile -= 0.45
        elif self.equipped_gear.get("feet") == "Pro Alpha Running Shoes": estimated_pace_per_mile -= 0.15 
        elif self.equipped_gear.get("feet") == "Carbon-Plated Carbon Shell": estimated_pace_per_mile -= 0.25 
            
        return max(3.5, estimated_pace_per_mile)

    def generate_ai_training_recommendation(self):
        hist_cadence = getattr(self, 'cadence_history', [])
        avg_cadence = sum(hist_cadence) / len(hist_cadence) if hist_cadence else 165.0
        if self.fatigue >= 75:
            return {"status": "🔴 CRITICAL ADVISORY: RECOVERY MODE MANDATORY", "strategy": "Systemic fatigue exceeds safe bounds.", "target": "Log an 8+ hour Deep REM sleep session form.", "benefit": "Flushes fatigue spikes."}
        elif avg_cadence < 172:
            return {"status": "🟡 VECTOR WARNING: MECHANICAL INEFFICIENCY DETECTED", "strategy": "Cadence matches overstriding footprints.", "target": "Execute shorthand turnover drills.", "benefit": "Unlocks fluid +75g cash milestones."}
        else:
            return {"status": "🟢 OPTIMAL MATRIX: BASE READY FOR ENGAGEMENT", "strategy": "Biometrics clear for velocity track work.", "target": "Challenge a coliseum grand prix boss.", "benefit": "High level scaling maximizes rare drop rates."}

    def evaluate_and_trigger_achievements(self):
        if not hasattr(self, 'unlocked_badges') or self.unlocked_badges is None: self.unlocked_badges = []
        newly_opened = []
        lifetime_miles = sum(self.daily_miles) if self.daily_miles else 0.0
        hist_cadence = getattr(self, 'cadence_history', [])
        avg_cadence = sum(hist_cadence) / len(hist_cadence) if hist_cadence else 0.0
        achievements = [
            {"title": "🥇 Legend of Marathon", "cond": max(self.daily_miles) >= 26.2 if self.daily_miles else False, "msg": "Completed marathon vector!"},
            {"title": "⛰️ Mountain Scale Core", "cond": self.lifetime_elevation_gain >= 5000.0, "msg": "Passed 5,000 vertical feet!"},
            {"title": "⚡ Fluid Stride Maestro", "cond": avg_cadence >= 175.0, "msg": "Maintained high stride averages!"},
            {"title": "👑 Century Volume Tier", "cond": lifetime_miles >= 100.0, "msg": "Logged 100+ lifetime miles!"}
        ]
        for item in achievements:
            if item['cond'] and item['title'] not in self.unlocked_badges:
                self.unlocked_badges.append(item['title']); newly_opened.append(item['title'])
                self.log_history(f"🎖️ MEDAL UNLOCKED: {item['title']}")
        return newly_opened

    def execute_boss_battle(self, boss_name, design_base_power):
        if self.fatigue >= 80: return False, "❌ Exhaustion level too high to step onto the race track!", "None"
        distance_map = {"The Couch Potato": (1.0, 0.0), "The Desk Jockey": (3.1, 20.0), "The Cardio Hydra": (6.2, 80.0), "The 5K Local Contender": (3.1, 40.0), "The 10K Track Specialist": (6.2, 0.0), "The Sonic Singularity": (5.0, 50.0), "The Half-Marathon Cruiser": (13.1, 150.0), "The Treadmill Titan": (13.1, 0.0), "The Hill Sprint Gorgon": (2.0, 600.0), "The Lactate Overlord": (4.0, 100.0), "The Marathon Monarch": (26.2, 300.0), "The 50K Trail Blazer": (31.1, 2400.0), "The Ultramarathon Wraith": (50.0, 4000.0), "The 100-Mile Century Drone": (100.0, 8000.0), "The Chronos Phantom": (26.2, 100.0)}
        race_specs = distance_map.get(boss_name, (5.0, 100.0))
        race_distance, course_elev = race_specs[0], race_specs[1]
        wins = self.boss_wins.get(boss_name, 0)
        player_pace = self.estimate_player_race_pace(race_distance, course_elev)
        player_finish_time = player_pace * race_distance
        base_boss_pace = 12.0 - (design_base_power * 0.05); mutated_boss_pace = base_boss_pace - (wins * 0.25)
        speed_floor = 4.5 if race_distance > 10.0 else 3.82; pacing_max_ceiling = player_pace / 3.0; final_capped_boss_pace = max(speed_floor, pacing_max_ceiling, mutated_boss_pace)
        boss_finish_time = final_capped_boss_pace * race_distance
        
        player_final_time = player_finish_time * random.uniform(0.98, 1.02); boss_final_time = boss_finish_time * random.uniform(0.98, 1.02)
        self.fatigue = min(100, self.fatigue + 25)
        if player_final_time < boss_final_time:
            self.boss_wins[boss_name] += 1
            base_gold_payout = 50 + (wins * 25)
            gold_gained = int(base_gold_payout * 1.10) if boss_name in getattr(self, 'registered_races', []) else base_gold_payout
            xp_gained = 100 + (wins * 50); self.gold += gold_gained; self.total_xp += xp_gained; self.check_level_up()
            
            dynamic_drop_rate = min(0.65, 0.40 + (self.level * 0.01))
            dropped_loot = "None"
            if random.random() <= dynamic_drop_rate:
                loot_pool = {"The Couch Potato": "Titan Hydration Shaker", "The Desk Jockey": "Ergonomic Insoles", "The Cardio Hydra": "Speed Vapor Pack", "The Marathon Monarch": "Oxygen Infused Fuel Cell", "The Sonic Singularity": "Chrono Pace Loom", "The Treadmill Titan": "Carbon-Plated Carbon Shell", "The Hill Sprint Gorgon": "Gravity Compensator Core", "The Lactate Overlord": "Bio-Engineered Buffer", "The Ultramarathon Wraith": "Eternal CamelBak Shield", "The Chronos Phantom": "Infinity Chronometer Track"}
                item_name = loot_pool.get(boss_name, "None")
                if item_name != "None" and item_name not in self.inventory:
                    self.inventory.append(item_name); dropped_loot = item_name
                    self.log_history(f"🎁 Level-Scaled Drops Secured: {item_name}")
            
            if not hasattr(self, 'elevation_milestone_history'): self.elevation_milestone_history = []
            self.elevation_milestone_history.append(self.lifetime_elevation_gain)
            
            self.evaluate_and_trigger_achievements()
            return True, f"🏆 VICTORY! Deactivated {boss_name}.", dropped_loot
        else:
            return False, f"💀 BLOWN ENGINE! Out-paced down the stretch loop.", "None"

    def record_run(self, distance, time_minutes, focus_type, source="Manual", file_avg_hr=150, elevation_gain=0.0, cadence=0):
        if self.fatigue >= 90: return "❌ Too exhausted to run! Go rest first.", False
        self.avg_heart_rate = int((self.avg_heart_rate + file_avg_hr) / 2)
        zone_num, zone_name, zone_multiplier = self.calculate_hr_zone(file_avg_hr)
        
        level_scale_factor = 1.0 + (self.level * 0.1)
        short_cutoff, elite_cutoff = 5.0 * level_scale_factor, 17.0 * level_scale_factor
        if distance > elite_cutoff: distance_xp = distance * 25; stat_gain = 5; fatigue_cost = 40
        elif distance >= short_cutoff: distance_xp = distance * 15; stat_gain = 3; fatigue_cost = 25
        else: distance_xp = distance * 10; stat_gain = 1; fatigue_cost = 15

        current_pace = time_minutes / (distance or 1)
        if current_pace < 8.0: self.vo2_max = min(85.0, self.vo2_max + (0.1 * distance))
        challenge_payout_multiplier = 1.0
        target_challenge = st.session_state.get("target_challenge_pace", 0)
        if current_pace <= target_challenge and target_challenge > 0: challenge_payout_multiplier = 1.5; distance_xp += 150 

        focus_modifier = 2.0 if (focus_type == "Speed" and current_pace < 7) else (1.5 if (focus_type == "Speed" and current_pace < 9) else 1.0)
        if focus_type == "Speed": fatigue_cost += 10
        gold_multiplier = 1.2 if self.equipped_gear.get("feet") == "Pro Alpha Running Shoes" else (1.3 if self.equipped_gear.get("feet") == "Carbon-Plated Carbon Shell" else 1.0)
        if self.equipped_gear.get("feet") == "⚡ Hyper-Velocity Sonic Propulsion Boot": gold_multiplier += 0.5
        if self.equipped_gear.get("accessory") == "Chrono Pace Loom": gold_multiplier += 1.0
            
        cadence_bonus_xp = 0
        if cadence >= 170: final_gold_payout = int(25 * gold_multiplier * challenge_payout_multiplier) + 75; cadence_bonus_xp += 50
        else: final_gold_payout = int(25 * gold_multiplier * challenge_payout_multiplier)
        if cadence > 0: self.cadence_history.append(cadence)

        elevation_bonus_xp = 0
        if elevation_gain > 0:
            self.lifetime_elevation_gain += elevation_gain
            elevation_bonus_xp = int((elevation_gain / 50.0) * 5)

        self.gold += final_gold_payout
        gear_xp_bonus, gear_fatigue_mod = self.get_gear_bonus("run")
        base_pool = (distance_xp + (50 if current_pace < 7 else 25)) * focus_modifier
        total_run_xp = int(base_pool * zone_multiplier) + gear_xp_bonus + cadence_bonus_xp + elevation_bonus_xp
        
        self.running_level += int(stat_gain * focus_modifier)
        self.total_xp += total_run_xp
        self.fatigue = min(100, self.fatigue + max(5, fatigue_cost - gear_fatigue_mod))
        self.daily_miles.append(distance)
        
        if not hasattr(self, 'elevation_milestone_history'): self.elevation_milestone_history = []
        self.elevation_milestone_history.append(self.lifetime_elevation_gain)
        
        self.log_history(f"Ran {distance:.2f} miles (+{final_gold_payout}g) [Pace: {current_pace:.2f} min/mi]")
        self.check_level_up(); self.evaluate_and_trigger_achievements()
        return f"🏃 Run Logged! Gained: {total_run_xp} XP.", True

    def rest_and_recover(self, sleep_hours, sleep_quality="Standard"):
        base_recovery = sleep_hours * 12
        if not hasattr(self, 'deep_rem_streak'): self.deep_rem_streak = 0
        
        quality_map = {"Restless (Disturbed Vectors)": 0.7, "Standard": 1.0, "Deep REM Mastery (Optimal)": 1.5}
        scalar = quality_map.get(sleep_quality, 1.0)
        final_recovery = base_recovery * scalar
        
        if "deep rem" in sleep_quality.lower() or "mastery" in sleep_quality.lower():
            self.deep_rem_streak += 1
        else:
            self.deep_rem_streak = 0

        if sleep_hours >= 8 and "deep" in sleep_quality.lower():
            final_recovery += 25
            self.resting_heart_rate = max(40, self.resting_heart_rate - 2)
        elif sleep_hours >= 8:
            final_recovery += 15
            self.resting_heart_rate = max(40, self.resting_heart_rate - 1)
            
        if self.equipped_gear.get("accessory") == "🧬 Cellular Rejuvenation Serum Injector":
            final_recovery *= 1.3
            
        self.fatigue = max(0, self.fatigue - final_recovery)
        self.log_history(f"Slept {sleep_hours} hours [{sleep_quality} Quality]. Fatigue cleared.")
        
        streak_triggered = False
        if self.deep_rem_streak >= 3:
            self.gold += 300; self.total_xp += 200; self.deep_rem_streak = 0
            self.check_level_up(); streak_triggered = True

        self.days_tracked += 1
        if streak_triggered:
            return f"🛌 Day {self.days_tracked} begins. Fatigue: {self.fatigue}%. 🔥 STREAK CATALYST UNLOCKED! +300 Gold & +200 XP secured!"
        return f"🛌 Day {self.days_tracked} begins. Fatigue: {self.fatigue}% [Active Streak: {self.deep_rem_streak}/3]"

    def buy_race_registration(self, boss_name, cost):
        if self.gold < cost: return False, "❌ Insufficient gold!"
        if not hasattr(self, 'registered_races'): self.registered_races = []
        if boss_name in self.registered_races: return False, "❌ Already registered!"
        self.gold -= cost; self.registered_races.append(boss_name)
        return True, f"🎟️ Registered: {boss_name}"
    def buy_item(self, item_name, cost):
        if self.gold < cost: return False, "❌ Insufficient gold!"
        if item_name in self.inventory: return False, "❌ Owned!"
        self.gold -= cost; self.inventory.append(item_name)
        return True, f"🛍️ Purchased {item_name}!"
    def equip_item(self, item_name, slot):
        if item_name not in self.inventory: return False, "❌ Unowned!"
        self.equipped_gear[slot] = item_name; return True, f"✅ Configured {item_name}!"
    def get_gear_bonus(self, activity_type):
        bx, fr = 0, 0
        if activity_type == "run":
            if self.equipped_gear["feet"] == "⚡ Hyper-Velocity Sonic Propulsion Boot": bx += 100; fr += 12
            elif self.equipped_gear["feet"] == "Pro Alpha Running Shoes": bx += 30; fr += 5
            elif self.equipped_gear["feet"] == "Speed Vapor Pack": bx += 60; fr += 8
        if self.equipped_gear["accessory"] == "Titan Hydration Shaker": fr += 5
        return bx, fr
    def log_history(self, message): self.history_logs.append(f"Day {self.days_tracked}: {message}")
    def to_dict(self): return {k: v for k, v in self.__dict__.items() if "streamlit" not in str(type(v))}
    @classmethod
    def from_dict(cls, data):
        char = cls()
        for key, value in data.items(): setattr(char, key, value)
        return char

