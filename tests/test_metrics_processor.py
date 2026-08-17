# -*- coding: utf-8 -*-
"""Unit tests for the conversion helpers and guard clauses in metrics_processor.py."""
import json

import pytest

import metrics_processor


class TestCleanElevationString:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("+820.0 ft", 820),
            ("820", 820),
            (" +1,0 ft", 0),
            ("-350 ft", -350),
            ("", 0),
            ("not elevation", 0),
            (None, 0),
        ],
    )
    def test_strips_formatting_and_falls_back_to_zero(self, raw, expected):
        assert metrics_processor.clean_elevation_string(raw) == expected


class TestDecimalPaceToSeconds:
    @pytest.mark.parametrize(
        "pace,expected",
        [(8.82, 529), (7.0, 420), (0.0, 0), (0.5, 30), (10.999, 660)],
    )
    def test_converts_decimal_minutes_to_seconds(self, pace, expected):
        assert metrics_processor.decimal_pace_to_seconds(pace) == expected

    def test_invalid_input_returns_zero(self):
        assert metrics_processor.decimal_pace_to_seconds("fast") == 0
        assert metrics_processor.decimal_pace_to_seconds(None) == 0


class TestProcessAndAwardMetricsGuards:
    def test_missing_save_file_is_a_noop(self, tmp_path, monkeypatch, run_log):
        monkeypatch.setattr(metrics_processor, "SAVE_FILE", str(tmp_path / "absent.json"))
        assert metrics_processor.process_and_award_metrics(run_log) is None

    def test_save_file_without_metric_container_is_a_noop(
        self, tmp_path, monkeypatch, run_log
    ):
        save_file = tmp_path / "save_file.json"
        save_file.write_text(json.dumps({"gold": 50}), encoding="utf-8")
        monkeypatch.setattr(metrics_processor, "SAVE_FILE", str(save_file))

        assert metrics_processor.process_and_award_metrics(run_log) is None
        assert json.loads(save_file.read_text(encoding="utf-8")) == {"gold": 50}
