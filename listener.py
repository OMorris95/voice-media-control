"""Voice listener using Vosk for speech recognition."""

import json
import logging
import os
import queue
import sys
import threading

import sounddevice as sd
from vosk import Model, KaldiRecognizer

from commands import match_command, send_media_key

logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000


def get_model_path():
    """Get the Vosk model path (handles PyInstaller bundling)."""
    if getattr(sys, 'frozen', False):
        # Running as bundled exe - model is in _MEIPASS
        return os.path.join(sys._MEIPASS, 'model')
    else:
        # Running as script
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'model')


class VoiceListener:
    """Listens to microphone input and recognizes voice commands."""

    def __init__(self, config, on_command=None, on_error=None, on_status=None):
        """
        Initialize the voice listener.

        Args:
            config: Config dict with commands, wake word, mic settings
            on_command: Callback(action_name) when a command is matched
            on_error: Callback(error_message) when an error occurs
            on_status: Callback(status_text) for status updates
        """
        self.config = config
        self.on_command = on_command
        self.on_error = on_error
        self.on_status = on_status

        self.model = None
        self.recognizer = None
        self.stream = None
        self.audio_queue = queue.Queue()

        self._running = False
        self._paused = False
        self._thread = None

    def _load_model(self):
        """Load the Vosk model."""
        model_path = get_model_path()

        if not os.path.exists(model_path):
            error_msg = f"Vosk model not found at: {model_path}"
            logger.error(error_msg)
            if self.on_error:
                self.on_error(error_msg)
            return False

        try:
            logger.info(f"Loading Vosk model from: {model_path}")
            self.model = Model(model_path)
            self.recognizer = KaldiRecognizer(self.model, SAMPLE_RATE)
            logger.info("Vosk model loaded successfully")
            return True
        except Exception as e:
            error_msg = f"Failed to load Vosk model: {e}"
            logger.error(error_msg)
            if self.on_error:
                self.on_error(error_msg)
            return False

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback for sounddevice stream - puts audio data in queue."""
        if status:
            logger.warning(f"Audio status: {status}")
        if not self._paused:
            self.audio_queue.put(bytes(indata))

    def _process_audio(self):
        """Background thread that processes audio from queue."""
        while self._running:
            try:
                data = self.audio_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if self._paused:
                continue

            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                text = result.get("text", "")
                if text:
                    logger.debug(f"Recognized: {text}")
                    self._handle_recognition(text)
            else:
                # Partial result - could use for feedback if desired
                pass

    def _handle_recognition(self, text):
        """Handle recognized text - match commands and execute."""
        action = match_command(text, self.config)
        if action:
            logger.info(f"Command matched: {text} -> {action}")
            send_media_key(action)
            if self.on_command:
                self.on_command(action)

    def start(self):
        """Start listening for voice commands."""
        if self._running:
            return True

        if not self._load_model():
            return False

        # Get mic device
        mic_device = self.config.get("mic_device")

        try:
            self.stream = sd.RawInputStream(
                samplerate=SAMPLE_RATE,
                blocksize=8000,
                dtype='int16',
                channels=1,
                device=mic_device,
                callback=self._audio_callback
            )
            self.stream.start()
            logger.info("Audio stream started")
        except Exception as e:
            error_msg = f"Failed to open microphone: {e}"
            logger.error(error_msg)
            if self.on_error:
                self.on_error(error_msg)
            return False

        self._running = True
        self._paused = False
        self._thread = threading.Thread(target=self._process_audio, daemon=True)
        self._thread.start()

        if self.on_status:
            self.on_status("listening")

        return True

    def stop(self):
        """Stop listening and clean up resources."""
        self._running = False

        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception as e:
                logger.warning(f"Error closing stream: {e}")
            self.stream = None

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

        self.model = None
        self.recognizer = None

        # Clear the queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

        logger.info("Voice listener stopped")

    def pause(self):
        """Pause listening (keeps stream open but ignores audio)."""
        self._paused = True
        logger.info("Voice listener paused")
        if self.on_status:
            self.on_status("paused")

    def resume(self):
        """Resume listening after pause."""
        self._paused = False
        logger.info("Voice listener resumed")
        if self.on_status:
            self.on_status("listening")

    def is_paused(self):
        """Check if listener is paused."""
        return self._paused

    def is_running(self):
        """Check if listener is running."""
        return self._running

    def reload_config(self, config):
        """Hot-reload configuration (updates command matching without restart)."""
        self.config = config
        logger.info("Configuration reloaded")


def get_available_mics():
    """Get list of available microphone devices."""
    devices = []
    try:
        for i, device in enumerate(sd.query_devices()):
            if device['max_input_channels'] > 0:
                devices.append({
                    'index': i,
                    'name': device['name']
                })
    except Exception as e:
        logger.error(f"Failed to query audio devices: {e}")
    return devices
