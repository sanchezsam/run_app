# -*- coding: utf-8 -*-
"""Unit tests for the Character progression engine in models.py."""
import pytest

from models import Character


@pytest.fixture
def char():
    return Character(name="Tester", bodyweight_lbs=175)


class TestLevelling:
    def test_xp_for_next_level_scales_with_level(self, char):
        first = char.xp_for_next_level()
        char.level = 5
        assert char.xp_for_next_level() > first

    def test_fuel_cell_accessory_discounts_requirement(self, char):
        full_cost = char.xp_for_next_level()
        char.equipped_gear["accessory"] = "Oxygen Infused Fuel Cell"
        assert char.xp_for_next_level() == int(full_cost * 0.90)

    def test_check_level_up_consumes_xp_and_pays_rewards(self, char):
        required = char.xp_for_next_level()
        char.total_xp = required + 10
        assert char.check_level_up() is True
        assert char.level == 2
        assert char.total_xp == 10
        assert char.stat_points == 2
        assert char.gold == 150

    def test_check_level_up_can_chain_multiple_levels(self, char):
        char.total_xp = 100000
        char.check_level_up()
        assert char.level > 2

    def test_check_level_up_noop_below_threshold(self, char):
        char.total_xp = 1
        assert char.check_level_up() is False
        assert char.level == 1


class TestStatsAndCurrency:
    def test_upgrade_stat_requires_points(self, char):
        ok, msg = char.upgrade_stat("running")
        assert ok is False
        assert "No Allocation Points" in msg

    def test_upgrade_running_spends_point_and_raises_vo2(self, char):
        char.stat_points = 1
        ok, _ = char.upgrade_stat("running")
        assert ok is True
        assert char.running_level == 2
        assert char.vo2_max == pytest.approx(40.5)
        assert char.stat_points == 0
        assert char.history_logs

    def test_upgrade_unknown_stat_rejected(self, char):
        char.stat_points = 3
        ok, msg = char.upgrade_stat("swimming")
        assert (ok, char.stat_points) == (False, 3)
        assert msg == "Unknown stat."

    def test_exchange_gold_requires_funds(self, char):
        ok, _ = char.exchange_gold_for_stat_point()
        assert ok is False
        assert char.stat_points == 0

    def test_exchange_gold_grants_stat_point(self, char):
        char.gold = 300
        ok, _ = char.exchange_gold_for_stat_point(base_cost=250)
        assert ok is True
        assert (char.gold, char.stat_points) == (50, 1)


class TestForge:
    def test_missing_components_rejected(self, char):
        ok, msg = char.forge_apex_gear("Speed Vapor Pack", "Carbon-Plated Carbon Shell")
        assert ok is False
        assert "Material error" in msg

    def test_duplicate_instances_rejected(self, char):
        char.inventory = ["Speed Vapor Pack"]
        ok, msg = char.forge_apex_gear("Speed Vapor Pack", "Speed Vapor Pack")
        assert ok is False
        assert "Alchemy error" in msg

    def test_unknown_recipe_rejected(self, char):
        char.inventory = ["Speed Vapor Pack", "Titan Hydration Shaker"]
        ok, msg = char.forge_apex_gear("Speed Vapor Pack", "Titan Hydration Shaker")
        assert ok is False
        assert "Blueprint mismatch" in msg
        assert len(char.inventory) == 2

    @pytest.mark.parametrize(
        "components,expected",
        [
            (
                ("Speed Vapor Pack", "Carbon-Plated Carbon Shell"),
                "⚡ Hyper-Velocity Sonic Propulsion Boot",
            ),
            (
                ("Carbon-Plated Carbon Shell", "Speed Vapor Pack"),
                "⚡ Hyper-Velocity Sonic Propulsion Boot",
            ),
            (
                ("Titan Hydration Shaker", "Bio-Engineered Buffer"),
                "🧬 Cellular Rejuvenation Serum Injector",
            ),
            (
                ("Bio-Engineered Buffer", "Titan Hydration Shaker"),
                "🧬 Cellular Rejuvenation Serum Injector",
            ),
        ],
    )
    def test_valid_recipes_consume_components(self, char, components, expected):
        char.inventory = list(components)
        ok, _ = char.forge_apex_gear(*components)
        assert ok is True
        assert char.inventory == [expected]


