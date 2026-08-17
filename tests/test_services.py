# -*- coding: utf-8 -*-
"""Unit tests for the parsing and analytics helpers in services.py."""
import datetime
import json

import pytest

import services
from models import Character

GPX_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1">
  <metadata><time>2025-03-09T12:00:00Z</time></metadata>
  <trk><trkseg>
{points}
  </trkseg></trk>
</gpx>
"""


def build_gpx(points, include_metadata_time=True):
    """Builds a GPX document from (lat, lon, elevation_m, iso_time) tuples."""
    nodes = []
    for lat, lon, ele, stamp in points:
        time_node = f"<time>{stamp}</time>" if stamp else ""
        nodes.append(
            f'    <trkpt lat="{lat}" lon="{lon}"><ele>{ele}</ele>{time_node}</trkpt>'
        )
    doc = GPX_TEMPLATE.format(points="\n".join(nodes))
    if not include_metadata_time:
        doc = doc.replace("<metadata><time>2025-03-09T12:00:00Z</time></metadata>", "")
    return doc.encode("utf-8")


ONE_MILE_POINTS = [
    (39.0000, -105.0000, 1600.0, "2025-03-09T12:00:00Z"),
    (39.0200, -105.0000, 1650.0, "2025-03-09T12:08:00Z"),
    (39.0400, -105.0000, 1620.0, "2025-03-09T12:16:00Z"),
]


class TestParseGarminGpx:
    def test_missing_trackpoints_is_reported(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ok, msg = services.parse_garmin_gpx(Character(), b"<gpx></gpx>")
        assert ok is False
        assert "No tracking coordinate nodes" in msg

    def test_invalid_xml_returns_error_message(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        ok, msg = services.parse_garmin_gpx(Character(), b"not xml at all")
        assert ok is False
        assert msg

    def test_successful_sync_awards_gold_xp_and_fatigue(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        player = Character()
        ok, msg = services.parse_garmin_gpx(player, build_gpx(ONE_MILE_POINTS))
        assert ok is True
        assert "2025-03-09" in msg
        assert "Duration: 00:16:00" in msg
        assert player.gold > 50
        assert player.total_xp > 0
        assert player.days_tracked == 2
        assert 0 < player.fatigue <= 100
        assert len(player.history_logs) == 1

    def test_elevation_gain_is_converted_to_feet(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        player = Character()
        _, msg = services.parse_garmin_gpx(player, build_gpx(ONE_MILE_POINTS))
        assert "+164.0 ft" in msg

    def test_save_file_is_written(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        services.parse_garmin_gpx(Character(), build_gpx(ONE_MILE_POINTS))
        saved = json.loads((tmp_path / "save_file.json").read_text(encoding="utf-8"))
        assert saved["history_logs"]

    def test_duplicate_date_is_rejected(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        player = Character()
        services.parse_garmin_gpx(player, build_gpx(ONE_MILE_POINTS))
        ok, msg = services.parse_garmin_gpx(player, build_gpx(ONE_MILE_POINTS))
        assert ok is False
        assert "Duplicate Workout Applied" in msg

    def test_zero_distance_track_is_rejected(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        stationary = [
            (39.0, -105.0, 1600.0, "2025-03-09T12:00:00Z"),
            (39.0, -105.0, 1600.0, "2025-03-09T12:10:00Z"),
        ]
        ok, msg = services.parse_garmin_gpx(Character(), build_gpx(stationary))
        assert ok is False
        assert "0 miles covered" in msg

    def test_missing_timestamps_fall_back_to_default_duration(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        points = [(lat, lon, ele, None) for lat, lon, ele, _ in ONE_MILE_POINTS]
        ok, msg = services.parse_garmin_gpx(
            Character(), build_gpx(points, include_metadata_time=False)
        )
        assert ok is True
        assert "Duration: 00:30:00" in msg
        assert datetime.date.today().isoformat() in msg

    def test_fatigue_is_capped_at_one_hundred(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        player = Character()
        player.fatigue = 95
        services.parse_garmin_gpx(player, build_gpx(ONE_MILE_POINTS))
        assert player.fatigue == 100


class TestStubbedParsers:
    def test_tcx_stub(self):
        assert services.parse_garmin_tcx(Character(), b"") == (True, "TCX module active")

    def test_sleep_csv_stub(self):
        assert services.parse_garmin_sleep_csv(Character(), b"") == (
            True,
            "Sleep CSV module active",
        )


class TestCalculateCharacterStats:
    def test_empty_history_starts_everyone_at_level_one(self):
        stats = services.calculate_character_stats([])
        assert stats["endurance"]["level"] == 1
        assert stats["pace"]["progress"] == 0.0
        assert stats["elevation_force"]["total"] == 0

    def test_non_dict_entries_are_skipped(self):
        stats = services.calculate_character_stats(["Day 1: ran somewhere"])
        assert stats["endurance"]["total"] == 0

    def test_endurance_points_include_long_run_bonus(self):
        short = services.calculate_character_stats(
            [{"Distance (Miles)": 9.0, "pace": 11.0}]
        )
        long_run = services.calculate_character_stats(
            [{"Distance (Miles)": 10.0, "pace": 11.0}]
        )
        assert short["endurance"]["total"] == 90
        assert long_run["endurance"]["total"] == 150

    def test_pace_points_reward_sub_seven_minute_miles(self):
        stats = services.calculate_character_stats(
            [{"Distance (Miles)": 5.0, "pace": 6.5}]
        )
        assert stats["pace"]["total"] == int((11.0 - 6.5) * 20) + 100

    def test_slow_pace_earns_no_pace_points(self):
        stats = services.calculate_character_stats(
            [{"Distance (Miles)": 5.0, "pace": 12.0}]
        )
        assert stats["pace"]["total"] == 0

    def test_elevation_points_strip_formatting_and_add_bonus(self):
        stats = services.calculate_character_stats(
            [{"Distance (Miles)": 5.0, "pace": 11.0, "Elevation (ft)": "+600 ft"}]
        )
        assert stats["elevation_force"]["total"] == 300 + 75

    def test_level_and_progress_are_bounded(self):
        stats = services.calculate_character_stats(
            [{"Distance (Miles)": 20.0, "pace": 6.0, "Elevation (ft)": "1200"}] * 10
        )
        for key in ("endurance", "pace", "elevation_force"):
            assert stats[key]["level"] >= 2
            assert 0.0 <= stats[key]["progress"] <= 1.0


class TestCalculateStatDecay:
    def test_empty_history_has_no_decay(self):
        assert services.calculate_stat_decay([]) == {
            "days_inactive": 0,
            "decay_penalty": 0,
            "applied": False,
        }

    def test_logs_without_dates_have_no_decay(self):
        assert services.calculate_stat_decay(["a string log"])["applied"] is False

    def test_recent_run_stays_inside_grace_period(self):
        recent = (datetime.date.today() - datetime.timedelta(days=3)).isoformat()
        result = services.calculate_stat_decay([{"Date": recent}])
        assert result == {"days_inactive": 3, "decay_penalty": 0, "applied": False}

    def test_inactivity_past_grace_period_costs_five_xp_per_day(self):
        stale = (datetime.date.today() - datetime.timedelta(days=12)).isoformat()
        result = services.calculate_stat_decay([{"Date": stale}])
        assert result == {"days_inactive": 12, "decay_penalty": 25, "applied": True}

    def test_latest_run_wins_over_older_entries(self):
        recent = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
        old = (datetime.date.today() - datetime.timedelta(days=90)).isoformat()
        assert services.calculate_stat_decay([{"Date": old}, {"Date": recent}])[
            "applied"
        ] is False


class TestMonthlyFitnessLoad:
    def test_empty_history_yields_empty_frame(self):
        assert services.calculate_monthly_fitness_load([]).empty

    def test_monthly_volumes_are_summed_per_month(self):
        logs = [
            {"Date": "2025-01-05", "Distance (Miles)": 5.0},
            {"Date": "2025-01-20", "Distance (Miles)": 7.0},
            {"Date": "2025-02-10", "Distance (Miles)": 3.0},
        ]
        monthly = services.calculate_monthly_fitness_load(logs)
        assert list(monthly["Distance"]) == [12.0, 3.0]
        assert list(monthly["Month_Label"]) == ["Jan 2025", "Feb 2025"]

    def test_chronic_fitness_uses_three_month_rolling_mean(self):
        logs = [
            {"Date": "2025-01-05", "Distance (Miles)": 30.0},
            {"Date": "2025-02-05", "Distance (Miles)": 0.0},
            {"Date": "2025-03-05", "Distance (Miles)": 0.0},
        ]
        monthly = services.calculate_monthly_fitness_load(logs)
        assert monthly["Chronic_Fitness"].iloc[-1] == pytest.approx(10.0)
        assert monthly["Performance_Status"].iloc[-1] == pytest.approx(10.0)

    def test_unparseable_distances_become_zero(self):
        monthly = services.calculate_monthly_fitness_load(
            [{"Date": "2025-01-05", "Distance (Miles)": "n/a"}]
        )
        assert monthly["Distance"].iloc[0] == 0.0


class TestLiveCombatStats:
    def _log(self, days_ago, miles, pace, elev):
        stamp = (datetime.date.today() - datetime.timedelta(days=days_ago)).isoformat()
        return {
            "Date": stamp,
            "Distance (Miles)": miles,
            "pace": pace,
            "Elevation (ft)": elev,
        }

    def test_no_history_returns_baseline_stats(self):
        stats = services.get_live_combat_stats([])
        assert stats["active_hp"] == 100
        assert stats["evasion_chance"] == 0.05
        assert stats["attack_power_modifier"] == 1.0

    def test_malformed_history_falls_back_to_defaults(self):
        assert services.get_live_combat_stats([{"Date": "2025-01-01"}])["active_hp"] == 100

    def test_recent_volume_expands_health_pool(self):
        logs = [self._log(d, 10.0, 9.0, "+100 ft") for d in (1, 5, 9)]
        stats = services.get_live_combat_stats(logs)
        assert stats["max_hp_bonus"] > 0
        assert stats["active_hp"] == 100 + stats["max_hp_bonus"]

    def test_fast_paces_raise_evasion_up_to_the_cap(self):
        slow = services.get_live_combat_stats([self._log(1, 10.0, 11.5, "0")])
        fast = services.get_live_combat_stats([self._log(1, 10.0, 6.0, "0")])
        assert fast["evasion_chance"] > slow["evasion_chance"]
        assert fast["evasion_chance"] <= 0.45

    def test_climbing_raises_attack_power(self):
        flat = services.get_live_combat_stats([self._log(1, 10.0, 9.0, "+0 ft")])
        hilly = services.get_live_combat_stats([self._log(1, 10.0, 9.0, "+4000 ft")])
        assert hilly["attack_power_modifier"] > flat["attack_power_modifier"]

    def test_endurance_modifier_is_bounded(self):
        logs = [self._log(d, 20.0, 8.0, "+500 ft") for d in range(1, 30)]
        assert 0.4 <= services.get_live_combat_stats(logs)["endurance_modifier"] <= 1.5
