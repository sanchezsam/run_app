# -*- coding: utf-8 -*-
"""Unit tests for the patch/trophy award pipeline in upload_ui.py."""
import json

import pytest

import upload_ui
from metrics_config import FINAL_METRIC_CONFIG


class TestPaceToSeconds:
    @pytest.mark.parametrize(
        "raw,expected",
        [("07:30", 450), (" 6:45 ", 405), ("00:00", 0), ("7:30:00", 0), ("fast", 0), (None, 0)],
    )
    def test_parses_mm_ss_strings(self, raw, expected):
        assert upload_ui.pace_to_seconds(raw) == expected


class TestSplitVariance:
    def test_short_runs_are_ineligible(self):
        assert upload_ui.calculate_split_variance(["07:00", "07:10", "07:20"], 2.0) == -1.0

    def test_too_few_splits_are_ineligible(self):
        assert upload_ui.calculate_split_variance(["07:00", "07:10"], 6.0) == -1.0

    def test_warm_up_mile_is_excluded_from_the_spread(self):
        splits = ["09:00", "07:00", "07:10", "07:20"]
        assert upload_ui.calculate_split_variance(splits, 4.0) == 20.0

    def test_unparseable_splits_are_ignored(self):
        assert upload_ui.calculate_split_variance(["09:00", "bad", "oops"], 4.0) == -1.0

    def test_even_pacing_reports_zero_variance(self):
        assert upload_ui.calculate_split_variance(["08:00", "07:30", "07:30"], 3.0) == 0.0


class TestFinalKick:
    def test_faster_final_mile_returns_positive_percentage(self):
        assert upload_ui.calculate_final_kick("08:00", "07:20") == pytest.approx(8.33)

    def test_slower_final_mile_returns_negative_percentage(self):
        assert upload_ui.calculate_final_kick("07:00", "07:30") < 0

    def test_missing_or_zero_paces_return_zero(self):
        assert upload_ui.calculate_final_kick("00:00", "07:30") == 0.0
        assert upload_ui.calculate_final_kick("07:30", "") == 0.0


class TestCleanElevationAndPaceHelpers:
    def test_clean_elevation_string(self):
        assert upload_ui.clean_elevation_string("+1,445 ft") == 0
        assert upload_ui.clean_elevation_string("+1445 ft") == 1445
        assert upload_ui.clean_elevation_string(None) == 0

    def test_decimal_pace_to_seconds(self):
        assert upload_ui.decimal_pace_to_seconds(6.5) == 390
        assert upload_ui.decimal_pace_to_seconds("slow") == 0


class TestCheckSingleRunPatches:
    def _pillars(self, patches):
        return {p["pillar"]: p["id"] for p in patches}

    def test_empty_payload_earns_nothing_from_pace_pillar(self):
        pillars = self._pillars(upload_ui.check_single_run_patches({}))
        assert "pillar_1_velocity" not in pillars

    def test_velocity_pillar_tiers_are_inverted_ranges(self):
        pillars = self._pillars(
            upload_ui.check_single_run_patches({"Distance (Miles)": 5.0, "pace": 6.30})
        )
        assert pillars["pillar_1_velocity"] == "deer"

    def test_elevation_pillar_awards_matching_tier(self):
        pillars = self._pillars(
            upload_ui.check_single_run_patches(
                {"Distance (Miles)": 5.0, "pace": 9.0, "Elevation (ft)": "+800 ft"}
            )
        )
        assert pillars["pillar_2_elevation"] == "bighorn"

    def test_volume_pillar_awards_long_run_tier(self):
        pillars = self._pillars(
            upload_ui.check_single_run_patches({"Distance (Miles)": 16.0, "pace": 9.0})
        )
        assert pillars["pillar_4_volume"] == "endurance_laurel"

    def test_consistency_pillar_requires_minimum_distance(self, run_log):
        short = dict(run_log)
        short["Distance (Miles)"] = 2.0
        pillars = self._pillars(upload_ui.check_single_run_patches(short))
        assert "pillar_5_consistency" not in pillars

    def test_final_kick_pillar_uses_splits(self, run_log):
        pillars = self._pillars(upload_ui.check_single_run_patches(run_log))
        assert "pillar_3_strategy" in pillars

    def test_missing_pace_skips_pace_dependent_pillars(self):
        pillars = self._pillars(
            upload_ui.check_single_run_patches(
                {"Distance (Miles)": 8.0, "pace": None, "Elevation (ft)": "+400 ft"}
            )
        )
        assert "pillar_1_velocity" not in pillars
        assert pillars["pillar_2_elevation"] == "marmot"

    def test_non_list_splits_payload_is_tolerated(self):
        patches = upload_ui.check_single_run_patches(
            {"Distance (Miles)": 8.0, "pace": 8.0, "splits": "corrupted"}
        )
        assert isinstance(patches, list)

    def test_alternate_field_names_are_supported(self):
        pillars = self._pillars(
            upload_ui.check_single_run_patches({"dist": 7.0, "ele": "+900 ft", "pace": 8.0})
        )
        assert pillars["pillar_2_elevation"] == "bighorn"
        assert pillars["pillar_4_volume"] == "stride_tracker"