class TestHeartRateZones:
    @pytest.mark.parametrize(
        "avg_hr,zone,multiplier",
        [(200, 5, 2.0), (165, 4, 1.5), (145, 3, 1.2), (125, 2, 1.0), (90, 1, 0.8)],
    )
    def test_zone_boundaries(self, char, avg_hr, zone, multiplier):
        num, label, mult = char.calculate_hr_zone(avg_hr)
        assert (num, mult) == (zone, multiplier)
        assert f"Zone {zone}" in label


class TestRacePaceEstimate:
    def test_pace_never_drops_below_floor(self, char):
        char.vo2_max = 85.0
        assert char.estimate_player_race_pace(3.1) >= 3.5

    def test_longer_distance_yields_slower_pace(self, char):
        assert char.estimate_player_race_pace(26.2) > char.estimate_player_race_pace(3.1)

    def test_high_cadence_history_improves_pace(self, char):
        baseline = char.estimate_player_race_pace(10.0)
        char.cadence_history = [185, 185]
        assert char.estimate_player_race_pace(10.0) < baseline

    def test_elevation_adds_climbing_tax(self, char):
        flat = char.estimate_player_race_pace(10.0)
        assert char.estimate_player_race_pace(10.0, course_elevation_feet=2000.0) > flat

    def test_fatigue_penalises_pace(self, char):
        fresh = char.estimate_player_race_pace(10.0)
        char.fatigue = 90
        assert char.estimate_player_race_pace(10.0) > fresh

    def test_apex_boots_beat_pro_alpha_shoes(self, char):
        char.equipped_gear["feet"] = "Pro Alpha Running Shoes"
        shoes = char.estimate_player_race_pace(10.0)
        char.equipped_gear["feet"] = "⚡ Hyper-Velocity Sonic Propulsion Boot"
        assert char.estimate_player_race_pace(10.0) < shoes


class TestRecommendations:
    def test_critical_fatigue_advisory(self, char):
        char.fatigue = 80
        assert "CRITICAL ADVISORY" in char.generate_ai_training_recommendation()["status"]

    def test_low_cadence_warning(self, char):
        char.cadence_history = [150, 160]
        assert "VECTOR WARNING" in char.generate_ai_training_recommendation()["status"]

    def test_optimal_matrix(self, char):
        char.cadence_history = [180, 182]
        assert "OPTIMAL MATRIX" in char.generate_ai_training_recommendation()["status"]


class TestAchievements:
    def test_no_badges_without_activity(self, char):
        assert char.evaluate_and_trigger_achievements() == []

    def test_marathon_and_century_badges_unlock(self, char):
        char.daily_miles = [26.5, 80.0]
        opened = char.evaluate_and_trigger_achievements()
        assert "🥇 Legend of Marathon" in opened
        assert "👑 Century Volume Tier" in opened

    def test_elevation_and_cadence_badges_unlock(self, char):
        char.lifetime_elevation_gain = 6000.0
        char.cadence_history = [180, 176]
        opened = char.evaluate_and_trigger_achievements()
        assert "⛰️ Mountain Scale Core" in opened
        assert "⚡ Fluid Stride Maestro" in opened

    def test_badges_are_not_duplicated(self, char):
        char.lifetime_elevation_gain = 6000.0
        char.evaluate_and_trigger_achievements()
        assert char.evaluate_and_trigger_achievements() == []

    def test_none_badge_container_is_repaired(self, char):
        char.unlocked_badges = None
        char.evaluate_and_trigger_achievements()
        assert char.unlocked_badges == []


