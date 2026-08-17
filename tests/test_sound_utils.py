# -*- coding: utf-8 -*-
"""Unit tests for the cross-platform beep helper in sound_utils.py."""
import pytest

import sound_utils

EVENT_TONES = {
    "success": 1,
    "levelup": 4,
    "upgrade": 2,
    "buy_gear": 2,
    "boss_victory": 2,
    "loot": 2,
    "boss_defeat": 2,
    "error": 1,
}


class FakeWinsound:
    def __init__(self):
        self.beeps = []

    def Beep(self, frequency, duration):
        self.beeps.append((frequency, duration))


@pytest.fixture
def fake_winsound(monkeypatch):
    fake = FakeWinsound()
    monkeypatch.setattr(sound_utils, "winsound", fake)
    return fake


@pytest.mark.parametrize("event,expected_beeps", sorted(EVENT_TONES.items()))
def test_each_event_emits_its_tone_sequence(fake_winsound, event, expected_beeps):
    sound_utils.play_sound(event)
    assert len(fake_winsound.beeps) == expected_beeps


def test_unknown_event_is_silent(fake_winsound):
    sound_utils.play_sound("nonexistent_event")
    assert fake_winsound.beeps == []


def test_without_winsound_falls_back_to_terminal_bell(monkeypatch, capsys):
    monkeypatch.setattr(sound_utils, "winsound", None)
    sound_utils.play_sound("levelup")
    assert capsys.readouterr().out == "\a"
