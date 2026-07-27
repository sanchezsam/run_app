# -*- coding: utf-8 -*-
import sys

try:
    import winsound
except ImportError:
    winsound = None

def play_sound(sound_type):
    """Plays system tones based on game events without external assets."""
    if winsound:
        if sound_type == "success": winsound.Beep(523, 150)
        elif sound_type == "levelup":
            winsound.Beep(523, 100); winsound.Beep(659, 100)
            winsound.Beep(784, 100); winsound.Beep(1046, 300)
        elif sound_type == "upgrade": winsound.Beep(587, 100); winsound.Beep(880, 250)
        elif sound_type == "buy_gear": winsound.Beep(784, 80); winsound.Beep(1175, 200)
        elif sound_type == "boss_victory": winsound.Beep(523, 100); winsound.Beep(1046, 400)
        elif sound_type == "loot": winsound.Beep(880, 80); winsound.Beep(1318, 300)
        elif sound_type == "boss_defeat": winsound.Beep(293, 200); winsound.Beep(220, 500)
        elif sound_type == "error": winsound.Beep(220, 400)
    else:
        sys.stdout.write("\a")
        sys.stdout.flush()