class TestProcessAndAwardMetrics:
    def _write_save(self, tmp_path, profile):
        path = tmp_path / "save_file.json"
        path.write_text(json.dumps(profile), encoding="utf-8")
        return path

    def _read_save(self, tmp_path):
        return json.loads((tmp_path / "save_file.json").read_text(encoding="utf-8"))

    def test_missing_save_file_is_a_noop(self, tmp_path, monkeypatch, run_log):
        monkeypatch.chdir(tmp_path)
        assert upload_ui.process_and_award_metrics(run_log) is None

    def test_profile_without_metric_container_is_untouched(
        self, tmp_path, monkeypatch, run_log
    ):
        monkeypatch.chdir(tmp_path)
        self._write_save(tmp_path, {"gold": 10})
        upload_ui.process_and_award_metrics(run_log)
        assert self._read_save(tmp_path) == {"gold": 10}

    def test_run_is_appended_with_patches_and_odometers_tick_up(
        self, tmp_path, monkeypatch, run_log, save_profile
    ):
        monkeypatch.chdir(tmp_path)
        self._write_save(tmp_path, save_profile)

        upload_ui.process_and_award_metrics(dict(run_log))
        saved = self._read_save(tmp_path)

        assert len(saved["history_logs"]) == 1
        assert saved["history_logs"][0]["earned_patches"]
        assert saved["unlocked_badges"]
        assert saved["final_metric_data"]["lifetime_odometer_miles"] == 6.5
        assert saved["final_metric_data"]["lifetime_calories_burned"] == 650
        assert saved["lifetime_elevation_gain"] == 820.0

    def test_duplicate_run_is_not_appended_twice(
        self, tmp_path, monkeypatch, run_log, save_profile
    ):
        monkeypatch.chdir(tmp_path)
        self._write_save(tmp_path, save_profile)

        upload_ui.process_and_award_metrics(dict(run_log))
        upload_ui.process_and_award_metrics(dict(run_log))

        assert len(self._read_save(tmp_path)["history_logs"]) == 1

    def test_mileage_trophies_unlock_at_configured_thresholds(
        self, tmp_path, monkeypatch, run_log, save_profile
    ):
        monkeypatch.chdir(tmp_path)
        first_trophy = FINAL_METRIC_CONFIG["trophy_cabinet"]["shelf_a_mileage"]["trophies"][0]
        save_profile["final_metric_data"]["lifetime_odometer_miles"] = (
            first_trophy["threshold"] - 1.0
        )
        self._write_save(tmp_path, save_profile)

        upload_ui.process_and_award_metrics(dict(run_log))
        cabinet = self._read_save(tmp_path)["final_metric_data"]["trophy_cabinet"]
        assert first_trophy["id"] in cabinet["shelf_a_mileage"]

    def test_elevation_and_calorie_shelves_unlock(
        self, tmp_path, monkeypatch, run_log, save_profile
    ):
        monkeypatch.chdir(tmp_path)
        elev_trophy = FINAL_METRIC_CONFIG["trophy_cabinet"]["shelf_b_elevation"]["trophies"][0]
        cal_trophy = FINAL_METRIC_CONFIG["trophy_cabinet"]["shelf_c_calories"]["trophies"][0]
        save_profile["lifetime_elevation_gain"] = float(elev_trophy["threshold"])
        save_profile["final_metric_data"]["lifetime_calories_burned"] = cal_trophy["threshold"]
        self._write_save(tmp_path, save_profile)

        upload_ui.process_and_award_metrics(dict(run_log))
        cabinet = self._read_save(tmp_path)["final_metric_data"]["trophy_cabinet"]
        assert elev_trophy["id"] in cabinet["shelf_b_elevation"]
        assert cal_trophy["id"] in cabinet["shelf_c_calories"]

    def test_prestige_loops_count_past_the_baselines(
        self, tmp_path, monkeypatch, run_log, save_profile
    ):
        monkeypatch.chdir(tmp_path)
        cabinet_cfg = FINAL_METRIC_CONFIG["trophy_cabinet"]
        save_profile["final_metric_data"]["lifetime_odometer_miles"] = 3000.0
        save_profile["lifetime_elevation_gain"] = 160000.0
        save_profile["final_metric_data"]["lifetime_calories_burned"] = 160000
        self._write_save(tmp_path, save_profile)

        upload_ui.process_and_award_metrics(dict(run_log))
        loops = self._read_save(tmp_path)["final_metric_data"]["trophy_cabinet"]["prestige_loops"]

        assert loops["mileage_loops_count"] == int(
            (3006.5 - 2000) // cabinet_cfg["shelf_a_mileage"]["loop_increment"]
        )
        assert loops["elevation_loops_count"] == int(
            (160820.0 - 100000) // cabinet_cfg["shelf_b_elevation"]["loop_increment"]
        )
        assert loops["calorie_loops_count"] == int(
            (160650 - 100000) // cabinet_cfg["shelf_c_calories"]["loop_increment"]
        )

    def test_badges_are_not_duplicated_across_runs(
        self, tmp_path, monkeypatch, run_log, save_profile
    ):
        monkeypatch.chdir(tmp_path)
        self._write_save(tmp_path, save_profile)

        upload_ui.process_and_award_metrics(dict(run_log))
        second = dict(run_log)
        second["Date"] = "2025-05-05"
        upload_ui.process_and_award_metrics(second)

        badges = self._read_save(tmp_path)["unlocked_badges"]
        assert len(badges) == len(set(badges))
