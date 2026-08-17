# -*- coding: utf-8 -*-
"""Unit tests for the trophy room analytics engine in showroom_engine.py."""
import datetime

import pandas as pd
import pytest

import arena_tournaments_config as arena_cfg
import metrics_config as cfg
import personal_records_config as pr_cfg
import showroom_engine as engine


def make_log(date, miles=5.0, pace=8.5, elevation="+250 ft", **extra):
    payload = {
        "Date": date,
        "Distance (Miles)": miles,
        "pace": pace,
        "Elevation (ft)": elevation,
    }
    payload.update(extra)
    return payload


@pytest.fixture
def df_logs():
    return engine.sanitize_json_history_logs(
        [
            make_log("2024-01-10", miles=6.0, pace=9.0, elevation="+300 ft"),
            make_log("2024-06-15", miles=13.5, pace=7.5, elevation="+1200.5 ft"),
            make_log("2025-02-01", miles=3.2, pace=6.4, elevation="+50 ft"),
        ]
    )


class TestSanitizeJsonHistoryLogs:
    def test_none_and_non_list_inputs_return_empty_frame(self):
        assert engine.sanitize_json_history_logs(None).empty
        assert engine.sanitize_json_history_logs("not a list").empty

    def test_string_logs_are_filtered_out(self):
        df = engine.sanitize_json_history_logs(["Day 3: lost to the Cardio Hydra"])
        assert df.empty

    def test_entries_without_dates_are_dropped(self):
        df = engine.sanitize_json_history_logs([{"Distance (Miles)": 4.0}])
        assert df.empty

    def test_alternate_field_names_are_accepted(self):
        df = engine.sanitize_json_history_logs(
            [{"date": "2025-01-01", "distance": 4.0, "Avg_Pace": 8.0, "elevation": 120}]
        )
        row = df.iloc[0]
        assert (row["Display_Distance"], row["Avg_Pace"], row["Total_Ascent"]) == (
            4.0,
            8.0,
            120.0,
        )

    def test_elevation_strings_are_parsed_to_absolute_floats(self):
        df = engine.sanitize_json_history_logs([make_log("2025-01-01", elevation="-865.5 ft")])
        assert df.iloc[0]["Total_Ascent"] == pytest.approx(865.5)

    def test_unparseable_values_fall_back_to_zero(self):
        df = engine.sanitize_json_history_logs(
            [make_log("2025-01-01", miles="lots", pace="fast", elevation="steep")]
        )
        row = df.iloc[0]
        assert (row["Display_Distance"], row["Avg_Pace"], row["Total_Ascent"]) == (0.0, 0.0, 0.0)

    def test_five_k_time_is_carried_through(self):
        df = engine.sanitize_json_history_logs([make_log("2025-01-01", Five_K_Time="21:30")])
        assert df.iloc[0]["Five_K_Time"] == "21:30"


class TestPersonalRecords:
    def test_empty_logs_use_configured_fallbacks(self):
        prs = engine.calculate_personal_records(pd.DataFrame())
        assert prs["longest_run"]["val"] == "0.00 Mi"
        assert prs["longest_run"]["date"] == "No Logs Uploaded"

    def test_every_registered_record_is_present(self, df_logs):
        prs = engine.calculate_personal_records(df_logs)
        expected = {r["id"] for r in pr_cfg.PERSONAL_RECORDS_REGISTRY}
        assert set(prs) == expected

    def test_longest_run_uses_max_distance_and_its_date(self, df_logs):
        prs = engine.calculate_personal_records(df_logs)
        assert prs["longest_run"]["val"].startswith("13.50")
        assert prs["longest_run"]["date"] == "2024-06-15"

    def test_fastest_pace_is_formatted_as_minutes_and_seconds(self, df_logs):
        prs = engine.calculate_personal_records(df_logs)
        assert prs["fastest_mile"]["val"].startswith("6:24")

    def test_peak_year_sums_annual_mileage(self, df_logs):
        prs = engine.calculate_personal_records(df_logs)["peak_annual_volume"]
        assert prs["val"].startswith("19.5")
        assert prs["date"] == "Year: 2024"

    def test_min_mode_picks_the_smallest_positive_numeric_value(self, df_logs):
        df = df_logs.copy()
        df["Five_K_Time"] = [0, 1335, 1500]
        prs = engine.calculate_personal_records(df)["fastest_5k"]
        assert prs["val"].startswith("1335")
        assert prs["date"] == "2024-06-15"

    def test_min_mode_keeps_fallback_for_non_numeric_values(self, df_logs):
        df = df_logs.copy()
        df["Five_K_Time"] = ["22:15", "23:40", ""]
        fallback = next(
            r["fallback_value"]
            for r in pr_cfg.PERSONAL_RECORDS_REGISTRY
            if r["id"] == "fastest_5k"
        )
        assert engine.calculate_personal_records(df)["fastest_5k"]["val"] == fallback

    def test_missing_columns_keep_fallback_values(self):
        df = pd.DataFrame([{"Date": "2025-01-01"}])
        prs = engine.calculate_personal_records(df)
        assert prs["longest_run"]["val"] == "0.00 Mi"


