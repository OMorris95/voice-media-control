"""Configuration management for Voice Media Controller."""

import json
import os
import sys


def get_app_dir():
    """Get the application directory (handles PyInstaller bundling)."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


CONFIG_PATH = os.path.join(get_app_dir(), 'config.json')

DEFAULT_CONFIG = {
    "wake_word_enabled": True,
    "wake_word": "hey music",
    "commands": {
        "next": ["next", "skip"],
        "back": ["back", "previous"],
        "pause": ["pause", "stop"],
        "play": ["play", "resume"]
    },
    "mic_device": None,
    "sensitivity": 0.5,
    "auto_start": False
}


def load_config():
    """Load config from file, merging with defaults for any missing keys."""
    config = DEFAULT_CONFIG.copy()

    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                user_config = json.load(f)

            # Merge user config into defaults
            for key, value in user_config.items():
                if key == "commands" and isinstance(value, dict):
                    # Merge commands dict
                    config["commands"] = {**DEFAULT_CONFIG["commands"], **value}
                else:
                    config[key] = value
        except (json.JSONDecodeError, IOError):
            # If config is corrupted, use defaults
            pass
    else:
        # First run - create config file with defaults
        save_config(config)

    return config


def save_config(config):
    """Save config to JSON file."""
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        return True
    except IOError:
        return False
