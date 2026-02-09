"""Command matching and media key simulation."""

import logging
from pynput.keyboard import Key, Controller

logger = logging.getLogger(__name__)

keyboard = Controller()

# Map action names to pynput media keys
MEDIA_KEYS = {
    "next": Key.media_next,
    "back": Key.media_previous,
    "pause": Key.media_play_pause,
    "play": Key.media_play_pause
}


def send_media_key(action):
    """Send a media key press for the given action."""
    key = MEDIA_KEYS.get(action)
    if key:
        try:
            keyboard.press(key)
            keyboard.release(key)
            logger.info(f"Sent media key: {action}")
            return True
        except Exception as e:
            logger.error(f"Failed to send media key {action}: {e}")
            return False
    return False


def match_command(text, config):
    """
    Match recognized text against configured commands.

    Args:
        text: Recognized speech text (lowercase)
        config: Config dict with wake_word_enabled, wake_word, and commands

    Returns:
        Action name ('next', 'back', 'pause', 'play') or None if no match
    """
    text = text.lower().strip()

    if not text:
        return None

    # Check wake word if enabled
    if config.get("wake_word_enabled", True):
        wake_word = config.get("wake_word", "hey music").lower()
        if wake_word not in text:
            return None
        # Remove wake word from text for command matching
        text = text.replace(wake_word, "").strip()

    # Match against command words
    commands = config.get("commands", {})
    for action, triggers in commands.items():
        for trigger in triggers:
            if trigger.lower() in text:
                logger.debug(f"Matched command: '{trigger}' -> {action}")
                return action

    return None
