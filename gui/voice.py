import threading
import logging
import asyncio
import tempfile
import os

logger = logging.getLogger("ruby.voice")


class VoiceEngine:
    VOICE = "en-US-AriaNeural"
    RATE = "+20%"
    VOLUME = "+50%"

    def __init__(self):
        self.enabled = False
        self._edge = None
        self._edge_available = False
        self._fallback = None
        self._voice_name = None
        self._init_speakers()

    def _init_speakers(self):
        try:
            import edge_tts
            self._edge = edge_tts
            self._edge_available = True
            self._voice_name = f"Edge Neural ({self.VOICE})"
            self.enabled = True
            logger.info("Edge TTS ready — %s", self._voice_name)
        except ImportError:
            logger.warning("edge-tts not installed, trying pyttsx3 fallback")
            self._init_pyttsx3()

    def _init_pyttsx3(self):
        try:
            import pyttsx3
            self._fallback = pyttsx3.init()
            self._fallback.setProperty("rate", 190)
            self._fallback.setProperty("volume", 0.9)
            voices = self._fallback.getProperty("voices")
            female_keywords = ["zira", "hazel", "female", "woman", "girl",
                               "microsoft heather", "microsoft helena",
                               "catherine", "linda", "microsoft eva",
                               "microsoft toni", "microsoft elsa"]
            selected = None
            for v in voices:
                vname = v.name.lower() if v.name else ""
                vid = v.id.lower() if v.id else ""
                for kw in female_keywords:
                    if kw in vname or kw in vid:
                        selected = v
                        break
                if selected:
                    break
            if selected:
                self._fallback.setProperty("voice", selected.id)
                self._voice_name = selected.name
            elif voices:
                self._fallback.setProperty("voice", voices[-1].id)
                self._voice_name = voices[-1].name
            self.enabled = True
            logger.info("pyttsx3 fallback ready — %s", self._voice_name)
        except ImportError:
            logger.warning("No TTS engine available. Voice disabled.")
        except Exception as e:
            logger.warning("Voice init failed: %s", e)

    def speak(self, text: str):
        if not self.enabled or not text.strip():
            return
        clean = text.replace("*", "").replace("_", "").replace("#", "").strip()
        if not clean:
            return
        if self._edge_available:
            self._speak_edge(clean)
        elif self._fallback:
            self._speak_pyttsx3(clean)

    def _speak_edge(self, text: str):
        tmp = os.path.join(tempfile.gettempdir(), f"ruby_{id(text)}_{threading.get_ident()}.mp3")
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            communicate = self._edge.Communicate(
                text, voice=self.VOICE, rate=self.RATE, volume=self.VOLUME
            )
            loop.run_until_complete(communicate.save(tmp))
            loop.close()
            self._play_mp3(tmp)
        except Exception as e:
            logger.warning("Edge TTS error: %s", e)

    def _play_mp3(self, path: str):
        try:
            import miniaudio
            import wave
            decoded = miniaudio.decode_file(path)
            wav_path = path.replace(".mp3", ".wav")
            with wave.open(wav_path, "wb") as wf:
                wf.setnchannels(decoded.nchannels)
                wf.setsampwidth(decoded.sample_width)
                wf.setframerate(decoded.sample_rate)
                wf.writeframes(bytes(decoded.samples))
            import winsound
            winsound.PlaySound(wav_path, winsound.SND_FILENAME | winsound.SND_SYNC)
        except Exception as e:
            logger.warning("MP3 playback error: %s", e)

    def _speak_pyttsx3(self, text: str):
        try:
            self._fallback.say(text)
            self._fallback.runAndWait()
        except Exception as e:
            logger.warning("pyttsx3 speak error: %s", e)

    def speak_async(self, text: str):
        if not self.enabled or not text.strip():
            return
        t = threading.Thread(target=self.speak, args=(text,), daemon=True)
        t.start()

    def toggle(self) -> bool:
        self.enabled = not self.enabled
        logger.info("Voice %s", "ON" if self.enabled else "OFF")
        return self.enabled

    def get_voice_name(self) -> str:
        return self._voice_name or "Unknown"

    def stop(self):
        pass