class TestBossBattle:
    def test_exhausted_athlete_cannot_race(self, char):
        char.fatigue = 85
        won, msg, loot = char.execute_boss_battle("The Couch Potato", 10)
        assert (won, loot) == (False, "None")
        assert "Exhaustion" in msg

    def test_victory_awards_gold_xp_and_loot(self, char, monkeypatch):
        monkeypatch.setattr("models.random.uniform", lambda a, b: 1.0)
        monkeypatch.setattr("models.random.random", lambda: 0.0)
        char.vo2_max = 85.0
        won, msg, loot = char.execute_boss_battle("The Couch Potato", 0)
        assert won is True
        assert char.boss_wins["The Couch Potato"] == 1
        assert char.gold > 50
        assert loot == "Titan Hydration Shaker"
        assert loot in char.inventory
        assert char.fatigue == 25

    def test_registered_race_pays_gold_bonus(self, char, monkeypatch):
        monkeypatch.setattr("models.random.uniform", lambda a, b: 1.0)
        monkeypatch.setattr("models.random.random", lambda: 1.0)
        char.vo2_max = 85.0
        char.registered_races = ["The Couch Potato"]
        char.execute_boss_battle("The Couch Potato", 0)
        assert char.gold == 50 + int(50 * 1.10)

    def test_defeat_leaves_records_untouched(self, char, monkeypatch):
        monkeypatch.setattr("models.random.uniform", lambda a, b: 1.0)
        char.vo2_max = 5.0
        char.fatigue = 79
        won, msg, loot = char.execute_boss_battle("The Chronos Phantom", 100)
        assert (won, loot) == (False, "None")
        assert char.boss_wins["The Chronos Phantom"] == 0
        assert char.gold == 50

    def test_unknown_boss_uses_default_race_specs(self, char, monkeypatch):
        monkeypatch.setattr("models.random.uniform", lambda a, b: 1.0)
        monkeypatch.setattr("models.random.random", lambda: 1.0)
        char.vo2_max = 85.0
        char.boss_wins["Mystery Rival"] = 0
        won, _, loot = char.execute_boss_battle("Mystery Rival", 0)
        assert (won, loot) == (True, "None")


class TestRecordRun:
    def test_exhausted_athlete_cannot_log_run(self, char):
        char.fatigue = 95
        msg, ok = char.record_run(5.0, 40.0, "Endurance")
        assert ok is False
        assert "Too exhausted" in msg

    def test_short_run_awards_minimum_tier(self, char):
        msg, ok = char.record_run(2.0, 20.0, "Endurance", file_avg_hr=140)
        assert ok is True
        assert char.daily_miles == [2.0]
        assert char.fatigue == 15
        assert "Run Logged" in msg

    def test_elite_distance_costs_more_fatigue_than_short_run(self, char):
        char.record_run(30.0, 240.0, "Endurance", file_avg_hr=140)
        assert char.fatigue == 40

    def test_speed_focus_adds_fatigue_and_multiplier(self, char):
        char.record_run(6.0, 36.0, "Speed", file_avg_hr=140)
        assert char.fatigue == 35

    def test_fast_pace_raises_vo2_max(self, char):
        char.record_run(6.0, 42.0, "Endurance", file_avg_hr=140)
        assert char.vo2_max > 40.0

    def test_high_cadence_pays_gold_bonus_and_is_recorded(self, char):
        char.record_run(3.0, 30.0, "Endurance", file_avg_hr=140, cadence=175)
        assert char.cadence_history == [175]
        assert char.gold == 50 + 25 + 75

    def test_elevation_gain_accumulates_lifetime_total(self, char):
        char.record_run(3.0, 30.0, "Endurance", file_avg_hr=140, elevation_gain=500.0)
        assert char.lifetime_elevation_gain == 500.0
        assert char.elevation_milestone_history == [500.0]

    def test_zero_distance_does_not_divide_by_zero(self, char):
        msg, ok = char.record_run(0.0, 30.0, "Endurance", file_avg_hr=140)
        assert ok is True

    def test_gold_multiplier_gear_pays_more(self, char):
        plain = Character()
        plain.record_run(4.0, 40.0, "Endurance", file_avg_hr=140)
        char.equipped_gear["feet"] = "Carbon-Plated Carbon Shell"
        char.record_run(4.0, 40.0, "Endurance", file_avg_hr=140)
        assert char.gold > plain.gold


