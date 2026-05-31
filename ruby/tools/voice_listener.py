import logging
import threading
import time
import io
import wave
import numpy as np

logger = logging.getLogger("ruby.voice.listener")

class VoiceListener:
    def __init__(self):
        self._recognizer = None
        self._sample_rate = 16000
        self.available = False
        self.listening = False
        self._init_engine()

    def _init_engine(self):
        try:
            import speech_recognition as sr
            self._recognizer = sr.Recognizer()
            self._recognizer.energy_threshold = 300
            self._recognizer.dynamic_energy_threshold = True
            self._recognizer.pause_threshold = 0.8

            try:
                import sounddevice as sd
                sd.query_devices()
                self._use_sounddevice = True
            except Exception:
                self._use_sounddevice = False

            if self._use_sounddevice:
                try:
                    self._calibrate_sounddevice()
                except Exception as e:
                    logger.warning("Sounddevice calibration failed: %s", e)
                    self._use_sounddevice = False

            if not self._use_sounddevice:
                try:
                    self._mic = sr.Microphone()
                    with self._mic as source:
                        self._recognizer.adjust_for_ambient_noise(source, duration=0.5)
                except Exception as e:
                    logger.warning("No microphone found: %s", e)
                    return

            self.available = True
            logger.info("Microphone ready (sounddevice: %s)", self._use_sounddevice)
        except ImportError as e:
            logger.warning("Speech recognition not available: %s", e)

    def _calibrate_sounddevice(self):
        import sounddevice as sd
        duration = 0.5
        recording = sd.rec(
            int(duration * self._sample_rate),
            samplerate=self._sample_rate,
            channels=1,
            dtype='float32'
        )
        sd.wait()
        rms = np.sqrt(np.mean(recording ** 2))
        if rms < 0.01:
            rms = 0.01
        self._noise_level = rms
        self._energy_threshold = rms * 3

    def _record_sounddevice(self, timeout: float, phrase_limit: float) -> np.ndarray | None:
        import sounddevice as sd
        max_samples = int(phrase_limit * self._sample_rate)
        buffer = np.zeros(max_samples, dtype='float32')
        ptr = 0
        silence_frames = 0
        max_silence = int(0.8 * self._sample_rate / 512)

        start_time = time.time()
        recording = sd.rec(
            int(phrase_limit * self._sample_rate),
            samplerate=self._sample_rate,
            channels=1,
            dtype='float32'
        )
        sd.wait()

        recording = recording.flatten()
        rms = np.sqrt(np.mean(recording ** 2))

        if rms < self._noise_level * 1.5:
            return None

        return recording

    def _sounddevice_to_audio_data(self, recording: np.ndarray) -> object:
        import speech_recognition as sr
        int_data = (recording * 32767).astype(np.int16)
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self._sample_rate)
            wf.writeframes(int_data.tobytes())
        buf.seek(0)
        return sr.AudioData(buf.read(), self._sample_rate, 2)

    def listen_once(self, timeout: float = 5.0, phrase_limit: float = 8.0) -> str | None:
        if not self.available:
            return None

        try:
            import speech_recognition as sr

            if self._use_sounddevice:
                recording = self._record_sounddevice(timeout, phrase_limit)
                if recording is None or len(recording) < self._sample_rate * 0.5:
                    return None
                audio = self._sounddevice_to_audio_data(recording)
            else:
                with self._mic as source:
                    self._recognizer.adjust_for_ambient_noise(source, duration=0.3)
                    audio = self._recognizer.listen(
                        source, timeout=timeout, phrase_time_limit=phrase_limit
                    )

            text = self._recognizer.recognize_google(audio)
            logger.info("Heard: %s", text)
            return text

        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            logger.warning("STT request error: %s", e)
            return None
        except Exception as e:
            logger.warning("Listen error: %s", e)
            return None

    def listen_async(self, callback, timeout: float = 10.0):
        if not self.available:
            return
        t = threading.Thread(
            target=self._listen_loop,
            args=(callback, timeout),
            daemon=True
        )
        t.start()

    def _listen_loop(self, callback, timeout: float):
        self.listening = True
        try:
            result = self.listen_once(timeout=timeout)
            if result:
                callback(result)
        finally:
            self.listening = False

    def start_continuous(self, callback, wake_word: str = "ruby"):
        if not self.available:
            logger.warning("Cannot start continuous listening: mic not available")
            return
        t = threading.Thread(
            target=self._continuous_loop,
            args=(callback, wake_word.lower()),
            daemon=True
        )
        t.start()
        logger.info("Continuous listening started (wake word: '%s')", wake_word)

    def _continuous_loop(self, callback, wake_word: str):
        import speech_recognition as sr
        while self.available:
            try:
                if self._use_sounddevice:
                    recording = self._record_sounddevice(1.0, 5.0)
                    if recording is None:
                        continue
                    audio = self._sounddevice_to_audio_data(recording)
                else:
                    with self._mic as source:
                        self._recognizer.adjust_for_ambient_noise(source, duration=0.2)
                        audio = self._recognizer.listen(source, timeout=1, phrase_time_limit=5)

                text = self._recognizer.recognize_google(audio)
                if not text:
                    continue
                text_lower = text.lower().strip()

                if text_lower.startswith(wake_word):
                    command = text_lower[len(wake_word):].strip()
                    logger.info("Wake word detected. Command: %s", command)
                    callback(command, via_wake=True)
                else:
                    callback(text, via_wake=False)
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except Exception as e:
                logger.debug("Continuous listen error: %s", e)
                time.sleep(0.5)

    def stop(self):
        self.available = False
        self.listening = False