class TestAwardInstances:
    def test_empty_logs_return_typed_empty_frame(self):
        df = engine.compile_all_award_instances(None)
        assert list(df.columns) == ["award_code", "date", "metric", "type", "details"]
        assert df.empty

    def test_rows_without_rewards_produce_no_instances(self, df_logs):
        assert engine.compile_all_award_instances(df_logs).empty

    def test_awards_are_expanded_with_type_prefixed_codes(self):
        df = engine.sanitize_json_history_logs([make_log("2025-04-01", miles=8.0)])
        df["earned_patches"] = [
            [
                {"id": "rabbit", "name": "Rabbit Cruise", "type": "patch"},
                {"id": "century", "name": "Century", "type": "trophy"},
            ]
        ]
        instances = engine.compile_all_award_instances(df)
        assert list(instances["award_code"]) == ["patch_rabbit", "trophy_century"]
        assert instances["date"].unique().tolist() == ["2025-04-01"]
        assert "Distance: 8.00 Mi" in instances.iloc[0]["details"]

    def test_awards_without_ids_are_skipped(self, df_logs):
        df = df_logs.copy()
        df["earned_patches"] = [[{"name": "Nameless"}], [], []]
        assert engine.compile_all_award_instances(df).empty

    def test_invalid_dates_are_dropped(self):
        df = pd.DataFrame([{"Date": "not-a-date", "Display_Distance": 1.0, "Avg_Pace": 8.0}])
        assert engine.compile_all_award_instances(df).empty


class TestAthleteRpgLevel:
    def test_no_instances_returns_entry_rank(self):
        level, xp, pct, title = engine.calculate_athlete_rpg_level(pd.DataFrame())
        assert (level, xp, pct) == (1, 0, 0)
        assert title == cfg.ATHLETIC_TIERS[0]["title"]

    def test_unknown_codes_use_the_default_gem_tier(self):
        df = pd.DataFrame([{"award_code": "patch_unknown_thing"}])
        level, xp, pct, _ = engine.calculate_athlete_rpg_level(df)
        assert xp == cfg.GEM_TIER_REGISTRY["emerald"]["xp"]
        assert level == 1
        assert pct == int((xp / cfg.XP_PER_LEVEL_THRESHOLD) * 100)

    def test_weekly_mileage_codes_resolve_their_configured_tier(self):
        reward = cfg.WEEKLY_MILEAGE_REWARDS[0]
        df = pd.DataFrame([{"award_code": f"weekly_miles_{reward['miles']}"}])
        _, xp, _, _ = engine.calculate_athlete_rpg_level(df)
        assert xp == cfg.GEM_TIER_REGISTRY[reward["tier"]]["xp"]

    def test_weekly_climb_codes_resolve_their_configured_tier(self):
        reward = cfg.WEEKLY_ELEVATION_REWARDS[0]
        df = pd.DataFrame([{"award_code": f"weekly_climb_{reward['climb_ft']}"}])
        _, xp, _, _ = engine.calculate_athlete_rpg_level(df)
        assert xp == cfg.GEM_TIER_REGISTRY[reward["tier"]]["xp"]

    def test_level_and_progress_roll_over_at_the_threshold(self):
        df = pd.DataFrame([{"award_code": "patch_unknown_thing"}] * 100)
        level, xp_in_level, pct, title = engine.calculate_athlete_rpg_level(df)
        assert level > 1
        assert xp_in_level < cfg.XP_PER_LEVEL_THRESHOLD
        assert 0 <= pct <= 100
        assert title in [t["title"] for t in cfg.ATHLETIC_TIERS]


