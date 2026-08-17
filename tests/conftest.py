# -*- coding: utf-8 -*-
"""Shared fixtures and import path setup for the unit test suite."""
import os
import sys

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


@pytest.fixture
def run_log():
    """A representative history_logs entry as produced by the upload pipeline."""
    return {
        "Date": "2025-05-04",
        "Name": "morning_run.fit",
        "Distance (Miles)": 6.50,
        "Duration": "00:45:30",
        "pace": 7.00,
        "Elevation (ft)": "+820.0 ft",
        "splits": [
            {"split_num": 1, "distance_mi": 1.0, "time": "07:30", "pace": "07:30"},
            {"split_num": 2, "distance_mi": 1.0, "time": "07:10", "pace": "07:10"},
            {"split_num": 3, "distance_mi": 1.0, "time": "07:05", "pace": "07:05"},
            {"split_num": 4, "distance_mi": 1.0, "time": "06:40", "pace": "06:40"},
        ],
    }


@pytest.fixture
def save_profile():
    """A minimal save_file.json payload containing the metric containers."""
    return {
        "unlocked_badges": [],
        "history_logs": [],
        "lifetime_elevation_gain": 0.0,
        "final_metric_data": {
            "lifetime_odometer_miles": 0.0,
            "lifetime_calories_burned": 0,
            "trophy_cabinet": {
                "shelf_a_mileage": [],
                "shelf_b_elevation": [],
                "shelf_c_calories": [],
                "prestige_loops": {
                    "mileage_loops_count": 0,
                    "elevation_loops_count": 0,
                    "calorie_loops_count": 0,
                },
            },
        },
    }
