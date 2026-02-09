"""Voice Media Controller - Entry Point."""

import logging
import os
import sys

from config import load_config, get_app_dir
from listener import VoiceListener
from tray import TrayApp
from settings import SettingsWindow

# Setup logging
LOG_FILE = os.path.join(get_app_dir(), 'voice_media_ctrl.log')

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class VoiceMediaController:
    """Main application class that coordinates all components."""

    def __init__(self):
        self.config = None
        self.listener = None
        self.tray = None
        self.settings_window = None

    def run(self):
        """Start the application."""
        logger.info("Starting Voice Media Controller")

        # Load config
        self.config = load_config()
        logger.info("Configuration loaded")

        # Create listener
        self.listener = VoiceListener(
            config=self.config,
            on_command=self._on_command,
            on_error=self._on_error,
            on_status=self._on_status
        )

        # Create tray app
        self.tray = TrayApp(
            on_settings=self._on_settings,
            on_toggle_pause=self._on_toggle_pause,
            on_quit=self._on_quit
        )

        # Start listening
        if not self.listener.start():
            logger.error("Failed to start voice listener")
            self.tray.set_status("error")
        else:
            logger.info("Voice listener started")

        # Run tray (blocks main thread)
        self.tray.run()

    def _on_command(self, action):
        """Called when a voice command is matched and executed."""
        logger.info(f"Command executed: {action}")
        self.tray.show_notification("Voice Media Controller", f"Command: {action}")

    def _on_error(self, message):
        """Called when an error occurs in the listener."""
        logger.error(f"Listener error: {message}")
        self.tray.set_status("error")
        self.tray.show_notification("Voice Media Controller - Error", message)

    def _on_status(self, status):
        """Called when listener status changes."""
        self.tray.set_status(status)

    def _on_settings(self):
        """Open settings window."""
        logger.debug("Opening settings window")
        self.settings_window = SettingsWindow(
            config=self.config,
            on_save=self._on_settings_save
        )
        self.settings_window.show()

    def _on_settings_save(self, new_config):
        """Called when settings are saved."""
        logger.info("Applying new configuration")
        self.config = new_config
        self.listener.reload_config(new_config)

    def _on_toggle_pause(self):
        """Toggle pause/resume listening."""
        if self.listener.is_paused():
            self.listener.resume()
            logger.info("Listening resumed")
        else:
            self.listener.pause()
            logger.info("Listening paused")

    def _on_quit(self):
        """Clean up and quit the application."""
        logger.info("Shutting down")
        if self.listener:
            self.listener.stop()


def main():
    """Entry point."""
    app = VoiceMediaController()
    try:
        app.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        raise
    finally:
        logger.info("Voice Media Controller stopped")


if __name__ == "__main__":
    main()
