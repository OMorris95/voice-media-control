# Voice Media Controller — Project Plan

A lightweight Python app that lets you control media (YouTube, Spotify, etc.) with voice commands. Runs in the system tray on Windows.

---

## Tech Stack

- **Python 3.11+**
- **Vosk** — offline speech recognition (small english model ~50MB)
- **sounddevice** — mic input
- **pynput** — simulate media keys
- **pystray + Pillow** — system tray icon & menu
- **tkinter** — small settings popup (built into Python, no extra dependency)
- **json** — settings saved to a `config.json` file

---

## File Structure

```
voice-media-ctrl/
├── main.py          # Entry point, starts tray + listener
├── listener.py      # Mic input → Vosk → command matching
├── commands.py      # Maps recognized words → media key actions
├── settings.py      # Tkinter settings popup window
├── config.py        # Load/save config.json, defaults
├── tray.py          # System tray icon, menu, status
├── config.json      # User settings (generated on first run)
└── model/           # Vosk model folder (small EN model)
```

---

## Default Config (config.json)

```json
{
  "wake_word_enabled": true,
  "wake_word": "hey music",
  "commands": {
    "next": ["next", "skip"],
    "back": ["back", "previous"],
    "pause": ["pause", "stop"],
    "play": ["play", "resume"]
  },
  "mic_device": null,
  "sensitivity": 0.5,
  "auto_start": false
}
```

---

## How It Works (Pipeline)

1. **main.py** loads config, starts tray icon, starts listener in a background thread
2. **listener.py** opens mic stream via `sounddevice`, feeds audio chunks to Vosk
3. Vosk returns recognized text → **commands.py** checks for wake word (if enabled), then matches against command words
4. On match → `pynput` sends the corresponding media key:
   - `VK_MEDIA_NEXT_TRACK`
   - `VK_MEDIA_PLAY_PAUSE`
   - `VK_MEDIA_PREV_TRACK`
5. Tray icon shows status (listening / paused), right-click menu has: Settings, Pause Listening, Quit

---

## Settings Popup (tkinter)

Single small window with:

- Wake word toggle checkbox + text field
- Command words: 4 text fields (next/back/pause/play) accepting comma-separated aliases
- Mic dropdown (enumerate available devices via `sounddevice`)
- Sensitivity slider
- Auto-start checkbox (adds/removes from Windows startup registry)
- Save button → writes to `config.json`, hot-reloads listener

---

## Build Order

1. **config.py** — load/save/defaults
2. **commands.py** — word-to-action mapping + media key sending
3. **listener.py** — mic → vosk → command matching loop
4. **main.py** — wire it up, confirm it works in terminal
5. **tray.py** — system tray icon with menu
6. **settings.py** — tkinter popup
7. Auto-start registry logic
8. Test & polish

---

## Packaging (optional later)

- **PyInstaller** one-file `.exe` so it runs without Python installed
- Bundle Vosk model inside the exe or alongside it
