"""
Audio management for music and sound effects.
"""

import pygame
import os
import traceback

def init_audio():
    """Initialize the audio mixer."""
    try:
        try:
            pygame.mixer.quit()
        except Exception:
            pass
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        print("DEBUG: pygame.mixer initialized (44100Hz, 16-bit, stereo)")
    except Exception as ex:
        print("DEBUG: pygame.mixer.init() failed:", ex)
        traceback.print_exc()


def _music_exists(path):
    """Check if music file exists."""
    exists = os.path.isfile(path)
    print(f"DEBUG: music exists check: {path} -> {exists}")
    return exists


def play_music(path, loop=-1, volume=0.5):
    """Play music from the given path."""
    try:
        if _music_exists(path):
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(loop)
            print(f"DEBUG: playing music: {path} (loop={loop}, vol={volume})")
            return True
        else:
            print(f"DEBUG: play_music: file not found: {path}")
    except Exception as ex:
        print(f"DEBUG: play_music failed for {path}: {ex}")
        traceback.print_exc()
    return False


def stop_music():
    """Stop currently playing music."""
    try:
        pygame.mixer.music.stop()
        print("DEBUG: music stopped")
    except Exception as ex:
        print("DEBUG: stop_music failed:", ex)
        traceback.print_exc()