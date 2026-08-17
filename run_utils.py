# -*- coding: utf-8 -*-
"""
Shared utilities for the Cardio Training Hub app.

Central home for the save-file persistence helpers, pace/duration/elevation
parsers and unit conversion constants that were previously copy-pasted across
the UI modules and the batch import scripts.
"""
import json
import math
import os

SAVE_FILE = 'save_file.json'

# Locations checked when the app is launched from a nested working directory.
SAVE_FILE_SEARCH_PATHS = ['save_file.json', '../save_file.json', 'data/save_file.json']

# Imperial conversion factors used by the Garmin import pipelines.
METERS_TO_MILES = 0.000621371
METERS_TO_FEET = 3.28084
KM_TO_MILES = 0.62137119


def is_missing(value) -> bool:
    """True for None, empty strings and NaN floats (pandas-free ``pd.isna``)."""
    if value is None or value == "":
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return False


# ==========================================
# SAVE FILE PERSISTENCE
# ==========================================
def player_to_payload(player) -> dict:
    """Normalizes a Character instance (or plain dict-like object) for json.dump."""
    if isinstance(player, dict):
        return player
    if hasattr(player, 'to_dict'):
        return player.to_dict()
    return player.__dict__


def save_player_profile(player, path=SAVE_FILE) -> None:
    """Writes the player profile back to the json save database."""
    with open(path, 'w', encoding='utf-8') as db_file:
        json.dump(player_to_payload(player), db_file, default=str, indent=4)


def load_save_data(path=SAVE_FILE, default=None):
    """Reads a json save database, returning ``default`` when absent or corrupt."""
    if not os.path.exists(path):
        return default
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default


def load_history_logs(search_paths=None, on_error=None) -> list:
    """
    Returns the raw activity list from the first readable save file.

    Handles the three shapes the database has used over time: a dict with a
    top-level ``history_logs`` key, a dict nesting it one level down, or a bare
    list of activity records. ``on_error`` receives any read exception.
    """
    for path in (search_paths or SAVE_FILE_SEARCH_PATHS):
        if not os.path.exists(path):
            continue
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            if isinstance(data, dict):
                if "history_logs" in data:
                    return data["history_logs"]
                for root_key in data.values():
                    if isinstance(root_key, dict) and "history_logs" in root_key:
                        return root_key["history_logs"]
            elif isinstance(data, list):
                return data
        except Exception as e:
            if on_error:
                on_error(e)
    return []


# ==========================================
# PACE, DURATION & ELEVATION PARSERS
# ==========================================
def pace_str_to_minutes(pace_str):
    """Converts a pace string like '10:36' or a float number into total decimal minutes."""
    if is_missing(pace_str):
        return 0.0
    if isinstance(pace_str, (int, float)):
        return float(pace_str)
    try:
        parts = str(pace_str).strip().split(':')
        if len(parts) == 2:
            return int(parts[0]) + (int(parts[1]) / 60.0)
        return float(pace_str)
    except (ValueError, IndexError):
        return 0.0


def minutes_to_pace_str(decimal_minutes):
    """Converts decimal minutes back to a readable string format like '08:45'."""
    if is_missing(decimal_minutes) or decimal_minutes <= 0:
        return "—"
    minutes = int(decimal_minutes)
    seconds = int(round((decimal_minutes - minutes) * 60))
    if seconds == 60:
        minutes += 1
        seconds = 0
    return f"{minutes:02d}:{seconds:02d}"


def duration_str_to_minutes(d_str):
    """Converts 'HH:MM:SS' or 'MM:SS' clock strings into decimal minutes."""
    try:
        parts = [int(p) for p in str(d_str).strip().split(':')]
        if len(parts) == 3:
            return parts[0] * 60 + parts[1] + parts[2] / 60.0
        elif len(parts) == 2:
            return parts[0] + parts[1] / 60.0
        return 0.0
    except Exception:
        return 0.0


def pace_to_seconds(pace_str: str) -> int:
    """Converts a pace string 'MM:SS' into total raw seconds."""
    try:
        parts = pace_str.strip().split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        return 0
    except (ValueError, AttributeError):
        return 0


def decimal_pace_to_seconds(decimal_pace: float) -> int:
    """Converts a decimal pace float (like 8.82) into raw total seconds."""
    try:
        minutes = int(decimal_pace)
        seconds = int(round((decimal_pace - minutes) * 60))
        return (minutes * 60) + seconds
    except (ValueError, TypeError):
        return 0


def calculate_split_variance(splits_list, total_distance: float) -> float:
    """
    Drops the first split (warm-up mile) and calculates the delta
    between the slowest and fastest remaining miles.
    Returns variance in seconds, or -1.0 if ineligible.
    """
    if total_distance < 3.0 or len(splits_list) < 3:
        return -1.0

    remaining_splits = splits_list[1:]
    splits_in_seconds = [pace_to_seconds(s) for s in remaining_splits if pace_to_seconds(s) > 0]
    if not splits_in_seconds:
        return -1.0

    return float(max(splits_in_seconds) - min(splits_in_seconds))


def calculate_final_kick(avg_pace_str: str, final_mile_str: str) -> float:
    """
    Calculates what percentage faster the final mile was compared to the average pace.
    Formula: (Avg Pace Seconds - Final Mile Seconds) / Avg Pace Seconds * 100
    """
    avg_seconds = pace_to_seconds(avg_pace_str)
    final_seconds = pace_to_seconds(final_mile_str)
    if avg_seconds <= 0 or final_seconds <= 0:
        return 0.0

    kick_percent = ((avg_seconds - final_seconds) / avg_seconds) * 100.0
    return round(kick_percent, 2)


def clean_elevation_string(elev_str: str) -> int:
    """Strips formatting symbols '+', 'ft', and whitespace to return a clean integer."""
    try:
        cleaned = elev_str.replace("+", "").replace("ft", "").strip()
        return int(float(cleaned))
    except (ValueError, AttributeError):
        return 0