class TestStreakDefense:
    def test_empty_logs_are_stable(self):
        assert engine.check_streak_defense_status(pd.DataFrame()) == ("stable", 0)

    def test_recent_activity_is_stable(self):
        today = datetime.date.today().isoformat()
        assert engine.check_streak_defense_status(
            engine.sanitize_json_history_logs([make_log(today)])
        ) == ("stable", 0)

    def test_long_layoff_starts_decaying(self):
        stale = (
            datetime.date.today() - datetime.timedelta(days=cfg.DEFENSE_WINDOW_DAYS + 5)
        ).isoformat()
        status, days = engine.check_streak_defense_status(
            engine.sanitize_json_history_logs([make_log(stale)])
        )
        assert status == "decaying"
        assert days >= cfg.DEFENSE_WINDOW_DAYS

    def test_unparseable_dates_are_treated_as_stable(self):
        df = pd.DataFrame([{"Date": "whenever"}])
        assert engine.check_streak_defense_status(df) == ("stable", 0)


class TestCurrentWeekMetrics:
    def test_empty_logs_return_zeroes(self):
        assert engine.calculate_current_week_metrics(pd.DataFrame()) == (0.0, 0.0)

    def test_only_current_iso_week_rows_are_summed(self):
        today = datetime.date.today()
        last_month = today - datetime.timedelta(days=45)
        df = engine.sanitize_json_history_logs(
            [
                make_log(today.isoformat(), miles=4.0, elevation="+100 ft"),
                make_log(last_month.isoformat(), miles=9.0, elevation="+900 ft"),
            ]
        )
        assert engine.calculate_current_week_metrics(df) == (4.0, 100.0)

    def test_broken_frames_return_zeroes(self):
        assert engine.calculate_current_week_metrics(pd.DataFrame([{"Date": "2025-01-01"}])) == (
            0.0,
            0.0,
        )


class TestCovetedTargets:
    def test_all_targets_start_locked(self):
        status = engine.evaluate_coveted_targets_status(pd.DataFrame())
        assert set(status) == set(cfg.COVETED_TARGETS)
        assert all(v["status"] == "Locked" for v in status.values())

    def test_partial_progress_is_reported_as_a_percentage(self, df_logs):
        status = engine.evaluate_coveted_targets_status(df_logs)["coveted_century_mount"]
        assert status["status"] == "Locked"
        assert "13.5" in status["progress_label"]

    def test_ultra_distance_unlocks_the_century_mount(self):
        required = cfg.COVETED_TARGETS["coveted_century_mount"]["distance_required"]
        df = engine.sanitize_json_history_logs([make_log("2025-01-01", miles=required + 1)])
        status = engine.evaluate_coveted_targets_status(df)["coveted_century_mount"]
        assert status["status"] == "Unlocked"
        assert "Mi Logged" in status["progress_label"]


class TestArenaTournaments:
    def test_empty_logs_leave_every_arena_locked(self):
        status = engine.evaluate_arena_tournament_medals(pd.DataFrame())
        assert set(status) == set(arena_cfg.ARENA_TOURNAMENTS_REGISTRY)
        assert all(v["count"] == 0 for v in status.values())

    def test_qualifying_runs_are_counted_per_arena(self):
        sprint_target = arena_cfg.ARENA_TOURNAMENTS_REGISTRY["coliseum_sprint_clash"][
            "target_distance"
        ]
        vert_target = arena_cfg.ARENA_TOURNAMENTS_REGISTRY["alpine_vert_challenge"][
            "target_elevation_ft"
        ]
        df = engine.sanitize_json_history_logs(
            [
                make_log("2025-01-01", miles=sprint_target + 1, elevation=f"+{vert_target + 10} ft"),
                make_log("2025-01-08", miles=sprint_target - 1, elevation="+50 ft"),
            ]
        )
        status = engine.evaluate_arena_tournament_medals(df)
        assert status["coliseum_sprint_clash"] == {"count": 1, "status_label": "x1 Contested"}
        assert status["alpine_vert_challenge"] == {"count": 1, "status_label": "x1 Climbed"}

    def test_short_runs_keep_arenas_locked(self):
        df = engine.sanitize_json_history_logs([make_log("2025-01-01", miles=1.0, elevation="+5 ft")])
        status = engine.evaluate_arena_tournament_medals(df)
        assert status["coliseum_sprint_clash"]["status_label"] == "LOCKED MATCH"
        assert status["alpine_vert_challenge"]["status_label"] == "LOCKED MATCH"