class TestRestAndRecover:
    def test_standard_sleep_clears_fatigue(self, char):
        char.fatigue = 60
        char.rest_and_recover(4, "Standard")
        assert char.fatigue == 12
        assert char.days_tracked == 2

    def test_long_sleep_lowers_resting_heart_rate(self, char):
        char.fatigue = 100
        char.rest_and_recover(8, "Standard")
        assert char.resting_heart_rate == 64
        assert char.fatigue == 0

    def test_deep_rem_gives_larger_recovery_and_streak(self, char):
        char.fatigue = 100
        char.rest_and_recover(8, "Deep REM Mastery (Optimal)")
        assert char.deep_rem_streak == 1
        assert char.resting_heart_rate == 63

    def test_restless_sleep_resets_streak(self, char):
        char.deep_rem_streak = 2
        char.rest_and_recover(6, "Restless (Disturbed Vectors)")
        assert char.deep_rem_streak == 0

    def test_three_deep_sleeps_trigger_streak_catalyst(self, char):
        for _ in range(3):
            msg = char.rest_and_recover(8, "Deep REM Mastery (Optimal)")
        assert "STREAK CATALYST" in msg
        assert char.deep_rem_streak == 0
        assert char.gold >= 350

    def test_serum_injector_boosts_recovery(self, char):
        char.fatigue = 100
        char.equipped_gear["accessory"] = "🧬 Cellular Rejuvenation Serum Injector"
        char.rest_and_recover(2, "Standard")
        assert char.fatigue == pytest.approx(100 - (24 * 1.3))


class TestShopAndGear:
    def test_buy_item_requires_gold(self, char):
        ok, msg = char.buy_item("Pro Alpha Running Shoes", 500)
        assert (ok, char.inventory) == (False, [])

    def test_buy_item_rejects_duplicates(self, char):
        char.gold = 500
        char.buy_item("Pro Alpha Running Shoes", 100)
        ok, msg = char.buy_item("Pro Alpha Running Shoes", 100)
        assert ok is False
        assert char.gold == 400

    def test_equip_requires_ownership(self, char):
        ok, _ = char.equip_item("Pro Alpha Running Shoes", "feet")
        assert (ok, char.equipped_gear["feet"]) == (False, "None")

    def test_equip_owned_item(self, char):
        char.inventory.append("Pro Alpha Running Shoes")
        ok, _ = char.equip_item("Pro Alpha Running Shoes", "feet")
        assert (ok, char.equipped_gear["feet"]) == (True, "Pro Alpha Running Shoes")

    def test_race_registration_flow(self, char):
        char.gold = 100
        assert char.buy_race_registration("The Marathon Monarch", 250)[0] is False
        char.gold = 300
        assert char.buy_race_registration("The Marathon Monarch", 250)[0] is True
        assert char.gold == 50
        assert char.buy_race_registration("The Marathon Monarch", 0)[0] is False

    @pytest.mark.parametrize(
        "feet,expected",
        [
            ("⚡ Hyper-Velocity Sonic Propulsion Boot", (100, 12)),
            ("Pro Alpha Running Shoes", (30, 5)),
            ("Speed Vapor Pack", (60, 8)),
            ("None", (0, 0)),
        ],
    )
    def test_gear_bonus_by_footwear(self, char, feet, expected):
        char.equipped_gear["feet"] = feet
        assert char.get_gear_bonus("run") == expected

    def test_hydration_accessory_only_reduces_fatigue(self, char):
        char.equipped_gear["accessory"] = "Titan Hydration Shaker"
        assert char.get_gear_bonus("run") == (0, 5)

    def test_non_run_activity_gets_no_footwear_bonus(self, char):
        char.equipped_gear["feet"] = "Pro Alpha Running Shoes"
        assert char.get_gear_bonus("sleep") == (0, 0)


class TestSerialization:
    def test_round_trip_preserves_state(self, char):
        char.gold = 999
        char.log_history("checkpoint")
        restored = Character.from_dict(char.to_dict())
        assert restored.gold == 999
        assert restored.history_logs == char.history_logs

    def test_log_history_prefixes_day_counter(self, char):
        char.days_tracked = 7
        char.log_history("did a thing")
        assert char.history_logs[-1] == "Day 7: did a thing"
