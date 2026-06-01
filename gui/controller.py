import logging
import threading

logger = logging.getLogger("ruby.controller")


class Controller:
    def __init__(self):
        self.brain = None
        self.voice = None
        self.listener = None
        self._init_brain()
        self._init_voice()
        self._init_listener()

    def _init_brain(self):
        try:
            from ruby.brain import Brain
            self.brain = Brain()
            logger.info("Brain ready: %s", self._detect_backend())
        except Exception as e:
            logger.warning("Brain init failed: %s", e)

    def _init_voice(self):
        try:
            from gui.voice import VoiceEngine
            self.voice = VoiceEngine()
        except Exception as e:
            logger.warning("Voice init failed: %s", e)

    def _init_listener(self):
        try:
            from ruby.tools.voice_listener import VoiceListener
            self.listener = VoiceListener()
            if not self.listener.available:
                self.listener = None
        except Exception as e:
            logger.warning("Listener init failed: %s", e)

    def _detect_backend(self) -> str:
        try:
            from ruby.tools.llm import LLMProvider
            llm = LLMProvider()
            if llm.ready:
                return llm.model
        except Exception:
            pass
        return "CUSTOM NEURAL BRAIN"

    def think(self, text: str) -> str:
        if self.brain:
            return self.brain.think(text)
        tl = text.lower()
        if "hello" in tl or "hi" in tl:
            return "Hey. Ruby online. What do you need?"
        if "time" in tl:
            import time
            return f"Current local time: {time.strftime('%H:%M:%S')}"
        return "Acknowledged."

    def think_async(self, text: str, callback):
        def _run():
            try:
                result = self.think(text)
                callback(result)
            except Exception as e:
                callback(f"[ERROR] {e}")
        threading.Thread(target=_run, daemon=True).start()

    def speak(self, text: str):
        if self.voice and self.voice.enabled:
            self.voice.speak_async(text)

    def listen(self, timeout=8, phrase_limit=10) -> str | None:
        if self.listener:
            return self.listener.listen_once(timeout, phrase_limit)
        return None

    def listen_async(self, callback, timeout=8, phrase_limit=10):
        def _run():
            result = self.listen(timeout, phrase_limit)
            if callback:
                callback(result)
        threading.Thread(target=_run, daemon=True).start()

    def listen_stop(self):
        if self.listener:
            self.listener.listen_stop()

    def start_wake(self, callback, wake_word="ruby"):
        if self.listener:
            self.listener.start_continuous(callback, wake_word)

    def stop_wake(self):
        if self.listener:
            self.listener.stop()

    def shutdown(self):
        if self.listener:
            self.listener.stop()

    @property
    def has_mic(self) -> bool:
        return self.listener is not None

    @property
    def has_voice(self) -> bool:
        return self.voice is not None and self.voice.enabled

    @property
    def backend_name(self) -> str:
        return self._detect_backend()
