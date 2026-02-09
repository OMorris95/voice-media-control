"""Settings popup window using tkinter."""

import logging
import sys
import tkinter as tk
from tkinter import ttk, messagebox

from config import save_config
from listener import get_available_mics

logger = logging.getLogger(__name__)

# Windows registry key for startup
STARTUP_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "VoiceMediaController"


def add_to_startup():
    """Add app to Windows startup registry."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            STARTUP_REG_KEY,
            0,
            winreg.KEY_SET_VALUE
        )
        # Get path to executable or script
        if getattr(sys, 'frozen', False):
            exe_path = sys.executable
        else:
            exe_path = f'pythonw "{sys.argv[0]}"'
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)
        logger.info("Added to Windows startup")
        return True
    except Exception as e:
        logger.error(f"Failed to add to startup: {e}")
        return False


def remove_from_startup():
    """Remove app from Windows startup registry."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            STARTUP_REG_KEY,
            0,
            winreg.KEY_SET_VALUE
        )
        try:
            winreg.DeleteValue(key, APP_NAME)
        except FileNotFoundError:
            pass  # Already not in startup
        winreg.CloseKey(key)
        logger.info("Removed from Windows startup")
        return True
    except Exception as e:
        logger.error(f"Failed to remove from startup: {e}")
        return False


