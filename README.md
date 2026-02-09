# Voice Media Controller

A lightweight Python app that lets you control media (YouTube, Spotify, etc.) with voice commands. Runs in the Windows system tray.

## Features

- Offline speech recognition (no internet required)
- Wake word activation ("hey music" by default)
- Control: play, pause, next track, previous track
- System tray with pause/resume and settings
- Customizable commands and wake word
- Auto-start with Windows option

## Requirements

- Windows 10/11
- Python 3.11+
- Microphone

## Installation

1. Clone or download this repository

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:
   ```bash
   python main.py
   ```

## Usage

A green circle appears in your system tray. Right-click for options:
- **Settings** - Configure wake word, commands, microphone
- **Pause/Resume** - Toggle listening
- **Quit** - Exit the app

### Voice Commands

With wake word enabled (default):
- "hey music next" - Skip to next track
- "hey music back" - Previous track
- "hey music pause" - Pause playback
- "hey music play" - Resume playback

Disable wake word in settings to use commands directly ("next", "pause", etc.)

## Configuration

Settings are saved to `config.json`. You can edit commands, add aliases, change the wake word, and select your microphone.

## Building as Executable

Create a standalone `.exe` with PyInstaller:
```bash
pip install pyinstaller
pyinstaller --onefile --noconsole --add-data "model;model" --name "VoiceMediaController" main.py
```

The exe will be in the `dist/` folder.

## Troubleshooting

- **No response to voice**: Check that your microphone is selected in Settings
- **Wrong commands triggered**: Try adjusting sensitivity or using more distinct command words
- **Red tray icon**: Check `voice_media_ctrl.log` for errors

## Credits

Speech recognition powered by [Vosk](https://alphacephei.com/vosk/) (Apache 2.0 License)
