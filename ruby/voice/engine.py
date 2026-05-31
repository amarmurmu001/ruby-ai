import logging
import queue
import threading
from config.settings import settings

logger = logging.getLogger("ruby.voice")

class VoiceEngine:
    def __init__(self):
        self.enabled = settings.VOICE_ENABLED
        self._tts = None
        self._stt = None
        self._speech_queue = queue.Queue()
        self._listening = False

        if self.enabled:
            self._init_tts()
            self._init_stt()

    def _init_tts(self):
        try:
            import pyttsx3
            self._tts = pyttsx3.init()
            self._tts.setProperty("rate", 180)
            self._tts.setProperty("volume", 0.9)
            voices = self._tts.getProperty("voices")
            if voices:
                self._tts.setProperty("voice", voices[0].id)
            logger.info("TTS initialised (pyttsx3)")
        except ImportError:
            logger.warning("pyttsx3 not installed. TTS disabled.")
            self._try_gtts()

    def _try_gtts(self):
        try:
            import gtts
            import pygame
            self._tts = "gtts"
            logger.info("TTS initialised (gTTS + pygame)")
        except ImportError:
            logger.warning("No TTS engine available. Voice output disabled.")
            self.enabled = False

    def _init_stt(self):
        try:
            import speech_recognition as sr
            self._stt = sr.Recognizer()
            logger.info("STT initialised (speech_recognition)")
        except ImportError:
            logger.warning("speech_recognition not installed. Voice input disabled.")

    def speak(self, text: str):
        if not self.enabled or not self._tts:
            return
        try:
            if hasattr(self._tts, "say"):
                self._tts.say(text)
                self._tts.runAndWait()
            elif self._tts == "gtts":
                import gtts
                import pygame
                import tempfile
                import os
                tts = gtts.gTTS(text=text, lang="en", slow=False)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                    tts.save(f.name)
                    pygame.mixer.init()
                    pygame.mixer.music.load(f.name)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        pygame.time.Clock().tick(10)
                    os.unlink(f.name)
        except Exception as e:
            logger.exception("TTS error")

    def listen(self, timeout: int = 5) -> str | None:
        if not self.enabled or not self._stt:
            return None
        try:
            import speech_recognition as sr
            with sr.Microphone() as source:
                self._stt.adjust_for_ambient_noise(source, duration=0.5)
                logger.info("Listening...")
                audio = self._stt.listen(source, timeout=timeout, phrase_time_limit=10)
            text = self._stt.recognize_google(audio)
            logger.info("Heard: %s", text)
            return text
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except Exception as e:
            logger.exception("STT error")
            return None

    def speak_async(self, text: str):
        if not self.enabled:
            return
        self._speech_queue.put(text)
        if not self._listening:
            self._listening = True
            t = threading.Thread(target=self._process_queue, daemon=True)
            t.start()

    def _process_queue(self):
        while not self._speech_queue.empty():
            text = self._speech_queue.get()
            self.speak(text)
            self._speech_queue.task_done()
        self._listening = False
