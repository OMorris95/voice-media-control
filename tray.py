"""System tray icon and menu using pystray."""

import logging
import threading

import pystray
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)

# Icon colors
COLORS = {
    "listening": "#22c55e",  # Green
    "paused": "#6b7280",     # Gray
    "error": "#ef4444"       # Red
}

ICON_SIZE = 64


def create_icon_image(color):
    """Create a simple colored circle icon."""
    image = Image.new('RGBA', (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Draw filled circle with slight padding
    padding = 4
    draw.ellipse(
        [padding, padding, ICON_SIZE - padding, ICON_SIZE - padding],
        fill=color
    )

    return image


class TrayApp:
    """System tray application with icon and menu."""

    def __init__(self, on_settings=None, on_toggle_pause=None, on_quit=None):
        """
        Initialize the tray app.

        Args:
            on_settings: Callback when Settings menu item is clicked
            on_toggle_pause: Callback when Pause/Resume is clicked
            on_quit: Callback when Quit is clicked
        """
        self.on_settings = on_settings
        self.on_toggle_pause = on_toggle_pause
        self.on_quit = on_quit

        self._status = "listening"
        self._icons = {
            status: create_icon_image(color)
            for status, color in COLORS.items()
        }

        self._icon = None
        self._menu_pause_item = None

    def _get_menu(self):
        """Build the tray menu."""
        is_paused = self._status == "paused"
        pause_text = "Resume Listening" if is_paused else "Pause Listening"

        return pystray.Menu(
            pystray.MenuItem("Settings", self._on_settings_click),
            pystray.MenuItem(pause_text, self._on_toggle_pause_click),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._on_quit_click)
        )

    def _on_settings_click(self, icon, item):
        """Handle Settings menu click."""
        if self.on_settings:
            # Run in separate thread to not block tray
            threading.Thread(target=self.on_settings, daemon=True).start()

    def _on_toggle_pause_click(self, icon, item):
        """Handle Pause/Resume menu click."""
        if self.on_toggle_pause:
            self.on_toggle_pause()

    def _on_quit_click(self, icon, item):
        """Handle Quit menu click."""
        if self.on_quit:
            self.on_quit()
        self.stop()

    def set_status(self, status):
        """
        Update the tray icon based on status.

        Args:
            status: One of 'listening', 'paused', 'error'
        """
        self._status = status
        if self._icon:
            self._icon.icon = self._icons.get(status, self._icons["listening"])
            # Update menu to reflect pause state
            self._icon.menu = self._get_menu()
            logger.debug(f"Tray status updated: {status}")

    def show_notification(self, title, message):
        """Show a Windows toast notification."""
        if self._icon:
            try:
                self._icon.notify(message, title)
                logger.debug(f"Notification shown: {title}")
            except Exception as e:
                logger.warning(f"Failed to show notification: {e}")

    def run(self):
        """Start the tray icon (blocks the calling thread)."""
        self._icon = pystray.Icon(
            name="VoiceMediaCtrl",
            icon=self._icons["listening"],
            title="Voice Media Controller",
            menu=self._get_menu()
        )

        logger.info("Starting system tray icon")
        self._icon.run()

    def run_detached(self):
        """Start the tray icon in a separate thread."""
        self._icon = pystray.Icon(
            name="VoiceMediaCtrl",
            icon=self._icons["listening"],
            title="Voice Media Controller",
            menu=self._get_menu()
        )

        thread = threading.Thread(target=self._icon.run, daemon=True)
        thread.start()
        logger.info("Started system tray icon (detached)")
        return thread

    def stop(self):
        """Stop and remove the tray icon."""
        if self._icon:
            self._icon.stop()
            logger.info("System tray icon stopped")