class SettingsWindow:
    """Tkinter settings popup window."""

    def __init__(self, config, on_save=None):
        """
        Initialize settings window.

        Args:
            config: Current config dict
            on_save: Callback(new_config) when settings are saved
        """
        self.config = config.copy()
        self.on_save = on_save

        self.window = None
        self._mic_devices = []

        # Tkinter variables (initialized in _create_widgets)
        self.wake_enabled_var = None
        self.sensitivity_var = None
        self.auto_start_var = None

    def show(self):
        """Show the settings window."""
        if self.window is not None:
            try:
                self.window.lift()
                self.window.focus_force()
                return
            except tk.TclError:
                pass

        self.window = tk.Tk()
        self.window.title("Voice Media Controller Settings")
        self.window.resizable(False, False)

        # Get available mics
        self._mic_devices = get_available_mics()

        self._create_widgets()
        self._load_values()

        # Center window on screen
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"+{x}+{y}")

        self.window.mainloop()

    def _create_widgets(self):
        """Create all the widgets."""
        frame = ttk.Frame(self.window, padding=15)
        frame.grid(row=0, column=0, sticky="nsew")

        row = 0

        # Wake Word Section
        ttk.Label(frame, text="Wake Word", font=("", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 5)
        )
        row += 1

        self.wake_enabled_var = tk.BooleanVar()
        ttk.Checkbutton(
            frame, text="Enable wake word",
            variable=self.wake_enabled_var
        ).grid(row=row, column=0, columnspan=2, sticky="w")
        row += 1

        ttk.Label(frame, text="Wake word:").grid(row=row, column=0, sticky="w", pady=2)
        self.wake_word_entry = ttk.Entry(frame, width=30)
        self.wake_word_entry.grid(row=row, column=1, sticky="w", pady=2)
        row += 1

        # Commands Section
        ttk.Separator(frame, orient="horizontal").grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=10
        )
        row += 1

        ttk.Label(frame, text="Commands (comma-separated)", font=("", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 5)
        )
        row += 1

        self.command_entries = {}
        for cmd in ["next", "back", "pause", "play"]:
            ttk.Label(frame, text=f"{cmd.capitalize()}:").grid(
                row=row, column=0, sticky="w", pady=2
            )
            entry = ttk.Entry(frame, width=30)
            entry.grid(row=row, column=1, sticky="w", pady=2)
            self.command_entries[cmd] = entry
            row += 1

        # Microphone Section
        ttk.Separator(frame, orient="horizontal").grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=10
        )
        row += 1

        ttk.Label(frame, text="Microphone", font=("", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 5)
        )
        row += 1

        ttk.Label(frame, text="Device:").grid(row=row, column=0, sticky="w", pady=2)
        self.mic_combo = ttk.Combobox(frame, width=27, state="readonly")
        mic_names = ["Default"] + [d['name'] for d in self._mic_devices]
        self.mic_combo['values'] = mic_names
        self.mic_combo.grid(row=row, column=1, sticky="w", pady=2)
        row += 1

        # Sensitivity Section
        ttk.Separator(frame, orient="horizontal").grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=10
        )
        row += 1

        ttk.Label(frame, text="Sensitivity", font=("", 10, "bold")).grid(
            row=row, column=0, columnspan=2, sticky="w", pady=(0, 5)
        )
        row += 1

        self.sensitivity_var = tk.DoubleVar()
        sensitivity_frame = ttk.Frame(frame)
        sensitivity_frame.grid(row=row, column=0, columnspan=2, sticky="ew")
        ttk.Label(sensitivity_frame, text="Low").pack(side="left")
        self.sensitivity_scale = ttk.Scale(
            sensitivity_frame,
            from_=0.0,
            to=1.0,
            orient="horizontal",
            variable=self.sensitivity_var,
            length=200
        )
        self.sensitivity_scale.pack(side="left", padx=5)
        ttk.Label(sensitivity_frame, text="High").pack(side="left")
        row += 1

        # Auto-start Section
        ttk.Separator(frame, orient="horizontal").grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=10
        )
        row += 1

        self.auto_start_var = tk.BooleanVar()
        ttk.Checkbutton(
            frame, text="Start with Windows",
            variable=self.auto_start_var
        ).grid(row=row, column=0, columnspan=2, sticky="w")
        row += 1

        # Buttons
        ttk.Separator(frame, orient="horizontal").grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=10
        )
        row += 1

        button_frame = ttk.Frame(frame)
        button_frame.grid(row=row, column=0, columnspan=2, sticky="e")

        ttk.Button(button_frame, text="Cancel", command=self._on_cancel).pack(
            side="left", padx=5
        )
        ttk.Button(button_frame, text="Save", command=self._on_save).pack(
            side="left"
        )

    def _load_values(self):
        """Load current config values into widgets."""
        self.wake_enabled_var.set(self.config.get("wake_word_enabled", True))
        self.wake_word_entry.insert(0, self.config.get("wake_word", "hey music"))

        commands = self.config.get("commands", {})
        for cmd, entry in self.command_entries.items():
            triggers = commands.get(cmd, [])
            entry.insert(0, ", ".join(triggers))

        # Set mic dropdown
        mic_device = self.config.get("mic_device")
        if mic_device is None:
            self.mic_combo.current(0)
        else:
            # Find matching device
            for i, device in enumerate(self._mic_devices):
                if device['index'] == mic_device:
                    self.mic_combo.current(i + 1)  # +1 for "Default"
                    break
            else:
                self.mic_combo.current(0)

        self.sensitivity_var.set(self.config.get("sensitivity", 0.5))
        self.auto_start_var.set(self.config.get("auto_start", False))

    def _on_save(self):
        """Save settings and close window."""
        # Build new config
        new_config = {
            "wake_word_enabled": self.wake_enabled_var.get(),
            "wake_word": self.wake_word_entry.get().strip(),
            "commands": {},
            "mic_device": None,
            "sensitivity": self.sensitivity_var.get(),
            "auto_start": self.auto_start_var.get()
        }

        # Parse commands
        for cmd, entry in self.command_entries.items():
            text = entry.get().strip()
            if text:
                triggers = [t.strip() for t in text.split(",") if t.strip()]
                new_config["commands"][cmd] = triggers
            else:
                new_config["commands"][cmd] = []

        # Get selected mic
        mic_index = self.mic_combo.current()
        if mic_index > 0 and mic_index <= len(self._mic_devices):
            new_config["mic_device"] = self._mic_devices[mic_index - 1]['index']

        # Handle auto-start
        if new_config["auto_start"] and not self.config.get("auto_start"):
            add_to_startup()
        elif not new_config["auto_start"] and self.config.get("auto_start"):
            remove_from_startup()

        # Save to file
        if save_config(new_config):
            logger.info("Settings saved")
            if self.on_save:
                self.on_save(new_config)
            self._close()
        else:
            messagebox.showerror("Error", "Failed to save settings")

    def _on_cancel(self):
        """Close window without saving."""
        self._close()

    def _close(self):
        """Close the window."""
        if self.window:
            # Clear variable references before destroying to avoid threading issues
            self.wake_enabled_var = None
            self.sensitivity_var = None
            self.auto_start_var = None
            self.window.quit()
            self.window.destroy()
            self.window = None
