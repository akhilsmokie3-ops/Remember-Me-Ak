"""
Voice I/O — Unified voice input/output with wake word detection.
================================================================
Merged from Zyron's core/voice.py + core/wake_word.py.

CHANGES:
- Single VoiceIO class replaces two separate modules
- Lazy imports for speech_recognition, vosk, pyttsx3
- Configurable wake word (not hardcoded)
- No auto-start — caller explicitly calls start_listening()
"""

import json
import os
import queue
import threading
import time
from typing import Callable, Optional


class VoiceIO:
    """
    Unified voice input/output with optional wake word detection.

    Usage:
        voice = VoiceIO(wake_word="sovereign")
        voice.speak("Hello")
        text = voice.listen()  # Blocks until speech detected
    """

    def __init__(
        self,
        wake_word: str = "sovereign",
        vosk_model_path: Optional[str] = None,
        tts_rate: int = 175,
    ):
        self.wake_word = wake_word.lower()
        self.vosk_model_path = vosk_model_path
        self.tts_rate = tts_rate

        # Lazy-loaded deps
        self._sr = None
        self._recognizer = None
        self._tts_engine = None
        self._vosk_model = None
        self._vosk_rec = None

        # State
        self._listening = False
        self._audio_queue = queue.Queue()
        self._tts_lock = threading.Lock()

    # ─── TTS ─────────────────────────────────────────────────────

    def _ensure_tts(self):
        if self._tts_engine is None:
            import pyttsx3
            self._tts_engine = pyttsx3.init()
            self._tts_engine.setProperty("rate", self.tts_rate)

    def speak(self, text: str):
        """Speak text aloud (thread-safe)."""
        with self._tts_lock:
            self._ensure_tts()
            self._tts_engine.say(text)
            self._tts_engine.runAndWait()

    # ─── SPEECH RECOGNITION ──────────────────────────────────────

    def _ensure_sr(self):
        if self._sr is None:
            import speech_recognition as sr
            self._sr = sr
            self._recognizer = sr.Recognizer()
            self._recognizer.dynamic_energy_threshold = True

    def listen(self, timeout: int = 10, phrase_time_limit: int = 15) -> Optional[str]:
        """
        Listen for speech using Google Speech Recognition.
        Returns recognized text or None on failure.
        """
        self._ensure_sr()

        try:
            with self._sr.Microphone() as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self._recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_time_limit
                )

            text = self._recognizer.recognize_google(audio)
            return text.strip()

        except self._sr.WaitTimeoutError:
            return None
        except self._sr.UnknownValueError:
            return None
        except self._sr.RequestError as e:
            print(f"⚠️ Speech Recognition API error: {e}")
            return None

    # ─── WAKE WORD (VOSK) ────────────────────────────────────────

    def _ensure_vosk(self):
        if self._vosk_model is None:
            from vosk import Model, KaldiRecognizer
            import sounddevice as sd

            model_path = self.vosk_model_path
            if not model_path:
                # Try common locations
                for candidate in (
                    "vosk-model",
                    os.path.expanduser("~/.vosk/model"),
                    "model",
                ):
                    if os.path.isdir(candidate):
                        model_path = candidate
                        break

            if not model_path or not os.path.isdir(model_path):
                raise FileNotFoundError(
                    f"Vosk model not found. Set vosk_model_path or place model in ./vosk-model/"
                )

            self._vosk_model = Model(model_path)
            self._vosk_rec = KaldiRecognizer(self._vosk_model, 16000)

    def wait_for_wake_word(self, callback: Callable[[str], None]):
        """
        Blocks and listens for wake word, then captures the following command.
        Calls callback(command_text) when wake word + command detected.
        """
        self._ensure_vosk()
        import sounddevice as sd

        self._listening = True
        print(f"🎤 Listening for wake word: '{self.wake_word}'...")

        def audio_callback(indata, frames, time_info, status):
            if status:
                print(f"⚠️ Audio status: {status}")
            self._audio_queue.put(bytes(indata))

        with sd.RawInputStream(
            samplerate=16000, blocksize=8000, dtype="int16",
            channels=1, callback=audio_callback,
        ):
            wake_detected = False
            while self._listening:
                try:
                    data = self._audio_queue.get(timeout=1.0)
                except queue.Empty:
                    continue

                if self._vosk_rec.AcceptWaveform(data):
                    result = json.loads(self._vosk_rec.Result())
                    text = result.get("text", "").lower()

                    if not wake_detected:
                        if self.wake_word in text:
                            wake_detected = True
                            print(f"✅ Wake word detected! Listening for command...")
                            # Try to extract command from same utterance
                            idx = text.find(self.wake_word)
                            remainder = text[idx + len(self.wake_word):].strip()
                            if remainder:
                                callback(remainder)
                                wake_detected = False
                    else:
                        # Wake word was detected, this is the command
                        if text.strip():
                            callback(text.strip())
                        wake_detected = False

    def stop_listening(self):
        """Stop the wake word listener."""
        self._listening = False

    # ─── HYBRID MODE ─────────────────────────────────────────────

    def start_voice_loop(self, handler: Callable[[str], str]):
        """
        Main voice loop: wake word → listen → handler → speak response.
        handler takes user text, returns response text.
        """
        def on_wake(command: str):
            if not command:
                # Wake word only, listen for full command via Google
                self.speak("Yes?")
                command = self.listen()
                if not command:
                    return

            response = handler(command)
            if response:
                self.speak(response)

        try:
            self.wait_for_wake_word(on_wake)
        except KeyboardInterrupt:
            self.stop_listening()
